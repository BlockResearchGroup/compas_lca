from textwrap import dedent

from compas_lca.enums import (
    BiobasedType,
    BituminousType,
    ComponentType,
    CompositeType,
    ConcreteType,
    FrameType,
    MaterialType,
    MetallicType,
    MineralType,
    PolymericType,
    WindowFittingType,
    WoodType,
    DoorType,
)

# Centralized prompt for one-shot type-only classification.
# This condenses the scattered guidance from the multi-stage
# Pydantic/Context flows into one concise instruction block.


def entry_type_guide() -> str:
    """Decision rules for classifying entry_type (material vs component vs unknown)."""
    return dedent(
        """
        ENTRY_TYPE DECISION RULES (apply top-to-bottom):
        1) Single material or uniform layer (even if pre-formed as sheet/panel/block/profile) → `material`
        2) Functional element with MULTIPLE distinct material families combined → `component`
        3) Insufficient or contradictory information → `unknown`

        KEY SIGNALS FOR COMPONENT (multi-material assembly):
        • Product name mentions "with ... facing/cladding/core" (e.g., "PU boards with aluminium facing")
        • Contains terms like "sandwich", "composite panel", "ETICS", "WDVS", "IGU", "insulating glass"
        • Multiple distinct material families listed together (e.g., metal + foam, glass + spacer + gas)
        • Complete assembled units: window system, door system, ceiling system, curtain wall

        KEY SIGNALS FOR MATERIAL (single/homogeneous):
        • Only ONE material family mentioned even if product form varies (sheet, panel, board, profile)
        • Raw material profiles, sheets, boards from one substance
        • Individual glass panes (float, laminated, toughened, safety glass) - NOT multi-pane assemblies
        • Pure insulation products from one material (PU foam, EPS, XPS, mineral wool, hemp, etc.)
        • Metal profiles, sheets, tubes (aluminum, steel) even if shaped/formed

        CLASSIFY AS MATERIAL (not component):
        • Steel beams, columns, profiles (single material, even if "structural element")
        • Aluminum profiles, sheets, extrusions (single metal - NOT window fittings unless hardware)
        • Concrete panels, blocks, precast elements (unless with DIFFERENT insulation core)
        • Single glass panes (monolithic, laminated, toughened, safety glass - NOT multi-pane IGU)
        • Metal roofing sheets, cladding panels (single material)
        • Insulation boards from ONE material (EPS, XPS, PU, PIR, mineral wool, wood fiber, hemp)
        • Precast concrete (reinforcement is integral, not a separate material layer)
        • PVC profiles, pipes, sheets (single polymer)

        CLASSIFY AS COMPONENT:
        • Window/door units with frame + glazing + hardware
        • Sandwich panels with metal facings + foam/wool core (DIFFERENT materials)
        • Insulation boards "with aluminium/metal facing" or "with reinforced facing"
        • Ceiling systems with tiles + suspension grid
        • ETICS/WDVS systems (insulation + adhesive + mesh + render)
        • IGUs (multi-pane glazing with spacers and gas fill)
        • Masonry units with integrated insulation fill

        NAMING TRAPS - these words ALONE do NOT make it a component:
        "unit", "system", "module", "device", "structure", "block", "frame", "element", "panel"
        Always check if multiple DISTINCT material families are combined.
        """
    ).strip()


