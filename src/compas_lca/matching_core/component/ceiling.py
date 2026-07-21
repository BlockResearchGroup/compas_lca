from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import CeilingForm
from compas_lca.enums import CeilingType


class CeilingFacet(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True, str_strip_whitespace=True)
    ceiling_type: CeilingType = Field(
        CeilingType.unknown, description="Ceiling type based on dominant/primary material composition & buildup", examples=["gypsum_board", "wood_panel", "metal_mesh"]
    )
    ceiling_form: Optional[CeilingForm] = Field(
        None, description="How the ceilings are built or supported. Construction system and/or form.", examples=["suspended", "direct_applied", "vaulted"]
    )
