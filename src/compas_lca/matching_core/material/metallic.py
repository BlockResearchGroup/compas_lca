from typing import Optional

from textwrap import dedent

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from compas_lca.enums import MetallicType
from compas_lca.enums import MetallicForm
from compas_lca.enums import MetallicForming
from compas_lca.enums import MetallicProduction
from compas_lca.enums import MetallicSurfaceTreatment
from compas_lca.matching_core.normalization import normalize_metallic_type

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

            SPELLING NOTE: Use American English spelling as defined in the enum values:
            • Use `aluminum` (NOT "aluminium")
            
            Assign the metallic type according to the highest-priority category whose criteria are satisfied, 
            using the list below arranged from most specific to most general:

            1. `stainless_steel` — Corrosion-resistant steel with chromium content (typically ≥10.5%).
               Keywords: "stainless", "inox", "rostfrei", "18-8", "304", "316", "1.4301", "1.4404".
               
            2. `low_alloy_steel` — Weathering steel (Corten) or high-strength low-alloy (HSLA) steel.
               Keywords: "weathering", "Corten", "HSLA", "S355", "S460".

            3. `cast_iron` — Cast or ductile iron products.
               Keywords: "cast iron", "ductile iron", "Gusseisen".

            4. `carbon_steel` — Standard/mild/structural steel without special alloy qualifiers.
               Use for generic steel, reinforcement bars (rebar), structural sections.
               Keywords: "steel", "mild steel", "structural steel", "S235", "S275", "rebar".
               Note: Coatings (galvanized, powder-coated) do NOT affect the metallic_type.
                           
            5. Non-ferrous metals → use their specific enum value:
               • `aluminum` — All aluminum/aluminium products (use American spelling)
               • `copper`, `brass`, `bronze`, `zinc`, `lead`
                           
            6. `unknown` — If none of the above can be confidently assigned.
            
            Choose the MOST SPECIFIC applicable type. A "stainless steel door" → `stainless_steel`;
            a generic "steel door" → `carbon_steel` (unless stainless is specified).
        """).strip(),
    )
    @field_validator("metallic_type", mode="before")
    @classmethod
    def _normalize_metallic_type(cls, value):
        return normalize_metallic_type(value)
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