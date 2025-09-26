from __future__ import annotations
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict

class Quantity(BaseModel):
    """
    Quantity Extraction from building elements.
    Note to Li: Tom mentioned that IfcQuantity can be wrong. Perhaps default geometry-based calculation instead of quantity extraction?
    """
    pieces: Optional[int] = Field(default=None, ge=0, description="Number of pieces")
    length: Optional[float] = Field(default=None, ge=0, description="Length in meters")
    area: Optional[float] = Field(default=None, ge=0, description="Area in m²")
    volume: Optional[float] = Field(default=None, ge=0, description="Volume in m³")
    weight: Optional[float] = Field(default=None, ge=0, description="Weight in kg")
    custom: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    @field_validator("pieces", "length", "area", "volume", "weight", mode="before")
    @classmethod
    def _empty_string_to_none_and_cast(cls, v):
        if v == "" or v is Ellipsis:
            return None
        return v

    @field_validator("custom", mode="before")
    @classmethod
    def _ensure_dict(cls, v):
        return v or {}

    def to_compas_data(self) -> Dict[str, Any]:
        return {
            "pieces": self.pieces,
            "length": self.length,
            "area": self.area,
            "volume": self.volume,
            "weight": self.weight,
            "custom": self.custom,
        }

    @classmethod
    def from_compas_data(cls, data: Dict[str, Any]) -> "Quantity":
        return cls(**data)

    def __repr__(self) -> str:
        return (
            f"Quantity(pieces={self.pieces}, length={self.length}, "
            f"area={self.area}, volume={self.volume}, weight={self.weight})"
        )
