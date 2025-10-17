from typing import Optional
from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict

from compas_lca.enums import ComponentType

# DRAFT
class WallFacet(BaseModel):

    model_config = ConfigDict(
        extra="forbid",                 # Forbid extra fields
        validate_assignment=True,       # Validate fields on assignment
        str_strip_whitespace=True       # Strip leading/trailing whitespace for str types
    )

    # Discriminator
    component_type: Literal[ComponentType.wall] = Field(ComponentType.wall)

    # Attributes to be inferred
    wall_type: Optional[str] = Field(
        None,
        description="""
        PLACEHOLDER
        Stores wall components (as found in LCA databases)
        """,
        examples=["wall_external_insulation", "masonry_wall_system"]
    )