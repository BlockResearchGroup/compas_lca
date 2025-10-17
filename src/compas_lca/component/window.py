from typing import Optional
from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict

from compas_lca.enums import ComponentType

# DRAFT
class WindowFacet(BaseModel):

    model_config = ConfigDict(
        extra="forbid",                 # Forbid extra fields
        validate_assignment=True,       # Validate fields on assignment
        str_strip_whitespace=True       # Strip leading/trailing whitespace for str types
    )

    # Discriminator
    component_type: Literal[ComponentType.window] = Field(ComponentType.window)

    # Attributes to be inferred
    window_type: Optional[str] = Field(
        None,
        description="""
        PLACEHOLDER
        Stores window components (as found in LCA databases)
        """,
        examples=["triple_glazed", "wooden_frame", "skylight"]
    )