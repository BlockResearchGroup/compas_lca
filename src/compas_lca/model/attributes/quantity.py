from typing import Any
from typing import Dict
from typing import List
from typing import Union

from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict

from compas_lca.validators import NameStr
from compas_lca.validators import UnitStr
from compas_lca.validators import ParsedNumber


Number = Union[int, float]

class Quantity(BaseModel):
    """
    One measurable property, normalized as name/value/unit.
    Example: Quantity(name="length", value=2.5, unit="m")
    """

    name: NameStr           # e.g. "pieces", "length", "area", "weight"
    value: ParsedNumber     # the numeric value
    unit: UnitStr           # e.g. "pcs", "mm", "m", "kg", "m2", "m3"
    custom: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    def __repr__(self) -> str:
        return f'Quantity(name="{self.name}", value={self.value}, unit="{self.unit}")'


class Quantities(BaseModel):
    """
    collection of Quantity items for one element.
    """
    items: List[Quantity] = Field(default_factory=list)
    model_config = ConfigDict(extra="forbid")

    def get(self, name: str) -> List[Quantity]:
        """finds all quantities with the given name."""
        key = name.strip()
        return [q for q in self.items if q.name == key]

    def __repr__(self) -> str:
        inner = ", ".join(repr(q) for q in self.items)
        return f"Quantities([{inner}])"