def material_type_guide() -> str:
    """Detailed material type decision rules with keywords and boundary clarifications."""
    return dedent(
        """
        MATERIAL TYPE DECISION RULES (apply top-down, choose ONE):

        1) wood → Organic, lignocellulosic wood-based materials from trees.
           Keywords (EN): wood, timber, lumber, parquet, plywood, veneer, LVL, glulam, CLT, OSB, MDF, HDF, 
                          particleboard, chipboard, fiberboard, wood fiber, wood wool, cellulose (wood-based)
           Keywords (DE): Holz, Brettschichtholz, Brettsperrholz, Sperrholz, Furnierschichtholz, Spanplatte, 
                          Faserplatte, MDF, HDF, OSB, Holzfaser, Holzwolle, Zellulose
           Keywords (FR): bois, contreplaqué, panneau, CLT, OSB, MDF
           NOTE: "Cellulose" insulation from recycled paper/wood pulp → 'wood'

        2) biobased → Bio-based materials NOT derived from wood (non-wood plant/animal fibers).
           CRITICAL: If product name contains ANY of these keywords → classify as 'biobased', NOT 'unknown':
           Keywords (EN): hemp, flax, linen, jute, cotton, sheep wool, straw, cork, bamboo, coconut, sisal, coir
           Keywords (DE): Hanf, Flachs, Jute, Baumwolle, Schafwolle, Stroh, Kork, Bambus, Kokos, Sisal, 
                          Thermo-Hanf, Thermohanf, Naturfaser
           Keywords (FR): chanvre, lin, jute, coton, laine de mouton, paille, liège, bambou, coco
           Product names like "Thermo Hemp", "Hemp insulation", "Sheep wool", "Cork board" → 'biobased'

        3) concrete → Products where CEMENT (Portland, blended, alkali-activated) is the PRIMARY binder.
           INCLUDES aerated/cellular concrete products:
           Keywords: concrete, reinforced concrete, RC, UHPC, cement mortar, cement screed, cement board, 
                     fiber-reinforced concrete, precast concrete, Beton, béton, aerated concrete, 
                     autoclaved aerated concrete, AAC, cellular concrete, Porenbeton, Gasbeton, Ytong, Hebel, 
                     foamed concrete, lightweight concrete
           NOTE: Lime plaster, gypsum products, calcium silicate → classify as 'mineral' (not concrete)

        4) mineral → Inorganic, nonmetallic, ceramic/stone/glass products WITHOUT cement as primary binder.
           Includes: lime-based products, gypsum, calcium silicate, natural stone, ceramics, glass.
           Keywords: plaster, plasterboard, gypsum board, lime, calcium silicate, brick, tile, ceramic, glass, 
                     stone, granite, marble, slate, sand, gravel, mineral wool, glass wool, rock wool, 
                     foam glass, perlite, vermiculite, aerogel, calcium sulfate
           Keywords (DE): Gips, Kalk, Kalksandstein, Ziegel, Fliese, Keramik, Glas, Stein, Mineralwolle, Glaswolle
           Keywords (FR): plâtre, chaux, brique, carreau, céramique, verre, pierre, laine minérale
           NOTE: Pure cement powder/paste without aggregate → 'mineral' (cement as raw material)

        5) metallic → Metals and alloys.
           Keywords: steel, stainless steel, aluminum, aluminium, copper, zinc, lead, brass, bronze, 
                     cast iron, iron, Stahl, Aluminium, Kupfer, Zink, acier, aluminium, cuivre
           SPELLING: Use American spelling 'aluminum' in output (enum value).

        6) polymeric → Synthetic organic polymers, plastics, rubbers, resins, foams (single polymer family).
           Keywords: PVC, PE, PP, PET, PUR, PIR, PU, EPDM, acrylic, polyester, polyamide, nylon, EPS, XPS, 
                     polystyrene, polyurethane, silicone, rubber, epoxy, resin, Kunststoff, plastique, Harz
           IMPORTANT: Pure resins (epoxy, polyester, acrylic resin) WITHOUT fiber reinforcement → 'polymeric'
           Only classify as 'composite' if EXPLICITLY combined with glass/carbon/basalt fibers.
           SPELLING TRAP: "polyester" ≠ "polyethylene" — check carefully!

        7) bituminous → Hydrocarbon binders and composites.
           Keywords: asphalt, bitumen, tar, bituminous membrane, Asphalt, Bitumen, bitume, asphalte

        8) composite → Engineered combination of TWO+ distinct material families.
           Use 'composite' ONLY when:
           - EXPLICITLY fiber-reinforced with fibers from DIFFERENT material family
           - Product name contains: GFRP, CFRP, GFK, CFK, fiber-cement, fibre-cement, WPC,
             "glass fiber reinforced", "carbon fiber reinforced", "basalt fiber reinforced"
           - Wood-plastic composites (WPC), wood-cement composites
           NOTE: Reinforced concrete is 'concrete' (steel reinforcement is integral)
           NOTE: Pure polymers/resins WITHOUT explicit fiber reinforcement → 'polymeric', NOT 'composite'

        9) unknown → ONLY if none of the above can be determined from available text.
           Avoid 'unknown' if ANY recognizable material keyword is present.

        BOUNDARY CLARIFICATIONS:
        • CONCRETE vs MINERAL: 'concrete' if cement-bonded aggregate or aerated cement product.
          Lime plaster, gypsum board, calcium silicate, pure cement powder → 'mineral'
        • COMPOSITE vs POLYMERIC: 'composite' ONLY if explicitly fiber-reinforced.
          Pure polymers, foams, resins (EPS, XPS, PVC, epoxy resin) → 'polymeric'
        • WOOD vs BIOBASED: 'wood' for tree-derived materials. 'biobased' for other plant/animal fibers.
        • Ignore surface coatings (laminates, varnish, paint) when determining the base material.
        • Always classify based on the dominant material by mass/volume or by explicit naming.
        """
    ).strip()


