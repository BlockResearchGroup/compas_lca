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
            Defines the dominant base metal or alloy family of the product.
            This classification refers strictly to the material's chemical composition,
            not its geometry, coating, finish, or manufacturing process.

            Assign the metallic type according to the highest-priority category whose criteria are satisfied, 
            using the list below arranged from most specific to most general:

            1. Stainless or corrosion-resistant steel → "stainless_steel"

            2. Weathering steel or high-strength low-alloy (HSLA) steel → "low_alloy_steel"

            3. Cast or ductile iron → "cast_iron"

            4. Structural / mild / carbon steel → "carbon_steel"
            Use for generic or structural steel without alloy-specific qualifiers.
            Coatings (galvanized, powder-coated, painted) do not affect the metallic_type.
                           
            5. Non-ferrous metals → use their specific enum
            "aluminum", "copper", "brass", "bronze", "zinc", "lead".
                           
            6. If none of the above categories can be confidently assigned → "unknown"
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
            Specific **steel grade or designation**, *not* the standard number.
            This field identifies the **grade symbol** defined *within* a steel standard 
            (the alphanumeric designation that encodes strength class and alloy composition), 
            rather than the name of the standard itself.
            Use this field for values such as:
            'S235JR', 'S460NL'
            Do NOT provide:
            - Only a standard number or document reference (e.g., "EN 10025", "ASTM A240")
            The grade should correspond to the product's declared composition or mechanical properties 
            as per a recognized steel specification. If not stated in the source, leave empty.
            Applicable only when `metallic_type` refers to a steel (e.g., carbon, low-alloy, or stainless).
        """).strip(),
        examples=["S235JR", "S355J2", "AISI 304", "1.4301", "ASTM A36"]
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