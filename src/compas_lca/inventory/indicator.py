from typing import Optional

from .constants import INDICATOR_NAME
from .constants import INDICATOR_UNITS
from .constants import STAGE_NAME

from compas.data import Data

class Indicator(Data):
    """An environmental indicator for one material/product/component, across life cycle stages."""
    def __init__(
        self,
        name: INDICATOR_NAME,
        stages: dict[STAGE_NAME, float],  # mapping: stage -> indicator value
        source: Optional[str] = None,
    ):
        super().__init__(name=name)
        self.name = name
        self.unit = INDICATOR_UNITS[name]

    @property
    def total(self) -> float:
        """Sum of all stage values."""
        return sum(self.stages.values())

    @property
    def stage_names(self) -> list[STAGE_NAME]:
        return list(self.stages.keys())

    @property
    def __data__(self) -> dict:
        return {
            "name": self.name,
            "unit": self.unit,
            "stages": self.stages,
            "source": self.source,
        }

    @classmethod
    def __from_data__(cls, data: dict) -> "Indicator":
        return cls(
            name=data["name"],
            unit=data.get("unit", INDICATOR_UNITS.get(data["name"], "unknown")),
            stages=data["stages"],
            source=data.get("source"),
        )

    def __repr__(self) -> str:
        return f"Indicator(name={self.name}, unit={self.unit}, total={self.total})"

