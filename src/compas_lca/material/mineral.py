from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import MaterialType
from compas_lca.enums import MineralType
from compas_lca.enums import MineralForm


class MineralFacet(BaseModel):
    model_config = ConfigDict(
        extra = "forbid",           # Forbid extra fields
        validate_assignment=True,   # Validate fields on assignment
        str_strip_whitespace=True   # Strips leading and trailing whitespace for str types
    )

    # Discriminator
    material_type: Literal[MaterialType.mineral] = Field(MaterialType.mineral)

    # attributes to be inferred
    mineral_type: MineralType = Field(
        MineralType.unknown,
        description="""
        Dominant material composition or geological origin of the mineral-based product. 
        Classifies the substance according to its raw mineral type or source — such as binders 
        (lime, gypsum, cement), earth- or rock-derived materials (clay, sand, stone), 
        fired ceramics, glass, or industrial minerals. 
        This attribute reflects the material’s intrinsic composition, not its geometric form.
        """,
        examples=["lime", "clay", "sandstone", "glass"]
    )
    mineral_form: MineralForm = Field(
        MineralForm.unknown,
        description="""
        Physical form or product configuration in which the mineral material appears. 
        Describes how the material is manufactured or used, and reflects geometry or 
        application form rather than material composition.
        """,
        examples=["masonry_unit", "panel", "aggregate"]
    )