def component_type_guide() -> str:
    """Detailed component type decision rules with key distinctions and disambiguation."""
    return dedent(
        """
        COMPONENT TYPE DECISION RULES (choose ONE):
        IMPORTANT: Only use these categories if the product is already classified as COMPONENT (entry_type).
        Raw materials (single material products) should NOT reach this classification.

        - window: Complete window assembly with frame + glazing + hardware, operating as a functional unit.
          Must include BOTH frame and glazing elements described together.
          Keywords: window unit, window system, Fenster, fenêtre, window assembly
          NOT: raw aluminum/PVC profiles (those are materials), not window fittings

        - infill: ASSEMBLED glazing products designed for openings - multi-pane/multi-layer glass units.
          ONLY includes assembled glass products:
            • IGU (insulating glass unit) with spacers and gas fill
            • Double/triple glazing assemblies
            • Glass blocks (assembled units)
          DOES NOT INCLUDE (these are MATERIALS, not infill):
            • Single glass panes (float, laminated, toughened, safety glass)
            • Individual glass sheets/panels
          Keywords: IGU, insulating glass, double glazing, triple glazing, Isolierglas, vitrage isolant

        - insulation_element: Multi-material thermal/acoustic products with DISTINCT material layers.
          MUST combine multiple DIFFERENT material families:
            • Sandwich panels with metal facings + foam/wool core
            • ETICS/WDVS systems (insulation + mesh + render)
            • Masonry units with integrated insulation fill
            • Insulation boards "with aluminium facing" or "with reinforced facing"
          Keywords: sandwich panel, ETICS, WDVS, composite insulation, Sandwichpaneel,
                   "with aluminium facing", "with metal facing", "multi-layer"
          NOT: Single-material insulation boards (EPS, XPS, mineral wool, PU foam) - those are materials

        - door: Complete door assembly with frame + leaf/panel + hardware.
          Keywords: door unit, door system, Tür, porte, door assembly

        - curtain_wall: Complete facade system with framing + infill panels as integrated assembly.
          Must be described as a complete facade/curtain wall system.
          Keywords: curtain wall, facade system, Vorhangfassade, mur-rideau, Fassadensystem
          NOT: individual facade profiles or panels (those are materials)

        - roof: Pre-assembled roof system or module with multiple components.
          Keywords: roof system, roofing assembly, Dachsystem

        - ceiling: Suspended ceiling system with grid + tiles/panels, OR acoustic ceiling panels.
          Keywords: ceiling system, suspended ceiling, Deckenverkleidung, plafond suspendu,
                   acoustic ceiling, Akustikdecke, ceiling tile system

        - shading_device: External/internal shading systems.
          Keywords: blinds, louvers, shutters, awning, Jalousie, Sonnenschutz, store

        - building_services: MEP equipment and systems.
          Keywords: HVAC, lighting, solar panel, heat pump, ventilation

        - stairs: Pre-fabricated stair system.

        - railing: Balustrade or guard rail system.

        - conveyor: Elevator or escalator system.

        - window_fitting: ONLY hardware and accessories for windows/doors.
          ONLY includes:
            • Handles, hinges, locks, latches
            • Seals, gaskets, weatherstripping
            • Window/door hardware sets
          DOES NOT INCLUDE (these are MATERIALS):
            • Aluminum profiles, extrusions
            • PVC profiles
            • Steel sections
            • Raw metal sheets/tubes
          Keywords: handle, hinge, lock, seal, gasket, fitting, hardware, Beschlag, Griff

        KEY DISTINCTIONS:
        • infill = ASSEMBLED glazing (IGU, multi-pane) - NOT single glass panes
        • insulation_element = multi-MATERIAL-FAMILY thermal product - NOT single-material insulation
        • window_fitting = HARDWARE ONLY - NOT raw profiles or materials
        • curtain_wall = complete facade SYSTEM - NOT individual facade panels
        • Single glass panes, metal profiles, pure insulation boards → classify as MATERIAL first!
        """
    ).strip()


