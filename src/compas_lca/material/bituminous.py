from typing import Optional
from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict

from compas_lca.enums import MaterialType
from compas_lca.enums import BituminousType
from compas_lca.enums import BituminousForm


class BituminousFacet(BaseModel):

    model_config = ConfigDict(
        extra="forbid",                 # Forbid extra fields
        validate_assignment=True,       # Validate fields on assignment
        str_strip_whitespace=True       # Strip leading/trailing whitespace for str types
    )

    # Discriminator
    material_type: Literal[MaterialType.bituminous] = Field(MaterialType.bituminous)

    # Attributes to be inferred
    bituminous_type: BituminousType = Field(
        BituminousType.unknown,
        description="""
        Binder/chemistry family of the bituminous material. 
        """,
        examples=["asphalt_mix", "polymer_modified_bitumen", "bitumen_emulsion", "asphalt_mix"]
    )
    bituminous_form: Optional[BituminousForm] = Field(
        None,
        description="""
        Physical form or application configuration in which the bituminous material is supplied/installed.
        """,
        examples=["sheet_membrane_torch_on", "shingle", "liquid_coating", "hot_mix"]
    )
    sd_value: Optional[float] = Field(
        None,
        description="""
        The measure of how much resistance to moisture diffusion th medium has, when compared to a meter of air.
        Only applicable to bituminous vapor barriers or retarders.
        """,
        examples=["10", "200"]
    )
