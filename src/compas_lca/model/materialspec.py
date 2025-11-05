from math import isclose

from typing import Optional
from typing import List
from typing import Tuple
from typing import Annotated

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field
from pydantic import model_validator

from compas_lca.matching_core.core import MatchingCore

Ratio01 = Annotated[float, Field(ge=0, le=1)]

class MaterialSpec(BaseModel):
    """
    One material composition unit within an element.
    - Pure: single material with ratio ~ 1.0
    - Composite: multiple materials with ratios summing ~ 1.0
    """
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    name: Optional[str] = None
    materials: List[Tuple[MatchingCore, Ratio01]] = Field(..., min_length=1)
    tolerance: float = Field(1e-3, exclude=True)

    @computed_field
    @property
    def is_composite(self) -> bool:
        return len(self.materials) > 1

    @model_validator(mode="after")
    def _validate_ratios(self) -> "MaterialSpec":
        ratios = [r for _, r in self.materials]
        total = sum(ratios)

        # Sum must be ~ 1.0 within tolerance
        if not isclose(total, 1.0, rel_tol=0.0, abs_tol=self.tolerance):
            raise ValueError(
                f"Sum of ratios must be 1.0 ± {self.tolerance:.6g}; got {total:.6f}"
            )

        # Optional: for single-entry specs, snap ratio to exactly 1.0 if within tolerance
        if len(self.materials) == 1 and not isclose(ratios[0], 1.0, rel_tol=0.0, abs_tol=self.tolerance):
            core, _ = self.materials[0]
            self.materials = [(core, 1.0)]

        return self