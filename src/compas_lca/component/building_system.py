from typing import Optional
from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict

from compas_lca.enums import ComponentType
from compas_lca.enums import BuildingServiceType

# DRAFT
class BuildingSystemFacet(BaseModel):

    model_config = ConfigDict(
        extra="forbid",                 # Forbid extra fields
        validate_assignment=True,       # Validate fields on assignment
        str_strip_whitespace=True       # Strip leading/trailing whitespace for str types
    )

    # Discriminator
    component_type: Literal[ComponentType.building_services] = Field(ComponentType.building_services)

    # Attributes to be inferred
    building_service_type: BuildingServiceType = Field(
        BuildingServiceType.unknown,
        description="""
        Type of technical installation or buildign service system
        """,
        examples=["pv_panel", "air_conditioning", "building_automation"]
    )
