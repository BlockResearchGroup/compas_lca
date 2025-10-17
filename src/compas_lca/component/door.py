from typing import Optional
from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict

from compas_lca.enums import ComponentType

# DRAFT
class DoorFacet(BaseModel):

    model_config = ConfigDict(
        extra="forbid",                 # Forbid extra fields
        validate_assignment=True,       # Validate fields on assignment
        str_strip_whitespace=True       # Strip leading/trailing whitespace for str types
    )

    # Discriminator
    component_type: Literal[ComponentType.door] = Field(ComponentType.door)

    # Attributes to be inferred
    door_type: Optional[str] = Field(
        None,
        description="""
        PLACEHOLDER
        Stores door components (as found in LCA databases)
        """,
        examples=["wood_door", "safety_door", "revolving_door"]
    )
