from typing import List
from typing import Optional

from textwrap import dedent

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import MaterialType
from compas_lca.enums import ApplicationAreas
from compas_lca.enums import FunctionalTypes
from compas_lca.enums import InsulationInfo

from compas_lca.validators import MaterialTypeValidated

class MaterialCommon(BaseModel):
    """Shared fields for all types for all materials (regardless of facet)"""
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    material_type: MaterialTypeValidated = Field(
        MaterialType.unknown,
        description=dedent("""
            Classify the product by its dominant base material (composition), not shape, coating, or process.
            Choose exactly one of: 'mineral', 'concrete', 'wood', 'biobased_nonwood', 'metallic', 
            'polymeric', 'bituminous', 'composite', 'unknown'.

            Decision rules (apply top-down):

            1) wood → Organic, lignocellulosic **wood-based** materials.
            Map to 'wood' if the name or description contains ANY of:
                english: wood, timber, lumber, parquet, plywood, veneer, LVL, laminated veneer lumber,
                        glulam, CLT, cross laminated timber, OSB, MDF, HDF, particleboard, chipboard,
                        hardboard, fibreboard/fiberboard, cork, bamboo
                german: Holz, Brettschichtholz, Brettsperrholz, Kreuzlagenholz, Sperrholz, Furnierschichtholz,
                        LVL, Leimholz, Mehrschichtparkett, Parkett, Spanplatte, Faserplatte, MDF, HDF, OSB
            examples: Multi-layer parquet, Cross laminated timber (CLT), MDF (uncoated)

            2) biobased_nonwood → **Bio-based materials NOT derived from wood**.
            Use this category if the dominant constituent comes from plants, animals, or crops **other than wood**.
            keywords: cotton, flax, linen, hemp, sheep wool, straw, cork, bamboo

            3) concrete → Cementitious / hydraulic binder with aggregates.
            keywords: concrete, reinforced concrete, RC, mortar, grout, UHPC, screed

            4) mineral → Inorganic, nonmetallic, ceramic/stone/glass (excluding concrete).
            keywords: plaster, plasterboard, brick, tile, ceramic, glass, stone, gypsum, rammed earth

            5) metallic → Metals and alloys.
            keywords: steel, stainless steel, aluminum, copper, zinc, lead, brass, bronze, cast iron

            6) polymeric → Synthetic organic polymers, plastics, rubbers, resins, foams.
            keywords: PVC, PE, PP, PET, PUR, PU, EPDM, acrylic, polyester, polyamide, nylon

            7) bituminous → Hydrocarbon binders and composites.
            keywords: asphalt, bitumen, tar, bituminous membrane

            8) composite → Engineered combination where no single base material dominates OR
            explicitly named composite.
            keywords: FRP, GFRP, CFRP, sandwich panel (if core and skins differ and no dominant base)

            9) unknown → If none of the above can be determined from available text.

            Notes:
            • Ignore surface coatings (laminates, varnish, paint) when determining the base material.
            • Always classify based on the **dominant** material by mass/volume or by explicit naming.
        """).strip(),
        examples=[
            "wood", "biobased_nonwood", "concrete", "mineral", 
            "metallic", "polymeric", "bituminous", "composite"
        ]
    )

    functional_types: List[FunctionalTypes] = Field(
        [FunctionalTypes.unknown],
        description=dedent("""
        List of the product's intended functional roles (i.e., function or function-related layer type)
        as explicitly declared in the input dataset.

        Rules:
        - Choose one single best PRIMARY intent whenever possible.
        - Add additional values ONLY if the material/product explicitly serves multiple 
        primary functions simultaneously (e.g., “thermal + acoustic insulation” panel).
        - If the role is not clearly stated in the raw data, keep “unknown”.
        - Air is NOT assignable and results in an empty list.
        """).strip(),
        examples=[
            ["structural"],
            ["insulation"],
            ["covering", "lining"],
            ["membrane", "waterproofing"]
        ]
    )
    application_areas: List[ApplicationAreas] = Field(
        [ApplicationAreas.unknown],
        description=dedent("""
            List of all explicitly stated application areas of a building (e.g., walls, floors, roofs). 
            This field allows multiple values if the material is applicable to several component types. 
            Only assign application areas that are explicitly stated in the raw data, or unambiguously
            common sense (e.g., ready-mixed concrete can be used for slabs, walls, columns, etc.)
        """).strip(),
        examples=[
            ["balcony", "railing"],
            ["wall", "slab", "column"],
            ["floor", "ceiling"],
            ["roof"]
        ]
    )
    insulation_info: Optional[List[InsulationInfo]] = Field(
        None,
        description=dedent("""
            High-level tags describing an insulation product's purpose and/or form.
            Populate this field ONLY if the product's `functional_types` includes 'insulation'.
            Choose all that apply if both purpose and form are stated (e.g., thermal + acoustic + semi_rigid).
            Examples:
            - EPS board for façade insulation → ['thermal', 'rigid']
            - Mineral wool slab declared for thermal + acoustic walls → ['thermal', 'acoustic', 'semi_rigid']
            - Underlay roll with ΔLw rating → ['impact_sound', 'flexible_roll_batt']
        """).strip(),
        examples=[
            ["thermal", "rigid"],
            ["thermal", "acoustic", "semi_rigid"],
            ["impact_sound", "flexible_roll_batt"]
        ]
    )
