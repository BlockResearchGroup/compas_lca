from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import RoofType


class RoofFacet(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True, str_strip_whitespace=True)
    roof_type: RoofType = Field(RoofType.unknown, description="The type of roof or roof superstructure described in the dataset", examples=["green_roof", "pitched_roof", "other"])
