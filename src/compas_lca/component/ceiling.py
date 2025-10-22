from typing import Optional
from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict

from compas_lca.enums import ComponentType
from compas_lca.enums import CeilingType
from compas_lca.enums import CeilingForm

class CeilingFacet(BaseModel):

    model_config = ConfigDict(
        extra="forbid",                 # Forbid extra fields
        validate_assignment=True,       # Validate fields on assignment
        str_strip_whitespace=True       # Strip leading/trailing whitespace for str types
    )

    # Discriminator
    component_type: Literal[ComponentType.ceiling] = Field(ComponentType.ceiling)

    # Attributes to be inferred
    ceiling_type: CeilingType = Field(
        CeilingType.unknown,
        description="""
        Ceiling type based on dominant/primary material composition & buildup
        """,
        examples=["gypsum_board", "wood_panel", "metal_mesh"]
    )
    ceiling_form: Optional[CeilingForm] = Field(
        None,
        description="""
        How the ceilings are built or supported.
        Construction system and/or form.
        """,
        examples=["suspended", "direct_applied", "vaulted"]
    )
