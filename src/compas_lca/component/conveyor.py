from typing import Optional
from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict

from compas_lca.enums import ComponentType

# DRAFT
class ConveyorFacet(BaseModel):

    model_config = ConfigDict(
        extra="forbid",                 # Forbid extra fields
        validate_assignment=True,       # Validate fields on assignment
        str_strip_whitespace=True       # Strip leading/trailing whitespace for str types
    )

    # Discriminator
    component_type: Literal[ComponentType.conveyor] = Field(ComponentType.conveyor)

    # Attributes to be inferred
    conveyor_type: Optional[str] = Field(
        None,
        description="""
        PLACEHOLDER
        Stores conveyor components (as found in LCA databases)
        """,
        examples=["elevator", "escalator", "wormhole"]
    )
