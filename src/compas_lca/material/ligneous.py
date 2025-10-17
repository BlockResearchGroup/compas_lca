from typing import Optional
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import MaterialType
from compas_lca.enums import LigneousType
from compas_lca.enums import LigneousForm
from compas_lca.enums import BaseSpecies
from compas_lca.enums import LigneousProcessing
from compas_lca.enums import LigneousAdhesive
from compas_lca.enums import DryingMethod
from compas_lca.enums import ModificationMethod


class LigneousFacet(BaseModel):

    model_config = ConfigDict(
        extra = "forbid",           # Forbid extra fields
        validate_assignment=True,   # Validate fields on assignment
        str_strip_whitespace=True   # Strips leading and trailing whitespace for str types
    )

    # Discriminator
    material_type: Literal[MaterialType.ligneous] = Field(MaterialType.ligneous)

    # attributes to be inferred
    ligneous_type: LigneousType = Field(
        LigneousType.unknown,
        description="""
        Classification of the wood-based material according to its primary composition and manufacturing type. 
        Distinguishes between natural solid wood, engineered wood products , and chemically or thermally modified wood. 
        This field represents the dominant product family or structural form of the ligneous material.
        """,
        examples=["natural_softwood", "glue_laminated_timber", "oriented_strand_board", "modified_wood"]
    )
    base_species: BaseSpecies = Field(
        BaseSpecies.unknown,
        description="""
        Dominant wood species or species group used as the raw material basis for the product. 
        Refers to the primary botanical source of the lignocellulosic material.
        """,
        examples=["spruce", "larch", "oak", "other"]
    )
    ligneous_form: Optional[LigneousForm] = Field(
        None,
        description="""
        Physical form or geometric configuration of the wood-based product. 
        Describes how the ligneous material appears in its final product state
        """,
        examples=["lumber", "beam", "flooring"]
    )
    ligneous_processing: LigneousProcessing = Field(
        LigneousProcessing.unknown,
        description="""
        Primary processing state or manufacturing treatment applied to the wood material. 
        Refers to how the wood has been converted or finished from its raw form.
        """,
        examples=["rough_sawn", "planed_surfaced", "machine_graded"]
    )
    ligneous_adhesive: Optional[LigneousAdhesive] = Field(
        None,
        description="""
        Adhesive system (primarily used in engineered wood products). 
        Adhesives determine moisture resistance and durability of the product.
        Only if the material explicitly has an adhesive system, otherwise None.
        """,
        examples=["MUF", "pMDI", "PF"]
    )
    drying_method: Optional[DryingMethod] = Field(
        None,
        description="""
        If specified, the method used to reduce the moisture content of the wood prior to use or further processing. 
        """,
        examples=["fresh_green", "air_dried", "vacuum_dried"]
    )
    modification_method: Optional[ModificationMethod] = Field(
        None,
        description="""
        If specified, the chemical, thermal, or physical process used to alter the properties of the wood material. 
        """,
        examples=["thermally_modified", "acetylated", "other"]
    )