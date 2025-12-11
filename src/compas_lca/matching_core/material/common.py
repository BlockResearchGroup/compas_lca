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
                    Holzfaser, Holzwolle, Zellulose (Holz-basiert)
                FR: bois, contreplaqué, panneau, CLT, OSB, MDF
            NOTE: "Cellulose" insulation from recycled paper/wood pulp → 'wood'
            examples: Multi-layer parquet, Cross laminated timber (CLT), MDF (uncoated), wood fiber insulation

            2) biobased → **Bio-based materials NOT derived from wood** (non-wood plant/animal fibers).
            CRITICAL: If product name contains ANY of these keywords → classify as 'biobased', NOT 'unknown':
                EN: hemp, flax, linen, jute, cotton, sheep wool, straw, cork, bamboo, coconut, sisal,
                    coir, seagrass, cattail, kenaf, ramie, kapok, animal fiber, plant fiber
                DE: Hanf, Flachs, Jute, Baumwolle, Schafwolle, Stroh, Kork, Bambus, Kokos, Sisal,
                    Thermo-Hanf, Thermohanf, Naturfaser, Pflanzenfaser, Tierfaser
                FR: chanvre, lin, jute, coton, laine de mouton, paille, liège, bambou, coco
            Product names like "Thermo Hemp", "Hemp insulation", "Sheep wool", "Cork board" → 'biobased'
            examples: Hemp insulation, Sheep wool insulation, Cork board, Flax fiber, Jute fiber

            3) concrete → Products where CEMENT (Portland, blended, alkali-activated) is the PRIMARY binder.
            INCLUDES aerated/cellular concrete products:
                keywords: concrete, reinforced concrete, RC, UHPC, cement mortar, cement screed, 
                          cement board, fiber-reinforced concrete, precast concrete, Beton, béton,
                          aerated concrete, autoclaved aerated concrete, AAC, cellular concrete,
                          Porenbeton, Gasbeton, Ytong, Hebel, foamed concrete, lightweight concrete
            NOTE: Lime plaster, gypsum products, calcium silicate → classify as 'mineral' (not concrete)
            examples: Ready-mixed concrete, Precast concrete, Aerated concrete block (AAC/Porenbeton)

            4) mineral → Inorganic, nonmetallic, ceramic/stone/glass products WITHOUT cement as primary binder.
            Includes: lime-based products, gypsum, calcium silicate, natural stone, ceramics, glass.
                keywords: plaster, plasterboard, gypsum board, lime, calcium silicate, brick, tile, 
                          ceramic, glass, stone, granite, marble, slate, sand, gravel, mineral wool,
                          glass wool, rock wool, foam glass, perlite, vermiculite, aerogel, calcium sulfate
                DE: Gips, Kalk, Kalksandstein, Ziegel, Fliese, Keramik, Glas, Stein, Mineralwolle, Glaswolle
                FR: plâtre, chaux, brique, carreau, céramique, verre, pierre, laine minérale
            NOTE: Pure cement powder/paste without aggregate → 'mineral' (cement as raw material)
            examples: Gypsum board, Lime plaster, Calcium silicate board, Float glass, Mineral wool

            5) metallic → Metals and alloys.
                keywords: steel, stainless steel, aluminum, aluminium, copper, zinc, lead, brass, bronze, 
                          cast iron, iron, Stahl, Aluminium, Kupfer, Zink, acier, aluminium, cuivre
            examples: Steel profile, Aluminum sheet, Copper pipe

            6) polymeric → Synthetic organic polymers, plastics, rubbers, resins, foams (single polymer family).
                keywords: PVC, PE, PP, PET, PUR, PIR, PU, EPDM, acrylic, polyester, polyamide, nylon,
                          EPS, XPS, polystyrene, polyurethane, silicone, rubber, epoxy, resin,
                          Kunststoff, plastique, Harz, résine
            IMPORTANT: Pure resins (epoxy, polyester, acrylic resin) WITHOUT fiber reinforcement → 'polymeric'
            Only classify as 'composite' if EXPLICITLY combined with glass/carbon/basalt fibers.
            examples: PVC pipe, EPS insulation board, XPS panel, EPDM membrane, Epoxy resin, PU foam

            7) bituminous → Hydrocarbon binders and composites.
                keywords: asphalt, bitumen, tar, bituminous membrane, Asphalt, Bitumen, bitume, asphalte
            examples: Bituminous roofing membrane, Asphalt paving

            8) composite → Engineered combination of TWO+ distinct material families.
            Use 'composite' ONLY when:
                - EXPLICITLY fiber-reinforced with fibers from DIFFERENT material family
                - Product name contains: GFRP, CFRP, GFK, CFK, fiber-cement, fibre-cement, WPC,
                  "glass fiber reinforced", "carbon fiber reinforced", "basalt fiber reinforced"
                - Wood-plastic composites (WPC), wood-cement composites
            NOTE: Reinforced concrete is 'concrete' (steel reinforcement is integral)
            NOTE: Pure polymers/resins WITHOUT explicit fiber reinforcement → 'polymeric', NOT 'composite'
            examples: GFRP profile, Fiber-cement board (Eternit), WPC decking, Carbon fiber composite

            9) unknown → ONLY if none of the above can be determined from available text.
            Avoid 'unknown' if ANY recognizable material keyword is present.

            BOUNDARY CLARIFICATIONS:
            • CONCRETE vs MINERAL: 'concrete' if cement-bonded aggregate or aerated cement product.
              Lime plaster, gypsum board, calcium silicate, pure cement powder → 'mineral'
            • COMPOSITE vs POLYMERIC: 'composite' ONLY if explicitly fiber-reinforced.
              Pure polymers, foams, resins (EPS, XPS, PVC, epoxy resin) → 'polymeric'
            • WOOD vs BIOBASED: 'wood' for tree-derived materials. 'biobased' for other plant/animal fibers.
            • Ignore surface coatings (laminates, varnish, paint) when determining the base material.
            • Always classify based on the **dominant** material by mass/volume or by explicit naming.
        """).strip(),
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