def _enum_list(enum_cls) -> str:
    return ", ".join(v.value for v in enum_cls)


def level3_catalog() -> str:
    """Structured catalog of level3 options with disambiguation rules from facet definitions."""
    lines = [
        "LEVEL3 VALUES AND DISAMBIGUATION RULES:",
        "",
        "=== MATERIAL LEVEL3 ===",
        "",
        f"wood → {_enum_list(WoodType)}",
        "  DISAMBIGUATION:",
        "  • glue_laminated_timber (Glulam): laminations bonded in THICKNESS direction for beams/columns.",
        "    Keywords: 'glulam', 'Brettschichtholz', 'BSH', 'GL24', 'GL28', 'GL32'",
        "  • finger_jointed_structural_timber: solid timber joined END-TO-END with finger joints to extend LENGTH.",
        "    Keywords: 'finger jointed', 'KVH', 'Keilgezinktes Vollholz', 'length-jointed'",
        "  • cross_laminated_timber (CLT): layers stacked with ALTERNATING grain directions, forming panels.",
        "    Keywords: 'CLT', 'Brettsperrholz', 'BSP', 'X-Lam', '3-Schicht-Platte', '5-Schicht-Platte'",
        "  • laminated_veneer_lumber (LVL): thin veneers (2-4mm) glued with parallel grain.",
        "    Keywords: 'LVL', 'Furnierschichtholz'",
        "  • plywood: cross-laminated VENEERS (thin sheets, alternating grain)",
        "  • oriented_strand_board: OSB, oriented wood strands bonded with resin",
        "  • particleboard: wood particles bonded with resin (Spanplatte)",
        "  • medium_density_fiberboard: MDF, fine wood fibers",
        "  • wood_fibre: rigid or flexible wood fiber insulation boards",
        "  • wood_wool: mineral-bonded wood wool boards (Heraklith-type)",
        "  • cellulose: loose-fill or blown cellulose insulation from recycled paper/wood pulp",
        "  • natural_softwood: solid softwood (spruce, pine, fir, larch)",
        "  • natural_hardwood: solid hardwood (oak, beech, ash, birch)",
        "",
        f"biobased → {_enum_list(BiobasedType)}",
        "  Use specific type when material clearly matches: cotton, cork, flax, hemp, sheep_wool, straw",
        "  Use 'other' if bio-based but doesn't fit specific categories",
        "",
        f"concrete → {_enum_list(ConcreteType)}",
        "  DISAMBIGUATION:",
        "  • aerated: Autoclave-cured cellular concrete (AAC). Air voids from chemical reaction.",
        "    Keywords: 'AAC', 'autoclaved', 'Ytong', 'Hebel', 'Porenbeton', 'cellular concrete'",
        "  • lightweight: Concrete with lightweight AGGREGATES (expanded clay, pumice). Voids in aggregates.",
        "    Keywords: 'lightweight aggregate', 'expanded clay', 'Liapor', 'pumice concrete'",
        "  • ready_mixed: Wet/fresh concrete from batching plant, delivered to site.",
        "    Keywords: 'ready-mix', 'fresh concrete', 'transport concrete'",
        "  • precast: Factory-manufactured concrete elements, cured before delivery.",
        "    Keywords: 'precast', 'prefabricated', 'factory-made'",
        "  • binder: Pure cement/binder WITHOUT aggregates (cement powder, paste). NOT concrete products.",
        "  • calcium_sulfate: Gypsum-based binders/screeds (anhydrite, gypsum screed)",
        "  • calcium_silicate: Sand-lime products (Kalksandstein)",
        "  • foamed_concrete: Mechanically foamed (not autoclaved), lower strength than AAC",
        "  If uncertain between aerated vs lightweight: 'autoclaved' or 'AAC' → aerated; aggregates → lightweight",
        "",
        f"mineral → {_enum_list(MineralType)}",
        "  INSULATION DISAMBIGUATION:",
        "  • rock_wool: Mineral fiber from basalt/volcanic rock. Keywords: 'rock wool', 'stone wool', 'Steinwolle'",
        "  • glass_wool: Mineral fiber from recycled glass/silica. Keywords: 'glass wool', 'fiberglass', 'Glaswolle'",
        "  • mineral_wool: GENERIC fallback only when rock vs glass is NOT specified",
        "  • foam_glass: Cellular/foamed glass with air pockets. Keywords: 'foam glass', 'cellular glass', 'Schaumglas'",
        "  • glass: Solid glass products (panes, fibers). NOT foamed. Use only for non-cellular glass.",
        "  Prefer rock_wool over mineral_wool when basalt/rock origin indicated.",
        "  Prefer foam_glass over glass when cellular structure mentioned.",
        "",
        f"metallic → {_enum_list(MetallicType)}",
        "  DISAMBIGUATION (most specific to most general):",
        "  • stainless_steel: Chromium ≥10.5%. Keywords: 'stainless', 'inox', 'rostfrei', '304', '316', '1.4301'",
        "  • low_alloy_steel: Weathering steel (Corten) or HSLA. Keywords: 'weathering', 'Corten', 'HSLA', 'S355', 'S460'",
        "  • carbon_steel: Standard/mild/structural steel. Use for generic 'steel', rebar. Keywords: 'steel', 'S235', 'S275'",
        "  • cast_iron: Cast or ductile iron. Keywords: 'cast iron', 'ductile iron', 'Gusseisen'",
        "  • aluminum: Use American spelling. All aluminum/aluminium products.",
        "  Coatings (galvanized, powder-coated) do NOT affect the metallic_type.",
        "  'Stainless steel door' → stainless_steel; generic 'steel door' → carbon_steel",
        "",
        f"polymeric → {_enum_list(PolymericType)}",
        "  DISAMBIGUATION:",
        "  • polyethylene: PE, HDPE, LDPE, LLDPE, UHMWPE. Includes PE films, pipes, membranes.",
        "  • polypropylene: PP. Includes PP pipes, geotextiles, fibers.",
        "  • polyester: PET, polyester fibers/resins. SPELLING TRAP: 'polyester' ≠ 'polyethylene'!",
        "  • expanded_polystyrene: EPS (white beaded foam)",
        "  • extruded_polystyrene: XPS (colored rigid foam boards)",
        "  • polyurethane: PUR/PU foams, coatings, adhesives",
        "  • polyisocyanurate: PIR (improved fire performance vs PUR)",
        "  • phenolic: Phenol-formaldehyde resins/foams. Keywords: 'phenolic', 'Bakelite'",
        "  • epoxy: Epoxy resins (adhesives, coatings, FRP matrix)",
        "  • resin: FALLBACK only when specific resin type cannot be determined. Prefer specific types.",
        "",
        f"bituminous → {_enum_list(BituminousType)}",
        "  • asphalt_mix: Bitumen + aggregate. • mastic_asphalt: High binder, voidless.",
        "  • polymer_modified_bitumen: SBS/APP modified. • bitumen_emulsion: Water-based.",
        "",
        f"composite → {_enum_list(CompositeType)}",
        "  DISAMBIGUATION:",
        "  • fiber_reinforced_polymer: FRP/GFRP/CFRP/BFRP. Polymer matrix + continuous fibers.",
        "    Keywords: 'FRP', 'GFRP', 'CFRP', 'glass fiber reinforced', 'carbon fiber reinforced', 'pultruded'",
        "  • fiber_cement_composite: Cement matrix + cellulose/synthetic fibers (Eternit-type).",
        "    Keywords: 'fiber cement', 'fibre cement', 'Faserzement', 'Eternit'",
        "  • wood_cement_composite: Wood particles/fibers bonded with cement.",
        "    Keywords: 'wood cement', 'CBPB', 'cement-bonded particleboard'",
        "  • wood_plastic_composite: WPC, wood particles in thermoplastic matrix.",
        "  • polymer_concrete: Polymer BINDER + mineral AGGREGATES. Polymer replaces cement.",
        "    Keywords: 'polymer concrete', 'resin concrete', 'epoxy concrete'",
        "  • particulate_filled_polymer: Polymer with mineral FILLERS (not coarse aggregates).",
        "  If aggregates (sand, gravel) bound by resin → polymer_concrete",
        "  If polymer contains fine mineral fillers → particulate_filled_polymer",
        "",
        "=== COMPONENT LEVEL3 ===",
        "",
        f"window → {_enum_list(FrameType)} (frame material)",
        "",
        f"door → {_enum_list(DoorType)} (frame/leaf material)",
        "  DISAMBIGUATION:",
        "  • stainless_steel: ONLY when 'stainless' explicitly mentioned. Keywords: 'stainless', 'inox', 'Edelstahl'",
        "  • steel: Standard carbon/mild steel doors. Use for generic 'steel door' or 'metal door' (if steel implied).",
        "  • aluminium: Note British spelling in enum. All aluminum/aluminium doors.",
        "",
        f"window_fitting → {_enum_list(WindowFittingType)} (hardware material)",
        "",
        "insulation_element → sandwich_panel, sandwich_board, masonry_unit_with_infill, layered_bonded, etics, other, unknown",
        "  DISAMBIGUATION:",
        "  • sandwich_panel: Factory-made STRUCTURAL panels, metal facings BOTH sides + insulating core. Self-supporting.",
        "    Keywords: 'sandwich panel', 'Sandwichelement', 'PIR panel', 'PUR panel', 'metal-faced panel'",
        "  • sandwich_board: NON-STRUCTURAL multilayer boards. Smaller format, interior finishing.",
        "    Facings may be gypsum, MDF, cement board. Keywords: 'insulation board with facing', 'thermal board'",
        "  • layered_bonded: Multiple insulation layers BONDED together without distinct structural facings.",
        "  • masonry_unit_with_infill: Blocks/bricks with integrated insulating infill in cavities.",
        "  • etics: External Thermal Insulation Composite System (insulation + adhesive + mesh + render).",
        "    Keywords: 'ETICS', 'EIFS', 'WDVS'",
        "  Metal facings + structural → sandwich_panel; Non-metal + non-structural → sandwich_board",
        "",
        "curtain_wall → aluminium, steel, stainless_steel, wood, wood_aluminium, pvc, glass, composite_other, other, unknown",
        "",
        "shading_device → aluminium, steel, stainless_steel, wood, fabric, plastic, other, unknown",
        "",
        "roof → green_roof, flat_roof, pitched_roof, other, unknown",
        "",
        "railing → aluminium, steel, stainless_steel, glass, wood, other, unknown",
        "",
        "infill → transparent, opaque, translucent, unknown",
        "",
        "ceiling → gypsum_board, mineral_fiber_tile, metal_panel, wood_panel, fabric_panel, other, unknown",
        "",
        "stairs → straight, quarter_turn, half_turn, spiral, winder, other, unknown",
        "",
        "building_services → pv_panels, heat_generation, ventilation, lighting, sanitary, electrical, other, unknown",
        "",
        "conveyor → elevator, escalator, other, unknown",
    ]
    return "\n".join(lines)


