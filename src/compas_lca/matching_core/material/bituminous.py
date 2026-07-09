from typing import Optional

from textwrap import dedent

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from compas_lca.enums import BituminousType
from compas_lca.enums import BituminousForm
from compas_lca.matching_core.normalization import normalize_bituminous_type


class BituminousFacet(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    bituminous_type: BituminousType = Field(
        BituminousType.unknown,
        description=dedent("""
        Binder / chemistry family of the bituminous material.

        Select exactly one value according to the primary binder type used:
        - asphalt_mix:
        Use when the material is an asphaltic concrete or asphalt mix used for paving.
        - mastic_asphalt:
        Use when the material is a voidless, high-binder-content asphalt,
        commonly used for waterproofing layers, flooring, or roofing applications.
        - bitumen:
        Use when the binder is unmodified petroleum bitumen, and the material is not a formulated asphalt mix.
        - polymer_modified_bitumen:
        Use when the bitumen binder is chemically or physically modified with polymers
        - bitumen_emulsion:
        Use when the binder is a water-based bitumen emulsion, typically applied cold
        - other:
        Use only when the material is clearly bituminous but does not fit any of the above categories.
        - unknown:
        Use when the material is known to be bituminous, but the binder or chemistry family
        cannot be determined from the available information.
        """).strip(),
        examples=["asphalt_mix", "mastic_asphalt", "bitumen_emulsion"]
    )
    @field_validator("bituminous_type", mode="before")
    @classmethod
    def _normalize_bituminous_type(cls, value):
        return normalize_bituminous_type(value)
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