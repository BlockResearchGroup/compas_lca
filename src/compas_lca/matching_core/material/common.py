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
            Choose exactly one of: 'mineral', 'concrete', 'wood', 'biobased', 'metallic', 
            'polymeric', 'bituminous', 'composite', 'unknown'.

            Decision rules (apply top-down):

            1) wood → Organic, lignocellulosic **wood-based** materials from trees.
            Map to 'wood' if the name or description contains ANY of:
                EN: wood, timber, lumber, parquet, plywood, veneer, LVL, laminated veneer lumber,
                    glulam, CLT, cross laminated timber, OSB, MDF, HDF, particleboard, chipboard,
                    hardboard, fibreboard/fiberboard, wood fiber, wood wool, cellulose (wood-based)
                DE: Holz, Brettschichtholz, Brettsperrholz, Kreuzlagenholz, Sperrholz, Furnierschichtholz,
                    LVL, Leimholz, Mehrschichtparkett, Parkett, Spanplatte, Faserplatte, MDF, HDF, OSB,
                    Holzfaser, Holzwolle, Zellulose
                FR: bois, contreplaqué, panneau, CLT, OSB, MDF
            examples: Multi-layer parquet, Cross laminated timber (CLT), MDF (uncoated), wood fiber insulation

            2) biobased → **Bio-based materials NOT derived from wood** (non-wood plant/animal fibers).
            Use this category if the dominant constituent comes from plants, animals, or crops **other than wood**.
                EN: hemp, flax, linen, jute, cotton, sheep wool, straw, cork, bamboo, coconut, sisal
                DE: Hanf, Flachs, Jute, Baumwolle, Schafwolle, Stroh, Kork, Bambus, Kokos, Sisal
                FR: chanvre, lin, jute, coton, laine de mouton, paille, liège, bambou
            examples: Hemp insulation, Sheep wool insulation, Cork board, Flax fiber

            3) concrete → Products where CEMENT (Portland, blended, alkali-activated) is the PRIMARY binder.
            Map to 'concrete' ONLY if cement-based:
                keywords: concrete, reinforced concrete, RC, UHPC, cement mortar, cement screed, 
                          cement board, fiber-reinforced concrete, precast concrete, Beton, béton
            NOTE: Lime plaster, gypsum products, calcium silicate → classify as 'mineral' (not concrete)

            4) mineral → Inorganic, nonmetallic, ceramic/stone/glass products WITHOUT cement as primary binder.
            Includes: lime-based products, gypsum, calcium silicate, natural stone, ceramics, glass.
                keywords: plaster, plasterboard, gypsum board, lime, calcium silicate, brick, tile, 
                          ceramic, glass, stone, granite, marble, slate, sand, gravel, mineral wool,
                          glass wool, rock wool, foam glass, perlite, vermiculite, aerogel
                DE: Gips, Kalk, Kalksandstein, Ziegel, Fliese, Keramik, Glas, Stein, Mineralwolle, Glaswolle
                FR: plâtre, chaux, brique, carreau, céramique, verre, pierre, laine minérale
            examples: Gypsum board, Lime plite, Calcium silicate board, Float glass, Mineral wool

            5) metallic → Metals and alloys.
                keywords: steel, stainless steel, aluminum, aluminium, copper, zinc, lead, brass, bronze, 
                          cast iron, iron, Stahl, Aluminium, Kupfer, Zink, acier, aluminium, cuivre
            examples: Steel profile, Aluminum sheet, Copper pipe

            6) polymeric → Synthetic organic polymers, plastics, rubbers, resins, foams (single polymer family).
                keywords: PVC, PE, PP, PET, PUR, PIR, PU, EPDM, acrylic, polyester, polyamide, nylon,
                          EPS, XPS, polystyrene, polyurethane, silicone, rubber, Kunststoff, plastique
            NOTE: If combined with fibers from a DIFFERENT material family (glass, carbon, basalt), 
                  classify as 'composite' instead.
            examples: PVC pipe, EPS insulation board, XPS panel, EPDM membrane

            7) bituminous → Hydrocarbon binders and composites.
                keywords: asphalt, bitumen, tar, bituminous membrane, Asphalt, Bitumen, bitume, asphalte
            examples: Bituminous roofing membrane, Asphalt paving

            8) composite → Engineered combination of TWO+ distinct material families.
            Use 'composite' when:
                - Fiber reinforcement from different family than matrix (GFRP, CFRP, fiber-cement)
                - Wood-plastic composites (WPC)
                - Explicitly named as composite or FRP
                keywords: FRP, GFRP, CFRP, fiber-cement, fibre-cement, WPC, wood-plastic, 
                          glass fiber reinforced, carbon fiber reinforced, basalt fiber reinforced
            NOTE: Reinforced concrete is 'concrete' (steel reinforcement is integral, not a composite layer)
            examples: GFRP profile, Fiber-cement board, WPC decking

            9) unknown → If none of the above can be determined from available text.

            BOUNDARY CLARIFICATIONS:
            • CONCRETE vs MINERAL: Use 'concrete' ONLY if Portland/blended cement is the primary binder.
              Lime plaster, gypsum board, calcium silicate → 'mineral'
            • COMPOSITE vs POLYMERIC: Use 'composite' if reinforced with fibers from different material family.
              Pure polymer products (EPS, XPS, PVC) → 'polymeric'
            • WOOD vs BIOBASED: Use 'wood' for tree-derived materials. Use 'biobased' for other plant/animal fibers.
            • Ignore surface coatings (laminates, varnish, paint) when determining the base material.
            • Always classify based on the **dominant** material by mass/volume or by explicit naming.
        """).strip(),
        examples=[
            "wood", "biobased", "concrete", "mineral", 
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
