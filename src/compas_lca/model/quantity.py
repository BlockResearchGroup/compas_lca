from typing import Dict
from typing import List

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.validators import ParsedNumber
from compas_lca.validators import QuantNameType
from compas_lca.validators import QuantUnitType


class Quantity(BaseModel):
    """
    One measurable property, normalized as name/value/unit.

    Example:
        Quantity(name="length", value=2.5, unit="m")
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, validate_assignment=True, str_strip_whitespace=True)

    name: QuantNameType  # e.g. "thickness", "length", "area", "weight"
    value: ParsedNumber  # the numeric value
    unit: QuantUnitType  # e.g. "m", "m2", "m3"

    def as_dict(self) -> Dict[str, ParsedNumber | str]:
        """Return a simple dict representation (for export/serialization)."""
        return {"name": self.name, "value": self.value, "unit": self.unit}

    def __repr__(self) -> str:
        return f'Quantity(name="{self.name}", value={self.value}, unit="{self.unit}")'


class Quantities(BaseModel):
    """
    collection of Quantity items for one element (e.g., length, area, volume).
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True, validate_assignment=True, str_strip_whitespace=True)

    quantities: List[Quantity] = Field(default_factory=list)

    def get(self, name: str) -> List[Quantity]:
        """finds all quantities with the given name."""
        key = name.strip()
        return [q for q in self.items if q.name == key]

    def __repr__(self) -> str:
        inner = ", ".join(repr(q) for q in self.items)
        return f"Quantities([{inner}])"
