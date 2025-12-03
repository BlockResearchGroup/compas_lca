from typing import Optional

from textwrap import dedent

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import BituminousType
from compas_lca.enums import BituminousForm


class BituminousFacet(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    bituminous_type: BituminousType = Field(
        BituminousType.unknown,
        description="Binder/chemistry family of the bituminous material.",
        examples=["asphalt_mix", "polymer_modified_bitumen", "bitumen_emulsion", "asphalt_mix"]
    )
    bituminous_form: Optional[BituminousForm] = Field(
        None,
        description="Physical form or application configuration in which the bituminous material is supplied/installed.",
        examples=["sheet_membrane_torch_on", "shingle", "liquid_coating", "hot_mix"]
    )
    sd_value: Optional[float] = Field(
        None,
        description=dedent("""
            The measure of how much resistance to moisture diffusion th medium has, when compared to a meter of air.
            Only applicable to bituminous vapor barriers or retarders.
        """).strip(),
        examples=["10", "200"]
    )