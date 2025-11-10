from typing import Optional

from textwrap import dedent

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import MetallicType
from compas_lca.enums import MetallicForm
from compas_lca.enums import MetallicForming
from compas_lca.enums import MetallicProduction
from compas_lca.enums import MetallicSurfaceTreatment


class MetallicFacet(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    metallic_type: MetallicType = Field(
        MetallicType.unknown,
        description=dedent("""
            Defines the dominant **base metal or alloy family** of the product.
            This refers to its **chemical composition**, not its shape, coating, or manufacturing process.

            Use this field to classify metallic materials by their primary alloy system
            (e.g., carbon steel, stainless steel, aluminum, copper).

            Mapping guidance:
            • Structural steel, rebar, mild steel → "carbon_steel"
            • Weathering steel, high-strength low-alloy (HSLA) → "low_alloy_steel"
            • Stainless or corrosion-resistant steel → "stainless_steel"
            • Cast iron, ductile iron, heritage ironwork → "cast_iron"
            • Non-ferrous metals (aluminum, copper, brass, bronze, zinc, lead) → respective enum
            • If composition cannot be determined → "unknown"
        """).strip(),
        examples=["carbon_steel", "stainless_steel", "aluminum", "copper", "other"],
    )
    metallic_form: MetallicForm = Field(
        MetallicForm.unknown,
        description=dedent("""
            Physical form or product shape in which the metallic material appears. 
            Defines the geometry or manufacturing state of the product rather than its composition.
            NOTE: A stud is a profile.
        """).strip(),
        examples=["profile", "plate", "rebar", "tube", "casting"]
    )
    steel_grade: Optional[str] = Field(
        None,
        description=dedent("""
            Standardized designation or grade of steel material, if applicable. 
            Refers to specific composition and mechanical property standards 
            (e.g., EN 10025, EN 10088, ASTM A36, AISI 304) that define alloy content, 
            strength class, and performance characteristics.
            Only applicable when `metallic_type` is a steel (e.g., carbon, low-alloy, or stainless).
        """).strip(),
        examples=["S235JR", "S355J2", "AISI 304", "1.4301"]
    )
    yield_strength: Optional[float] = Field(
        None,
        description=dedent("""
            Characteristic yield strength of the metallic material, expressed in megapascals (MPa).
            Represents the stress at which the material begins to deform plastically 
            (i.e., the transition from elastic to plastic behavior). 
            Only applicable to metallic materials with a defined yield point
            (e.g., carbon steel, low-alloy steel, stainless steel, aluminum alloys).
        """).strip(),
        examples=[235.0, 275.0, 355.0, 460.0]
    )
    metallic_production: Optional[MetallicProduction] = Field(
        None,
        description=dedent("""
            Production route of the metallic material, referring to the 
            metallurgical process used to produce the base metal or alloy before shaping or forming. 
            This attribute includes ore-based (primary) and recycled or scrap-based 
            (secondary) routes.
        """).strip(),
        examples=["ore_bf_bof", "scrap_eaf", "scrap_remelt"]
    )
    metallic_forming: Optional[MetallicForming] = Field(
        None,
        description=dedent("""
            Forming or shaping process used to produce the metallic product from its semi-finished state. 
            Describes the main mechanical or thermal method that gives the material its final geometry, 
            rather than the chemical or metallurgical production route.
        """).strip(),
        examples=["rolled", "extruded", "forged", "cast"]
    )
    metallic_surface_treatment: Optional[MetallicSurfaceTreatment] = Field(
        None,
        description=dedent("""
            Protective or decorative surface treatment applied to the metallic product. 
            Includes both organic and inorganic coatings and surface finishes or conversion treatments.
        """).strip(),
        examples=["galvanized", "anodized", "painted", "powder_coated", "none"]
    )