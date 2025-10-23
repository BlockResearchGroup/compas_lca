from typing import Optional
from typing import Iterator
from typing import Union

from uuid import UUID

from compas_lca.inventory.item import InventoryItem


class Inventory:
    """
    A list-like container for LCA inventory items that enforces type safety.

    Behaves like a Python list for the common operations (indexing, iteration,
    append/extend/insert, pop/remove, slicing assignment) but only accepts
    `InventoryItem` instances.
    """

    def __init__(self, items: Optional[list[InventoryItem]] = None) -> None:
        self._items: list[InventoryItem] = []
        if items:
            self.extend(items)

    # core list-like behavior
    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[InventoryItem]:
        return iter(self._items)

    def __getitem__(self, index):
        # Returns InventoryItem or list[InventoryItem] for slices (like a normal list)
        return self._items[index]

    def __setitem__(self, index, value: Union[InventoryItem, list[InventoryItem]]) -> None:
        if isinstance(index, slice):
            self._validate_many(value)
            self._items[index] = list(value)
        else:
            self._validate_one(value)
            self._items[index] = value

    def __repr__(self) -> str:
        return f"Inventory({len(self)} items)"

    # mutation APIs with validation
    def append(self, item: InventoryItem) -> None:
        self._validate_one(item)
        self._items.append(item)

    def extend(self, items: list[InventoryItem]) -> None:
        self._validate_many(items)
        self._items.extend(items)

    def insert(self, index: int, item: InventoryItem) -> None:
        self._validate_one(item)
        self._items.insert(index, item)

    def pop(self, index: int = -1) -> InventoryItem:
        return self._items.pop(index)

    def remove(self, item: InventoryItem) -> None:
        self._items.remove(item)

    def clear(self) -> None:
        self._items.clear()

    # utilities
    def get(self, id: UUID) -> Optional[InventoryItem]:
        """Return the item with the given UUID, or None if not found."""
        for it in self._items:
            if it.id == id:
                return it
        return None

    def remove_by_id(self, id: UUID) -> bool:
        """Remove the item with the given UUID. Returns True if removed, else False."""
        for i, it in enumerate(self._items):
            if it.id == id:
                del self._items[i]
                return True
        return False

    def to_list(self) -> list[InventoryItem]:
        """Return a shallow copy as a plain Python list."""
        return list(self._items)

    # validators
    @staticmethod
    def _validate_one(value: InventoryItem) -> None:
        if not isinstance(value, InventoryItem):
            raise TypeError(f"Inventory only accepts InventoryItem, got {type(value)!r}")

    @classmethod
    def _validate_many(cls, values: list[InventoryItem]) -> None:
        for v in values:
            cls._validate_one(v)

    # placeholders (to implement later)
    def from_excel(self, filepath: str):
        """Load an inventory from an Excel file."""
        pass

    def from_epds(self, filepaths: list[str]):
        """Load an inventory from EPD files."""
        pass
