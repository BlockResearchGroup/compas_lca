from typing import Literal
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import MaterialType
from compas_lca.enums import MetallicType
from compas_lca.enums import MetallicForm
from compas_lca.enums import MetallicForming
from compas_lca.enums import MetallicProduction
from compas_lca.enums import MetallicSurfaceTreatment


class MetallicFacet(BaseModel):

    model_config = ConfigDict(
        extra = "forbid",           # Forbid extra fields
        validate_assignment=True,   # Validate fields on assignment
        str_strip_whitespace=True   # Strips leading and trailing whitespace for str types
    )

    # Discriminator
    material_type: Literal[MaterialType.metallic] = Field(MaterialType.metallic)

    # attributes to be inferred
    metallic_type: MetallicType = Field(
        MetallicType.unknown,
        description="""
        Dominant material composition or alloy family of the metallic product.
        Refers to the base metal or alloy system that defines its chemical and physical properties,
        independent of its geometric form or production process.
        """,
        examples=["carbon_steel", "stainless_steel", "aluminum", "copper", "other"]
    )
    metallic_production: MetallicProduction = Field(
        MetallicProduction.unknown,
        description="""
        Production route of the metallic material, referring to the 
        metallurgical process used to produce the base metal or alloy before shaping or forming. 
        This attribute includes ore-based (primary) and recycled or scrap-based 
        (secondary) routes.
        """,
        examples=["ore_bf_bof", "scrap_eaf", "scrap_remelt"]
    )
    metallic_forming: Optional[MetallicForming] = Field(
        None,
        description="""
        Forming or shaping process used to produce the metallic product from its semi-finished state. 
        Describes the main mechanical or thermal method that gives the material its final geometry, 
        rather than the chemical or metallurgical production route.
        """,
        examples=["rolled", "extruded", "forged", "cast"]
    )
    metallic_form: Optional[MetallicForm] = Field(
        None,
        description="""
        Physical form or product shape in which the metallic material appears. 
        Defines the geometry or manufacturing state of the product rather than its composition.
        """,
        examples=["sheet", "plate", "rebar", "tube", "casting"]
    )
    metallic_surface_treatment: Optional[MetallicSurfaceTreatment] = Field(
        None,
        description="""
        Protective or decorative surface treatment applied to the metallic product. 
        Includes both organic and inorganic coatings and surface finishes or conversion treatments.
        """,
        examples=["galvanized", "anodized", "painted", "powder_coated", "none"]
    )
    steel_grade: Optional[str] = Field(
        None,
        description="""
        Standardized designation or grade of steel material, if applicable. 
        Refers to specific composition and mechanical property standards 
        (e.g., EN 10025, EN 10088, ASTM A36, AISI 304) that define alloy content, 
        strength class, and performance characteristics.
        Only applicable when `metallic_type` is a steel (e.g., carbon, low-alloy, or stainless).
        """,
        examples=["S235JR", "S355J2", "AISI 304", "1.4301"]
    )