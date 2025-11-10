from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict

from compas_lca.enums import BuildingServiceType

class BuildingServiceFacet(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    building_service_type: BuildingServiceType = Field(
        BuildingServiceType.unknown,
        description="Type of technical installation or buildign service system",
        examples=["pv_panel", "air_conditioning", "building_automation"]
    )