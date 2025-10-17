from typing import Optional
from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict

from compas_lca.enums import ComponentType

# DRAFT
class CeilingFacet(BaseModel):

    model_config = ConfigDict(
        extra="forbid",                 # Forbid extra fields
        validate_assignment=True,       # Validate fields on assignment
        str_strip_whitespace=True       # Strip leading/trailing whitespace for str types
    )

    # Discriminator
    component_type: Literal[ComponentType.ceiling] = Field(ComponentType.ceiling)

    # Attributes to be inferred
    ceiling_type: Optional[str] = Field(
        None,
        description="""
        PLACEHOLDER
        Stores ceiling components (as found in LCA databases)
        """,
        examples=["acoustic_ceiling", "technical_ceiling", "multilayer_system"]
    )
