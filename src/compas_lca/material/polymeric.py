from typing import Optional
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import MaterialType
from compas_lca.enums import PolymericType
from compas_lca.enums import PolymericForm


class PolymericFacet(BaseModel):

    model_config = ConfigDict(
        extra = "forbid",           # Forbid extra fields
        validate_assignment=True,   # Validate fields on assignment
        str_strip_whitespace=True   # Strips leading and trailing whitespace for str types
    )

    # Discriminator
    material_type: Literal[MaterialType.polymeric] = Field(MaterialType.polymeric)

    # attributes to be inferred
    polymeric_type: PolymericType = Field(
        PolymericType.unknown,
        description="""
        Dominant polymer or elastomer composition of the material. 
        Identifies the base polymer family used in the product, such as thermoplastics 
        thermosets, elastomers, or biopolymer composites.
        """,
        examples=["pvc", "pe", "polyurethane", "rubber"]
    )
    polymeric_form: Optional[PolymericForm] = Field(
        None,
        description="""
        Physical form or manufactured configuration in which the polymeric material appears. 
        Describes the product geometry or application type.
        """,
        examples=["sheet_membrane", "profile_rigid", "floor_tile_modular"]
    )
    recycled_content: Optional[bool] = Field(
        None,
        description="""
        This field describes if the polymeric material is has recycled content (True) or is primary (False)
        Assign a boolean value if this information is explicitly stated in the input dataset,
        or if the value unambiguously clear (common sense).
        """,
        examples=[True, False]
    )