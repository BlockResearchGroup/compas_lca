from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import StairType


class StairFacet(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True, str_strip_whitespace=True)
    stair_type: StairType = Field(StairType.unknown, description="The type of stair described in the dataset", examples=["straight", "spiral", "other"])
