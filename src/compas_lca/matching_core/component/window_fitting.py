from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from compas_lca.enums import WindowFittingType
from compas_lca.matching_core.normalization import normalize_window_fitting_type


class WindowFittingFacet(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True, str_strip_whitespace=True)
    window_fitting_type: WindowFittingType = Field(
        WindowFittingType.unknown, description="The material from which the window fitting is made", examples=["aluminium", "brass", "zinc"]
    )

    @field_validator("window_fitting_type", mode="before")
    @classmethod
    def _normalize_window_fitting_type(cls, value):
        return normalize_window_fitting_type(value)
