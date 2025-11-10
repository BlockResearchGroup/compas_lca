from typing import Optional

from textwrap import dedent

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import MineralType
from compas_lca.enums import MineralForm


class MineralFacet(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    mineral_type: MineralType = Field(
        MineralType.unknown,
        description=dedent("""
            Dominant material composition or geological origin of the mineral-based product. 
            Classifies the substance according to its raw mineral type or source — such as binders 
            (lime, gypsum, cement), earth- or rock-derived materials (clay, sand, stone), 
            fired ceramics, glass, or industrial minerals. 
            This attribute reflects the material's intrinsic composition, not its geometric form.
        """).strip(),
        examples=["lime", "clay", "sandstone", "glass"]
    )
    mineral_form: Optional[MineralForm] = Field(
        None,
        description=dedent("""
            Physical form or product configuration in which the mineral material appears. 
            Describes how the material is manufactured or used, and reflects geometry or 
            application form rather than material composition.
        """).strip(),
        examples=["masonry_unit", "panel", "aggregate"]
    )