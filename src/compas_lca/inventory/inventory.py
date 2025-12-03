import json
import sqlite3

from typing import Optional
from typing import Iterator
from typing import Union

from uuid import UUID

from pydantic import RootModel
from pydantic import ConfigDict

from compas_lca.inventory.item import InventoryItem

from compas_lca.matching_core.core import MatchingCore
from compas_lca.matching_core.material.core import MaterialCore
from compas_lca.matching_core.component.core import ComponentCore

from compas_lca.enums import EntryType

class Inventory(RootModel[list[InventoryItem]]):
    """
    Pydantic-validated, list-like container for InventoryItem instances.
    Uses RootModel, so the model itself is a validated list.
    Behaves like a Python list for common operations (indexing, iteration,
    append/extend/insert, pop/remove, slicing assignment).
    """

    model_config = ConfigDict(
        frozen=False                  # allow mutation of self.root
    )

    # Explicit root type (annotation)
    root: list[InventoryItem]

    # ---- init ----
    def __init__(self, items: Optional[list[InventoryItem]] = None) -> None:
        super().__init__(root=items or [])

    # ---- core list-like behavior ----
    def __len__(self) -> int:
        return len(self.root)

    def __iter__(self) -> Iterator[InventoryItem]:
        return iter(self.root)

    def __getitem__(self, index):
        return self.root[index]

    def __setitem__(self, index, value: Union[InventoryItem, list[InventoryItem]]) -> None:
        if isinstance(index, slice):
            self._validate_many(value)
            self.root[index] = list(value)
        else:
            self._validate_one(value)
            self.root[index] = value

    def __repr__(self) -> str:
        return f"Inventory({len(self)} items)"

    # ---- mutation APIs with validation ----
    def append(self, item: InventoryItem) -> None:
        self._validate_one(item)
        self.root.append(item)

    def extend(self, items: list[InventoryItem]) -> None:
        self._validate_many(items)
        self.root.extend(items)

    def insert(self, index: int, item: InventoryItem) -> None:
        self._validate_one(item)
        self.root.insert(index, item)

    def pop(self, index: int = -1) -> InventoryItem:
        return self.root.pop(index)

    def remove(self, item: InventoryItem) -> None:
        self.root.remove(item)

    def clear(self) -> None:
        self.root.clear()

    # ---- utilities ----
    def get(self, id: UUID) -> Optional[InventoryItem]:
        """Return the item with the given UUID, or None if not found."""
        for it in self.root:
            if it.id == id:
                return it
        return None

    def remove_by_id(self, id: UUID) -> bool:
        """Remove the item with the given UUID. Returns True if removed, else False."""
        for i, it in enumerate(self.root):
            if it.id == id:
                del self.root[i]
                return True
        return False

    def to_list(self) -> list[InventoryItem]:
        """Return a shallow copy as a plain Python list."""
        return list(self.root)

    # ---- validators ----
    @staticmethod
    def _validate_one(value: InventoryItem) -> None:
        if not isinstance(value, InventoryItem):
            raise TypeError(f"Inventory only accepts InventoryItem, got {type(value)!r}")

    @classmethod
    def _validate_many(cls, values: list[InventoryItem]) -> None:
        for v in values:
            cls._validate_one(v)

    # ---------- query helpers ----------
    @staticmethod
    def _is_material(item: InventoryItem) -> bool:
        return (
            isinstance(item.item_core, MatchingCore) and
            getattr(item.item_core, "entry_type", None) == EntryType.material and
            isinstance(getattr(item.item_core, "facet", None), MaterialCore)
        )

    @staticmethod
    def _is_component(item: InventoryItem) -> bool:
        return (
            isinstance(item.item_core, MatchingCore) and
            getattr(item.item_core, "entry_type", None) == EntryType.component and
            isinstance(getattr(item.item_core, "facet", None), ComponentCore)
        )

    # ---------- public querying API ----------
    def by_entry_type(self, entry_type: EntryType) -> list[InventoryItem]:
        """All items whose MatchingCore.entry_type equals `entry_type`."""
        out: list[InventoryItem] = []
        for it in self.root:
            core = getattr(it, "item_core", None)
            if isinstance(core, MatchingCore) and core.entry_type == entry_type:
                out.append(it)
        return out

    def by_material_type(self) -> list[InventoryItem]:
        """
        All items with entry_type == material.
        """
        out: list[InventoryItem] = []
        for it in self.root:
            if self._is_material(it):
                out.append(it)
        return out

    def by_component_type(self) -> list[InventoryItem]:
        """
        All items with entry_type == component.
        """
        out: list[InventoryItem] = []
        for it in self.root:
            if self._is_component(it):
                out.append(it)
        return out


    # ---- Serialize (JSON/JSONL/SQLITE) ----
    def save_json(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(mode="json"), f, ensure_ascii=False)

    def save_jsonl(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            for item in self.root:
                f.write(json.dumps(item.model_dump(mode="json"), ensure_ascii=False) + "\n")

    def save_sqlite(self, db_path: str, table: str="inventory_items") -> None:
        """ DRAFT """
        con = sqlite3.connect(db_path)
        con.execute(f"""CREATE TABLE IF NOT EXISTS {table} (
            id TEXT PRIMARY KEY,
            payload JSON NOT NULL,
            entry_type TEXT GENERATED ALWAYS AS (json_extract(payload, '$.item_core.entry_type')) VIRTUAL,
            material_type TEXT GENERATED ALWAYS AS (json_extract(payload, '$.item_core.facet.material_type')) VIRTUAL,
            component_type TEXT GENERATED ALWAYS AS (json_extract(payload, '$.item_core.facet.component_type')) VIRTUAL
        )""")
        con.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_entry ON {table}(entry_type)")
        con.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_mat ON {table}(material_type)")
        con.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_comp ON {table}(component_type)")

        rows = [
            (str(it.id), json.dumps(it.model_dump(mode="json"), ensure_ascii=False))
            for it in self.root
        ]
        con.executemany(f"INSERT OR REPLACE INTO {table}(id, payload) VALUES (?, ?)", rows)
        con.commit()
        con.close()

    # ---- Load (JSON/JSONL/SQLITE) ----
    @classmethod
    def load_json(cls, path: str) -> "Inventory":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.model_validate(data)

    @classmethod
    def load_jsonl(cls, path: str) -> "Inventory":
        items = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                items.append(InventoryItem.model_validate(json.loads(line)))
        return cls(items)
    
    @classmethod
    def load_sqlite(cls, db_path: str, *, entry_type=None, material_type=None,
                    component_type=None, table: str="inventory_items") -> "Inventory":
        """ DRAFT """
        con = sqlite3.connect(db_path)
        where, params = [], []
        if entry_type is not None:
            where.append("entry_type = ?")
            params.append(entry_type.value if hasattr(entry_type, "value") else str(entry_type))
        if material_type is not None:
            where.append("material_type = ?")
            params.append(material_type.value if hasattr(material_type, "value") else str(material_type))
        if component_type is not None:
            where.append("component_type = ?")
            params.append(component_type.value if hasattr(component_type, "value") else str(component_type))
        sql = f"SELECT payload FROM {table}" + (" WHERE " + " AND ".join(where) if where else "")
        rows = con.execute(sql, params)
        items = [InventoryItem.model_validate(json.loads(payload)) for (payload,) in rows]
        con.close()
        return cls(items)


    # ---- placeholders (to implement later) ----
    def from_excel(self, input_path: str):
        """Load an inventory from an Excel file."""
        raise NotImplementedError("Not implemented yet")

    def from_epds(self, input_paths: list[str]):
        """Load an inventory from EPD files."""
        raise NotImplementedError("Not implemented yet")

    def save_csv(self, path: str):
        """Load an inventory from an Excel file."""
        raise NotImplementedError("Not implemented yet")