def type_prompt() -> str:
    """Return the consolidated instruction used by the one-shot classifier."""
    material_values = ", ".join(mt.value for mt in MaterialType)
    component_values = ", ".join(ct.value for ct in ComponentType)

    return dedent(
        f"""
        You are an expert classifier for building materials/components.
        Classify in ONE step using the provided text only. Do not invent facts not present.

        === STEP 1: DETERMINE ENTRY_TYPE ===
        Allowed entry_type: material, component, unknown.

        {entry_type_guide()}

        === STEP 2: DETERMINE TYPE AND LEVEL3 ===

        Material types: {material_values}
        {material_type_guide()}

        Component types: {component_values}
        {component_type_guide()}

        === LEVEL3 REFERENCE ===
        {level3_catalog()}

        === OUTPUT FORMAT ===
        level3_value is REQUIRED (never null). Pick the closest subtype from the hints above; if truly unclear, use "unknown".

        Output JSON only, no prose:
        {{
          "entry_type": "<material|component|unknown>",
          "material_type": "<one of material types or null>",
          "component_type": "<one of component types or null>",
          "level3_value": "<subtype or unknown>"
        }}

        RULES:
        - If entry_type == material, set component_type to null and choose exactly one material_type and its level3_value.
        - If entry_type == component, set material_type to null and choose exactly one component_type and its level3_value.
        - If entry_type == unknown, set both material_type and component_type to "unknown" and level3_value to "unknown".
        - Use lowercase snake_case values only. Never add extra fields.
        """
    ).strip()
