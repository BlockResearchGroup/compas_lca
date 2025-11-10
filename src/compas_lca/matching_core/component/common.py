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
        description="The type of component described in the dataset",
        examples=["window", "roof", "building_system"]
    )