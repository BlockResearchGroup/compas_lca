"""
Note: this is all bio-based EXCEPT for wood-based materials.

For ontological clarity, this new facet is created for
biobased materials that do NOT fall under the ligneous,
or wood-based category. Since they are very idiosyncratic
and sparse, they will not require a bunch of shared attributes,
and probably a set of enums (types) will help with any distinction
and suffices in conjunction with MaterialCommon.
"""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from textwrap import dedent

from compas_lca.enums import BiobasedType
from compas_lca.matching_core.normalization import normalize_biobased_type

class BiobasedFacet(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    biobased_type: BiobasedType = Field(
        BiobasedType.unknown,
        description=dedent("""
            Categorical type of a NON-wood biobased material.

            Use one of the specific categories when the material clearly matches:
            • cotton             → "cotton"
            • cork (bark)        → "cork"
            • flax / linen       → "flax"
            • hemp               → "hemp"
            • sheep wool         → "sheep_wool"
            • straw (wheat, rice, barley, etc.) → "straw"

            Choose these specific types whenever the named material is the primary
            constituent or explicitly identified.

            If the material is clearly bio-based but does not fit any specific or generic category,
            use →  "other"

            If the material description is ambiguous, incomplete, or it is unclear whether the
            material is even bio-based use → "unknown"
        """).strip(),
        examples=["cotton", "hemp", "straw", "other", "unknown"]
    )
    @field_validator("biobased_type", mode="before")
    @classmethod
    def _normalize_biobased_type(cls, value):
        return normalize_biobased_type(value)