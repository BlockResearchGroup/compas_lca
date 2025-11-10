from typing import Optional

from textwrap import dedent

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import LigneousType
from compas_lca.enums import LigneousForm
from compas_lca.enums import BaseSpecies
from compas_lca.enums import LigneousProcessing
from compas_lca.enums import LigneousAdhesive
from compas_lca.enums import DryingMethod
from compas_lca.enums import ModificationMethod


class LigneousFacet(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    ligneous_type: LigneousType = Field(
        LigneousType.unknown,
        description=dedent("""
            Classification of the wood-based material according to its primary composition and manufacturing type. 
            Distinguishes between natural solid wood, engineered wood products , and chemically or thermally modified wood. 
            This field represents the dominant product family or structural form of the ligneous material.
            Example mappings: '3-Schicht-Platte' or '5-Schicht-Platte' is "ligneous_type" = "cross_laminated_timber" 
        """).strip(),
        examples=["natural_softwood", "cross_laminated_timber", "oriented_strand_board", "modified_wood"]
    )
    ligneous_form: LigneousForm = Field(
        LigneousForm.unknown,
        description=dedent("""
            Physical form or geometric configuration of the wood-based product. 
            Describes how the ligneous material appears in its final product state
        """).strip(),
        examples=["panel", "beam", "flooring"]
    )
    strength_class_designation: Optional[str] = Field(
        None,
        description=dedent("""
            Strength class designation per European standards.
            Typical values include EN 338 solid timber classes (softwood 'C' and hardwood 'D'),
            e.g. 'C24', 'D40', and EN 14080 glulam classes with suffix 'c' (combined) or 'h' (homogeneous),
            e.g. 'GL28c', 'GL32h'. Use None when not clearly stated or not applicable (e.g. panels like OSB/MDF).
        """).strip(),
        examples=["C24", "D40", "GL28c", "GL32h"]
    )

    base_species: Optional[BaseSpecies] = Field(
        None,
        description=dedent("""
            Dominant wood species or species group used as the raw material basis for the product. 
            Refers to the primary botanical source of the lignocellulosic material.
        """).strip(),
        examples=["spruce", "larch", "oak", "other"]
    )
    ligneous_processing: Optional[LigneousProcessing] = Field(
        None,
        description=dedent("""
            Primary processing state or manufacturing treatment applied to the wood material. 
            Refers to how the wood has been converted or finished from its raw form.
        """).strip(),
        examples=["rough_sawn", "planed_surfaced", "machine_graded"]
    )
    ligneous_adhesive: Optional[LigneousAdhesive] = Field(
        None,
        description=dedent("""
            Adhesive system (primarily used in engineered wood products). 
            Adhesives determine moisture resistance and durability of the product.
            Only if the material explicitly has an adhesive system, otherwise None.
        """).strip(),
        examples=["MUF", "pMDI", "PF"]
    )
    drying_method: Optional[DryingMethod] = Field(
        None,
        description="The method used to reduce the moisture content of the wood prior to use or further processing.",
        examples=["fresh_green", "air_dried", "vacuum_dried"]
    )
    modification_method: Optional[ModificationMethod] = Field(
        None,
        description="The chemical, thermal, or physical process used to alter the properties of the wood material.",
        examples=["thermally_modified", "acetylated", "other"]
    )