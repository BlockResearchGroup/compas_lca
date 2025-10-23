from typing import Optional
from typing import List

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field
from pydantic import model_validator

from compas_lca.matching_core.core import MatchingCore

class MaterialSpec(BaseModel):
    """
    Represents one material composition unit within an element.

    This can describe:
      • a pure, monolithic material (single LcaMaterial, ratio=1.0)
      • a composite material (multiple LcaMaterial with volumetric_ratio summing ≈ 1.0)

    Expresses how the element is materially built, independent of geometric layering.
    """
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None  # Optional descriptive label (e.g. "RC core", "Exterior finish")
    materials: List[MatchingCore] = Field(..., min_length=1)
    tolerance: float = Field(1e-3, exclude=True)

    @computed_field
    @property
    def is_composite(self) -> bool:
        return len(self.materials) > 1

    @model_validator(mode="after")
    def _validate_pure_or_composite(self):
        if len(self.materials) == 1:
            m = self.materials[0]
            if m.volumetric_ratio is None or abs(m.volumetric_ratio - 1.0) > self.tolerance:
                m.volumetric_ratio = 1.0
        else:
            total = sum(
                (m.volumetric_ratio or 0.0) for m in self.materials
            )
            if not (1.0 - self.tolerance) <= total <= (1.0 + self.tolerance):
                raise ValueError(
                    f"Sum of volumetric_ratio in composite must be ~1.0 (±{self.tolerance}); got {total:.6f}"
                )
        return self