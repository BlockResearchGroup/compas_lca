from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List
from typing import Union

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic import ConfigDict

Number = Union[int, float]

class Quantity(BaseModel):
    """
    One measurable property, normalized as name/value/unit.
    Example: Quantity(name="length", value=2.5, unit="m")
    """

    name: str                                # e.g. "pieces", "length", "area", "weight"
    value: Number                            # the numeric value
    unit: str                                # e.g. "pcs", "mm", "m", "kg", "m2", "m3"
    custom: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("name", mode="before")
    @classmethod
    def _normalize_name(cls, v: Any) -> str:
        if v is Ellipsis or v == "":
            raise ValueError("name is required")
        return str(v).strip()

    @field_validator("unit", mode="before")
    @classmethod
    def _normalize_unit(cls, v: Any) -> str:
        if v is Ellipsis or v == "":
            raise ValueError("unit is required")
        return str(v).strip()

    @field_validator("value", mode="before")
    @classmethod
    def _cast_value(cls, v: Any) -> Number:
        if v is Ellipsis or v == "":
            raise ValueError("value is required")
        if isinstance(v, (int, float)):
            return v
        try:
            return float(v) if ("." in str(v) or "e" in str(v).lower()) else int(v)
        except Exception as exc:
            raise ValueError(f"Cannot cast value {v!r} to number") from exc

    # Serialization (is this even required?)
    def to_compas_data(self) -> Dict[str, Any]:
        return {"name": self.name, "value": self.value, "unit": self.unit, "custom": self.custom}

    @classmethod
    def from_compas_data(cls, data: Dict[str, Any]) -> "Quantity":
        return cls(**data)

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

    # Serialization (is this even required?)
    def to_compas_data(self) -> Dict[str, Any]:
        return {"items": [q.to_compas_data() for q in self.items]}

    @classmethod
    def from_compas_data(cls, data: Dict[str, Any]) -> "Quantities":
        return cls(items=[Quantity.from_compas_data(it) for it in data["items"]])

    def __repr__(self) -> str:
        inner = ", ".join(repr(q) for q in self.items)
        return f"Quantities([{inner}])"
