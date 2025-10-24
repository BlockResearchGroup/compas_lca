from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import ComponentType

class ComponentCommon(BaseModel):
    """
    Shared fields for all types of construction components (pre-assembled elements with multiple materials)
    note: Rather sparse for now, to be extended in the future
    """
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    component_type: ComponentType = Field(
        ComponentType.unknown,
        description="""
        Overview of component types, yet to be defined more in detail
        """,
        examples=["window", "roof", "building_system"]
    )