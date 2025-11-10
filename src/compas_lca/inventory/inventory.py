"""
Usage example:

inv = Inventory(items)

# All materials / components / unknowns
materials = inv.by_entry_type(EntryType.material)
components = inv.by_entry_type(EntryType.component)
unknowns = inv.by_entry_type(EntryType.unknown)

# All concretes (materials with MaterialType.concrete)
concretes = inv.by_material_type(MaterialType.concrete)

# All windows (components with ComponentType.window)
windows = inv.by_component_type(ComponentType.window)

# Combined filter via `where(...)`
mat_concretes = inv.where(entry_type=EntryType.material, material_type=MaterialType.concrete)
comp_windows  = inv.where(entry_type=EntryType.component, component_type=ComponentType.window)

# Classmethod version on any iterable
subset = Inventory.where_from(items[:1000], entry_type=EntryType.material)
"""


from typing import Optional
from typing import Iterable
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
from compas_lca.enums import MaterialType
from compas_lca.enums import ComponentType

class Inventory(RootModel[list[InventoryItem]]):
    """
    Pydantic-validated, list-like container for LCA inventory items.
    Uses RootModel, so the model itself is a validated list

    Behaves like a Python list for common operations (indexing, iteration,
    append/extend/insert, pop/remove, slicing assignment) but only accepts
    `InventoryItem` instances.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,  # in case InventoryItem is a non-pydantic class
        frozen=False,                  # allow mutation of self.root
    )

    # Explicit root type (optional, but nice for editors)
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
        # Returns InventoryItem or list[InventoryItem] for slices (like a normal list)
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

    def by_material_type(self, material_type: MaterialType) -> list[InventoryItem]:
        """
        All items with entry_type == material AND MaterialCore.material_type == `material_type`.
        """
        out: list[InventoryItem] = []
        for it in self.root:
            if self._is_material(it) and it.item_core.facet.material_type == material_type:
                out.append(it)
        return out

    def by_component_type(self, component_type: ComponentType) -> list[InventoryItem]:
        """
        All items with entry_type == component AND ComponentCore.component_type == `component_type`.
        """
        out: list[InventoryItem] = []
        for it in self.root:
            if self._is_component(it) and it.item_core.facet.component_type == component_type:
                out.append(it)
        return out

    def where(
        self,
        *,
        entry_type: Optional[EntryType] = None,
        material_type: Optional[MaterialType] = None,
        component_type: Optional[ComponentType] = None,
    ) -> list[InventoryItem]:
        """
        Flexible filter:
          - If entry_type is provided, items must match it.
          - If material_type is provided, items must be materials with that material_type.
          - If component_type is provided, items must be components with that component_type.

        Combinations:
          - entry_type=material + material_type=... (common)
          - entry_type=component + component_type=... (common)
          - Only entry_type
          - Only material_type / component_type (entry_type inferred)
        """
        out: list[InventoryItem] = []
        for it in self.root:
            core = getattr(it, "item_core", None)
            if not isinstance(core, MatchingCore):
                continue

            # entry_type constraint (if given)
            if entry_type is not None and core.entry_type != entry_type:
                continue

            # material constraint
            if material_type is not None:
                if not self._is_material(it):
                    continue
                if it.item_core.facet.material_type != material_type:
                    continue

            # component constraint
            if component_type is not None:
                if not self._is_component(it):
                    continue
                if it.item_core.facet.component_type != component_type:
                    continue

            out.append(it)
        return out

    # ---------- classmethod variants (work on any iterable) ----------
    @classmethod
    def where_from(
        cls,
        items: Iterable[InventoryItem],
        **kwargs,
    ) -> list[InventoryItem]:
        """Like `.where(...)` but for any iterable of items."""
        return cls(list(items)).where(**kwargs)

    @classmethod
    def by_entry_type_from(cls, items: Iterable[InventoryItem], entry_type: EntryType) -> list[InventoryItem]:
        return cls(list(items)).by_entry_type(entry_type)

    @classmethod
    def by_material_type_from(cls, items: Iterable[InventoryItem], material_type: MaterialType) -> list[InventoryItem]:
        return cls(list(items)).by_material_type(material_type)

    @classmethod
    def by_component_type_from(cls, items: Iterable[InventoryItem], component_type: ComponentType) -> list[InventoryItem]:
        return cls(list(items)).by_component_type(component_type)

    # ---- placeholders (to implement later) ----
    def from_excel(self, filepath: str):
        """Load an inventory from an Excel file."""
        pass

    def from_epds(self, filepaths: list[str]):
        """Load an inventory from EPD files."""
        pass



"""
Ideas/drafts to store a big Inventory(RootModel[list[InventoryItem]])
in a tangible and reusable way:
"""

# =======================================================
# 1. Serialize (JSON/JSONL), where whole Inventory is
# dumped into JSON or NDJSON/JSONL
# zero dependencies, language-agnostic, pydantic v2 cleanly encodes everything
# used when mostly reading the whole inventory at once or streaming items line-by-line
# =======================================================

# write a single JSON blob
def save_inventory_json(inv: Inventory, path: str) -> None:
    data = inv.model_dump(mode="json")  # -> list[dict]
    import json
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def load_inventory_json(path: str) -> Inventory:
    import json
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Inventory.model_validate(data)  # validates the list into Inventory

# write/stream NDJSON (better for huge inventories and incremental processing)
def save_inventory_jsonl(inv: Inventory, path: str) -> None:
    import json
    with open(path, "w", encoding="utf-8") as f:
        for item in inv.root:
            f.write(json.dumps(item.model_dump(mode="json"), ensure_ascii=False) + "\n")

def load_inventory_jsonl(path: str) -> Inventory:
    import json
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            items.append(InventoryItem.model_validate(json.loads(line)))
    return Inventory(items)


# =======================================================
# 2. SQlite (or any DB) -  quariable and scalable without server
# Store each InventoryItem as JSON in a row, create generated columsn
# for fields you want to query (e.g., entry_type, material_type, component_type)
# Fast lookups, filters, without loading everything into memory, works cross-platform
# =======================================================

import sqlite3, json

def save_inventory_sqlite(inv: Inventory, db_path: str, table: str="inventory_items") -> None:
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

    rows = [(str(it.id), json.dumps(it.model_dump(mode='json'), ensure_ascii=False)) for it in inv.root]
    con.executemany(f"INSERT OR REPLACE INTO {table}(id, payload) VALUES (?, ?)", rows)
    con.commit()
    con.close()

def load_inventory_sqlite(db_path: str, *, entry_type=None, material_type=None, component_type=None,
                          table: str="inventory_items") -> Inventory:
    con = sqlite3.connect(db_path)
    where, params = [], []
    if entry_type is not None:
        where.append("entry_type = ?"); params.append(entry_type.value if hasattr(entry_type, "value") else str(entry_type))
    if material_type is not None:
        where.append("material_type = ?"); params.append(material_type.value if hasattr(material_type, "value") else str(material_type))
    if component_type is not None:
        where.append("component_type = ?"); params.append(component_type.value if hasattr(component_type, "value") else str(component_type))

    sql = f"SELECT payload FROM {table}" + (" WHERE " + " AND ".join(where) if where else "")
    items = [InventoryItem.model_validate(json.loads(row[0])) for row in con.execute(sql, params)]
    con.close()
    return Inventory(items)
