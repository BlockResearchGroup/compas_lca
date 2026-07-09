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

            ═══════════════════════════════════════════════════════════════════════════════
            PRIORITY KEYWORD DETECTION — Apply FIRST before any other analysis:
            ═══════════════════════════════════════════════════════════════════════════════
            
            IF product name/description contains ANY of these keywords → classify immediately:
            
            • BIOBASED keywords (non-wood plant/animal fibers) → 'biobased':
              hemp, flax, linen, jute, sheep wool, straw, cork, cotton,
              bamboo, coconut

            • WOOD keywords (tree-derived) → 'wood':
              wood, timber, lumber, plywood, veneer, LVL, glulam,
              CLT, OSB, MDF, HDF, particleboard,
              chipboard, fiberboard, wood fiber,
              wood wool, cellulose (insulation)
            
            • METALLIC keywords → 'metallic':
              steel, steel sheet, blech, stainless, aluminum, copper,
              zinc, brass, bronze, iron, cast iron, lead
            
            • POLYMERIC keywords → 'polymeric':
              PVC, polyvinyl, PE, polyethylene, PP, polypropylene, PET, polyester,
              PUR, PIR, polyurethane, EPDM, EPS, XPS, polystyrene, acrylic, polyamide,
              nylon, silicone, rubber
            
            • BITUMINOUS keywords → 'bituminous':
              asphalt, bitumen, tar, bituminous
            
            • CONCRETE keywords → 'concrete':
              concrete, reinforced concrete, RC, precast,
              aerated concrete, AAC, cement screed
            
            • MINERAL keywords → 'mineral':
              glass, gypsum, plaster, lime, calcium silicate,
              ceramic, brick, tile, stone,
              granite, marble, slate, mineral wool, glass wool, rock wool
            
            ═══════════════════════════════════════════════════════════════════════════════
            COMPOSITE — Use ONLY for explicit multi-material products:
            ═══════════════════════════════════════════════════════════════════════════════
            
            'composite' → ONLY when EXPLICITLY fiber-reinforced or multi-family combined:
              - GFRP, CFRP, fiber-cement, WPC, Linoleum
              - "glass fiber reinforced", "carbon fiber reinforced", "basalt fiber reinforced"
              - Wood-plastic composite, wood-cement composite
            NOTE: Reinforced concrete → 'concrete' (steel reinforcement is integral)
            NOTE: Pure resins/polymers WITHOUT fibers → 'polymeric', NOT 'composite'
            
            ═══════════════════════════════════════════════════════════════════════════════
            UNKNOWN — Use as last resort:
            ═══════════════════════════════════════════════════════════════════════════════
            
            'unknown' → ONLY if NO recognizable material keyword is present in the text.
            Only if the material is described as 'insulation' but contains no recognizable base material keywords, assign 'unknown'.
            NEVER use 'unknown' if ANY of the above keywords appear in the product name.
            
            ═══════════════════════════════════════════════════════════════════════════════
            BOUNDARY CLARIFICATIONS:
            ═══════════════════════════════════════════════════════════════════════════════
            
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
        - Whenver the material explicitly mentions "Stud Layer" assigng "stud_layer" and not "framing"
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
