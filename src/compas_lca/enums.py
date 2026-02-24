from enum import Enum

"""Enums for various categorical fields used in the extraction BaseModel classes."""

# -------------------------------------- 
# -------- INDICATOR ENUMS -------------
# -------------------------------------- 
class RefUnit(str, Enum):
    kg = "kg"
    m = "m"
    m2 = "m2"
    m3 = "m3"
    pcs = "pcs"
# -------------------------------------- 
# -------- QUANTITY ENUMS -------------
# -------------------------------------- 
class QuantUnit(str, Enum):
    m = "m"
    m2 = "m2"
    m3 = "m3"
class QuantName(str, Enum):
    volume = "volume"
    area = "area"
    length = "length"
    thickness = "thickness"

# -------------------------------------- 
# ----------- COMMON ENUMS -------------
# -------------------------------------- 
class EntryType(str, Enum):
    material = "material"
    component = "component"
    unknown = "unknown"
class Loadbearing(str, Enum):
    loadbearing = "loadbearing"
    non_loadbearing = "non_loadbearing"
    either = "either"
    unknown = "unknown"
class InteriorExterior(str, Enum):
    interior = "interior"
    exterior = "exterior"
    either = "either"
# -------------------------------------- 
# ----------- MATERIAL ENUMS ----------- 
# -------------------------------------- 
class MaterialType(str, Enum):
    mineral = "mineral"             # includes ceramic, stone, glass, etc.
    concrete = "concrete"           # explicit STAND-ALONE class for concrete (not mineral)
    wood = "wood"
    biobased = "biobased"
    metallic = "metallic"           # steel, aluminum, copper
    polymeric = "polymeric"         # plastics, rubbers, foams, resins
    bituminous = "bituminous"       # asphalt, bitumen membranes, tar
    composite = "composite"         # FRP, sandwich panels, fiber cement
    unknown = "unknown"
class ApplicationAreas(str, Enum):
    # ───────────────────────────────
    # Superstructure elements
    beam = "beam"
    column = "column"
    slab = "slab"
    wall = "wall"
    core_shaft = "core_shaft"                   # lift/stair cores, shafts
    roof = "roof"
    ceiling = "ceiling"
    stair = "stair"
    ramp = "ramp"
    balcony_terrace = "balcony_terrace"
    parapet = "parapet"
    railing = "railing"
    # ───────────────────────────────
    # Substructure / ground-contact
    foundation = "foundation"                   # strip, raft, pad
    footing = "footing"
    pile = "pile"
    retaining = "retaining"
    subgrade = "subgrade"                       # below-grade faces, basement walls
    # ───────────────────────────────
    # Envelope / surface layers
    facade = "facade"
    floor = "floor"
    pavement = "pavement"                       # exterior walking/driving surfaces, plaza
    plate = "plate"                             # optional dataset term
    window = "window"
    door = "door"
    # ───────────────────────────────
    # MEP systems
    hvac = "hvac"                               # ducts, air handling, ventilation units
    piping = "piping"                           # water, drainage, heating/cooling circuits
    electrical = "electrical"                   # cables, conduits, panels, lighting systems
    plumbing = "plumbing"                       # fixtures, water supply and waste elements
    fire_protection_device = "fire_protection_device"    # sprinklers, risers, detection systems
    equipment = "equipment"                     # mechanical/electrical devices, packaged systems
    service_system = "service_system"           # generic category for MEP when detailed type is unknown
    # ───────────────────────────────
    # Fallbacks
    other = "other"
    unknown = "unknown"

class FunctionalTypes(str, Enum):
    # Load-bearing & force transfer
    structural = "structural"                       # Primary load-bearing elements (concrete, steel sections, CLT, masonry units)
    reinforcement = "reinforcement"                 # Rebar, mesh, fibers, tendons, FRP sheets/plates
    stud_layer = "stud_layer"
    # insulation
    insulation = "insulation"
    #partition
    partition = "partition"
    # Finish / surface-related
    framing = "framing"                             # profiles that hold infill together, frames
    covering = "covering"                           # Discrete or roll-applied decorative or protective finish layer
    cladding = "cladding"                           # Exterior covering that forms the outer protective and/or decorative face of an element.
    lining = "lining"                               # Interior covering that forms the visible or finished face on the inside of an element.
    coating = "coating"                             # Thin film or liquid-applied finish providing color, protection, or seal (paint, varnish, sealer).
    plaster = "plaster"                             # Paste-like, trowel-applied layer forming a continuous smooth surface. Can be interior or exterior.
    render = "render"                               # Exterior plaster specifically formulated for façades. Weather-resistant but not necessarily waterproof.
    screed = "screed"                               # Thick, trowelled, or poured layer applied to floors as a base for coverings or as a level surface.
    membrane = "membrane"                           # Continuous thin sheet or film providing barrier or control function (e.g., waterproofing, vapor barrier).
    # Transparent / translucent
    glazing = "glazing"                             # IGUs, panes, laminated glass, polycarbonate sheets (primary function: transparent barrier)
    # Air
    air = "air"
    # Safety & protection (non-fire)
    safety = "safety"                               # Guardrails, safety glazing film (non-structural safety), anti-slip tapes, impact protection
    fire_protection = "fire_protection"
    waterproofing = "waterproofing"
    # Joints & connections
    fastener = "fastener"
    # Groundworks / civil
    piping = "piping"
    geosynthetic = "geosynthetic"                   # Geotextiles, geomembranes (non-waterproofing), geogrids, GCLs for soil functions
    paving_surfacing = "paving_surfacing"           # Asphalt, pavers, surface courses for roads/plazas (finish wearing course)
    # Bonding / shaping / substrate layers
    binder = "binder"                               # Cements, limes
    adhesive = "adhesive"                           # Holds materials together (glue, resins, epoxies, paste)
    mortar = "mortar"                               # Masonry mortar, tile mortar
    grout = "grout"                                 # Often used to fill gaps or to reinforce existing structures
    sealant = "sealant"                             # Blocks passage of fluids through openings in materials
    # Fallbacks
    other = "other"
    unknown = "unknown"


# -------------------------------------- 
# ----------- INSULATION ENUMS --------- 
# -------------------------------------- 
# awkward to have this in "MaterialCommon", but this is the only way to make it as efficient and precise as possible
# distinction between different insulation types is crucial for precise matching. Also, building level LCAs have proven
# that insulation is consitently in the top 3 functional types for highest emissions, and highest sensitivity. therefore
# it is very impactful in terms of LCA results and hence should be used within the 

class InsulationInfo(str, Enum):
    thermal = "thermal"              # thermal resistance / λ/R/U context
    acoustic = "acoustic"            # airborne sound absorption/insulation
    impact_sound = "impact_sound"
    rigid = "rigid"                 # EPS, XPS, PUR/PIR, phenolic, foamed glass, etc.
    semi_rigid = "semi_rigid"       # mineral wool slabs, wood fiber boards (semi-rigid)
    flexible_roll_batt = "flexible_roll_batt"  # rolls/batts (glass/stone wool, natural fibers
    loose_fill = "loose_fill"            # cellulose, perlite, vermiculite, granulates
    spray_foam = "spray_foam"             # site-applied PUR/PIR, Icynene-type
    other = "other"


# -------------------------------------- 
# ----------- CONCRETE ENUMS ----------- 
# -------------------------------------- 

class ConcreteType(str, Enum):
    ready_mixed = "ready_mixed"
    precast = "precast"
    cementitious_screed = "cementitious_screed"
    self_compacting = "self_compacting"
    lightweight = "lightweight"
    aerated = "aerated"
    binder = "binder"
    calcium_silicate = "calcium_silicate"
    calcium_sulfate = "calcium_sulfate"
    printed_concrete = "printed_concrete"
    foamed_concrete = "foamed_concrete"
    other = "other"
    unknown = "unknown"
class ConcreteForm(str, Enum):
    # In-situ (cast on site)
    amorphous = "amorphous"               # the "default" bulk form
    # Precast shapes / units
    panel = "panel"                       # walls, façades (precast, calcium silicate)
    slab = "slab"                         # floors, decks (precast, ready-mixed)
    beam = "beam"                         # structural members (precast)
    column = "column"                     # vertical supports (precast, ready-mixed)
    masonry_unit = "masonry_unit"         # masonry (aerated, foamed, calcium silicate)
    tile = "tile"                         # smaller surface units (aerated, lightweight)
    generic_element = "generic_element"   # generic for precast elements, pavers, etc.
    # Insulating / specialized forms
    board = "board"                       # insulation board (aerated, calcium silicate, foamed)
    fill = "fill"                         # lightweight/foamed fill applications
    spray = "spray"                       # sprayed / shotcrete (ready-mixed, lightweight)
    printed = "printed"                   # additive manufacturing (printed_concrete)
    # Other / fallback
    other = "other"
class BinderType(str, Enum):
    portland_cement = "portland_cement"
    blended_cement = "blended_cement"
    lime = "lime"
    gypsum = "gypsum"
    geopolymer_activated = "geopolymer_activated"
    alkali_activated = "alkali_activated"
    polymer_modified = "polymer_modified"
    resin_bound = "resin_bound"
    other = "other"

# ----------------------------------------
# ----------- METALLIC ENUMS -------------
# ----------------------------------------

class MetallicType(str, Enum):
    # Ferrous
    carbon_steel = "carbon_steel"          # mild, rebar, structural
    low_alloy_steel = "low_alloy_steel"    # weathering or high-strength steels
    stainless_steel = "stainless_steel"    # corrosion-resistant components
    cast_iron = "iron"                          # drainage, heritage structures
    # Non-ferrous
    aluminum = "aluminum"                  # façades, frames, sheets
    copper = "copper"                      # roofs, wiring, decorative
    brass = "brass"                        # fittings, architectural details
    bronze = "bronze"                      # sculptures, ornaments
    zinc = "zinc"                          # cladding, roofing
    lead = "lead"                          # flashing, legacy applications
    # fallback
    other = "other"
    unknown = "unknown"
class MetallicProduction(str, Enum):
    # Primary (ore-based) routes
    ore_bf_bof = "ore_bf_bof"                               # Blast furnace → basic oxygen (steel)
    ore_dri_eaf = "ore_dri_eaf"                             # Direct reduced iron → EAF (steel)
    ore_pyromet_smelting = "ore_pyromet_smelting"           # Smelting from sulfide/oxide ores (Cu, Pb, Ni)
    ore_hydromet_leaching = "ore_hydromet_leaching"         # Leach + solvent extraction/precipitation (Cu, Zn)
    # Secondary (recycled/scrap-based) routes
    scrap_eaf = "scrap_eaf"                       # Steel from scrap in EAF
    scrap_induction = "scrap_induction"           # Ferrous castings/steel remelt in induction
    scrap_cupola = "scrap_cupola"                 # Cast iron/cupola furnace route
    scrap_remelt = "scrap_remelt"                 # Non-ferrous remelt (Al, Cu alloys, Zn, Pb)
    # Fallbacks
    other = "other"
class MetallicForming(str, Enum):
    cast = "cast"                          # shaped by pouring molten metal into a mold
    forged = "forged"                      # plastically deformed by hammering or pressing
    rolled = "rolled"                      # formed by passing between rollers (hot or cold)
    extruded = "extruded"                  # forced through a die to create profiles or tubes
    drawn = "drawn"                        # reduced in cross-section by pulling through a die (wire, tube)
    deep_drawn = "deep_drawn"              # sheet metal drawn into hollow shapes (cups, shells)
    spun = "spun"                          # metal disk formed over a mandrel by spinning
    powder_metallurgy = "powder_metallurgy" # compacted and sintered from metallic powders
    additive = "additive"                  # built layer-by-layer via 3D printing or similar processes
    wrought = "wrought"                    # mechanically worked metal (generic term for shaped, non-cast products)
    other = "other"
class MetallicForm(str, Enum):
    sheet = "sheet"                      # thin flat rolled, typically <3 mm
    plate = "plate"                      # thick flat rolled (>3 mm)
    foil = "foil"                        # very thin sheet (<0.2 mm)
    coil = "coil"                        # continuous rolled strip wound in coils]
    profile = "profile"                  # extruded or rolled shape (I-beam, angle, channel) / stud
    bar = "bar"                          # solid long product, square or rectangular section
    grating = "grating"
    rod = "rod"                          # round long product, smaller diameter than bar
    wire = "wire"                        # drawn long product, very small diameter
    tube = "tube"                        # hollow cylindrical or prismatic section (includes pipe)
    mesh = "mesh"                        # woven or welded metallic net
    rebar = "rebar"                      # ribbed/deformed reinforcing bar for concrete
    billet = "billet"                    # semi-finished cast form before rolling or extrusion
    ingot = "ingot"                      # cast form for remelting/rolling
    casting = "casting"                  # final cast component (drain cover, fitting, etc.)
    forging = "forging"                  # shaped by hammering or pressing
    bolt = "bolt"
    screw = "screw"
    nail = "nail"
    rivet = "rivet"
    staple = "staple"
    anchor = "anchor"
    pin = "pin"
    other = "other"
    unknown = "unknown"
class MetallicSurfaceTreatment(str, Enum):
    galvanized = "galvanized"             # zinc coating by hot-dip or electroplating
    aluzinc = "aluzinc"                   # aluminum-zinc alloy coating (e.g., Galvalume)
    sherardized = "sherardized"           # diffusion zinc coating (thermal process)
    electroplated = "electroplated"       # generic electroplated coating (nickel, chrome, etc.)
    tin_plated = "tin_plated"             # tin plating for corrosion protection or solderability
    nickel_plated = "nickel_plated"       # nickel plating for protection or appearance
    anodized = "anodized"                 # anodic oxide layer, mainly on aluminum
    alodined = "alodined"                 # chromate conversion coating, mainly for aluminum
    painted = "painted"                   # liquid paint system
    powder_coated = "powder_coated"       # electrostatically applied dry powder coating
    epoxy_coated = "epoxy_coated"         # epoxy-based coating (often for rebar)
    polished = "polished"                 # mechanically polished surface
    mill = "mill"                         # as-rolled or as-extruded surface finish
    other = "other"


# ----------------------------------------
# ----------- Wood ENUMS -------------
# ----------------------------------------

class WoodType(str, Enum):
    # Natural (solid wood)
    natural_softwood = "natural_softwood"
    natural_hardwood = "natural_hardwood"

    # Modified wood
    modified_wood = "modified_wood"

    # Engineered / composite wood products
    finger_jointed_structural_timber = "finger_jointed_structural_timber"
    glue_laminated_timber = "glue_laminated_timber"           # glulam
    cross_laminated_timber = "cross_laminated_timber"         # CLT
    plywood = "plywood"
    laminated_veneer_lumber = "laminated_veneer_lumber"       # LVL
    oriented_strand_board = "oriented_strand_board"           # OSB
    particleboard = "particleboard"
    softboard = "softboard"
    medium_density_fiberboard = "medium_density_fiberboard"   # MDF
    high_density_fiberboard = "high_density_fiberboard"       # HDF
    hardboard = "hardboard"

    # Wood-based insulation
    cellulose = "cellulose"        # (wood-pulp based)
    wood_fibre = "wood_fibre"
    wood_wool = "wood_wool"

    # Fallbacks
    other = "other"
    unknown = "unknown"
class WoodForm(str, Enum):
    lumber = "lumber"
    beam = "beam"
    plank = "plank"
    board = "board"
    slab = "slab"
    panel = "panel"
    flooring = "flooring"
    mat = "mat"
    roll = "roll"
    loose_fill = "loose_fill"
    other = "other"
    unknown = "unknown"
class WoodProcessing(str, Enum):
    rough_sawn = "rough_sawn"
    planed_surfaced = "planed_surfaced"
    machine_graded = "machine_graded"
    finger_jointed = "finger_jointed"
    glued_panels = "glued_panels"
    other = "other"
class BaseSpecies(str, Enum):
    spruce = "spruce"
    pine = "pine"
    larch = "larch"
    fir = "fir"
    oak = "oak"
    birch = "birch"
    mixed = "mixed"
    other = "other"
class WoodAdhesive(str, Enum):
    UF = "UF"            # Urea-formaldehyde: interior, low moisture resistance; common in particleboard/MDF.
    MUF = "MUF"          # Melamine-urea-formaldehyde: improved moisture resistance; used in glulam and some plywood.
    PF = "PF"            # Phenol-formaldehyde: high durability and water resistance; typical for exterior plywood and LVL.
    pMDI = "pMDI"        # Polymeric MDI / PUR: formaldehyde-free, high-strength structural adhesive; standard for CLT.
    bio_based = "bio_based"  # Adhesives derived from natural sources (lignin, tannin, protein); niche/experimental products.
    other = "other"      # Any adhesive not fitting the above categories or unspecified adhesive systems.

class DryingMethod(str, Enum):
    fresh_green = "fresh_green"
    air_dried = "air_dried"
    kiln_dried = "kiln_dried"
    vacuum_dried = "vacuum_dried"
    solar_dried = "solar_dried"
    steam_conditioned = "steam_conditioned"
    other = "other"
class WoodSurface(str, Enum):
    oiled = "oiled"
    waxed = "waxed"
    varnished = "varnished"
    lacquered = "lacquered"
    painted = "painted"
    glazed = "glazed"
    impregnated = "impregnated"
    other = "other"
class ModificationMethod(str, Enum):
    thermally_modified = "thermally_modified"
    acetylated = "acetylated"
    other = "other"


# ----------------------------------------
# ----------- MINERAL ENUMS --------------
# ----------------------------------------

class MineralType(str, Enum):
    # Binders
    lime = "lime"
    gypsum = "gypsum"
    gypsum_lime = "gypsum_lime"
    cement = "cement"
    lime_cement = "lime_cement"
    # Earth & aggregates (raw minerals)
    clay = "clay"
    earth = "earth"
    sand = "sand"
    gravel = "gravel"
    silt = "silt"
    crushed_stone = "crushed_stone"
    # Natural stone / rock
    limestone = "limestone"
    sandstone = "sandstone"
    granite = "granite"
    marble = "marble"
    slate = "slate"
    basalt = "basalt"
    # Ceramics
    ceramic = "ceramic"
    # Industrial minerals / additives
    shale = "shale"
    pumice = "pumice"
    perlite = "perlite"
    vermiculite = "vermiculite"
    fly_ash = "fly_ash"
    slag = "slag"
    # Glass & wool / sand–lime
    glass = "glass"
    sand_lime_product = "sand_lime_product"
    # insulation
    aerogel = "aerogel"
    glass_wool = "glass_wool"
    foam_glass = "foam_glass"
    mineral_wool = "mineral_wool"
    rock_wool = "rock_wool"
    calcium_silicate = "calcium_silicate"
    silicum_dioxide = "silicum_dioxide"
    # fallbacks
    other = "other"
    unknown = "unknown"
class MineralForm(str, Enum):
    # Loose & powders
    powder = "powder"                      # dry, fine powder (cement, lime, gypsum, dry premix)
    granulate = "granulate"                # discrete grains/pellets (expanded perlite/vermiculite, foam-glass granules)
    aggregate = "aggregate"                # bulk granular material (sand, gravel, crushed stone); grading captured elsewhere
    paste_slurry = "paste_slurry"          # wet paste or slurry (ready-to-use mineral pastes, slurries)
    # Masonry & small units
    masonry_unit = "masonry_unit"
    paver_unit = "paver_unit"                    # paving stones/flags/curbs as discrete units (stone, fired, cast)
    tile = "tile"                                # thin plate units (ceramic/stone tiles for floor/wall/roof)
    # Boards, panels, panes
    board = "board"                             # flat sheet/panel/board (gypsum board, cement/fiber-cement board, stone panels)
    glass_pane = "glass_pane"     # monolithic flat glass (float, patterned, toughened); IGUs are considered components  
    plate = "plate"                             # thick natural-stone slab/plate (dimension stone, countertops, façade plates)
    # Insulation products
    batt = "batt"                          # semi-rigid mats (mineral wool/glass wool batts)
    blanket_roll = "blanket_roll"          # flexible rolls (glass/mineral wool blanket)
    loose_fill = "loose_fill"              # pour/blow-in granules/flakes (perlite, vermiculite, wool fibers)
    spray_applied_fiber = "spray_applied_fiber"  # sprayed/blown mineral fiber systems
    pipe_section = "pipe_section"          # pre-formed insulation shells/half-shells for pipes (wool or foam glass)
    # Cast/monolithic forms (non-unit)
    mass_cast = "mass_cast"                # cast/monolithic mineral product supplied/installed in place (e.g., cast stone, grout fills)
    # Fallbacks
    other = "other"


# ----------------------------------------
# ----------- POLYMER ENUMS --------------
# ----------------------------------------

class PolymericType(str, Enum):
    acrylic = "acrylic"                     # Glazing (acrylic glass), sealants, coatings, paints, adhesives
    epoxy = "epoxy"                         # Flooring, adhesives, coatings, FRP matrices (resin)
    expanded_polystyrene = "expanded_polystyrene" # EPS, Thermal insulation (boards, blocks, ICFs)
    extruded_polystyrene = "extruded_polystyrene" # XPS, rigid insulation boards
    polyamide = "polyamide"                 # Nylon, engineering thermoplastic
    polyethylene = "polyethylene"           # Membranes, vapor barriers, films, pipes, geomembranes
    polypropylene = "polypropylene"         # Geotextiles, pipes, fittings, fibers, films
    polyester = "polyester"                 # FRP matrices, coatings, fibers, insulation mats
    polyurethane = "polyurethane"           # PU, insulation, coatings, adhesives
    polyisocyanurate = "polyisocyanurate"   # PIR, Rigid insulation foams
    polyvinyl_chloride = "polyvinyl_chloride"   # PVC
    phenolic = "phenolic"                   # Rigid insulation foams, laminates
    polycarbonate = "polycarbonate"         # Transparent glazing panels, roofing sheets
    silicone = "silicone"                   # Sealants, adhesives, coatings
    rubber = "rubber"                       # Gaskets, membranes, flooring, sealants
    resin = "resin"                         # more a class, but is fallback if no type of resing specified
    aerogel = "aerogel"
    composite_polymer = "composite_polymer"
    other = "other"
    unknown = "unknown"
class PolymericForm(str, Enum):
    # sheet / film products
    sheet_membrane = "sheet_membrane"      # roll membranes, waterproofing sheets
    floor_roll = "floor_roll"              # resilient flooring rolls (vinyl)
    floor_tile = "floor_tile"              # modular flooring (LVT, rubber tile)
    fleece = "fleece"                      # geotextiles, reinforcement fabrics
    board = "board"                        # mostly for insulation
    # profiled / formed products
    profile_rigid = "profile_rigid"        # PVC/PE/PC extrusions, trims, gutters
    profile_flexible = "profile_flexible"  # flexible tubes, gaskets, joints
    tube = "tube"                          # pressure pipes
    fitting = "fitting"                    # pipe fittings, connectors
    # cellular / expanded forms
    foam = "foam"                          # insulation
    # liquid / paste / reactive forms
    liquid = "liquid"
    paste = "paste"
    tape = "tape"
    # fallback
    other = "other"

# ----------------------------------------
# ----------- BIOBASED ENUMS -----------
# ----------------------------------------
class BiobasedType(str, Enum):
    cotton = "cotton"
    cork = "cork"           # bark-based; not wood but bio-based
    flax = "flax"
    hemp = "hemp"
    sheep_wool = "sheep_wool"
    straw = "straw"
    other = "other"
    unknown = "unknown"


# ----------------------------------------
# ----------- BITUMINOUS ENUMS -----------
# ----------------------------------------

class BituminousType(str, Enum):
    asphalt_mix = "asphalt_mix"                      # hot/cold mix asphaltic concrete for paving
    mastic_asphalt = "mastic_asphalt"                  # high binder content, voidless mastic
    bitumen = "bitumen"                                # unmodified petroleum bitumen
    polymer_modified_bitumen = "polymer_modified_bitumen"  # e.g., SBS/APP modified
    bitumen_emulsion = "bitumen_emulsion"              # water-based emulsion (cationic/anionic)
    other = "other"
    unknown = "unknown"
class BituminousForm(str, Enum):
    sheet = "sheet"                        # rolled, preformed membranes (torch-on, self-adhesive)
    felt = "felt"                          # specific roofing felt product
    liquid= "liquid"                       # brush/spray/trowel coatings, mastics, primers
    shingle = "shingle"                    # discrete tile or shingle units
    paving_mix = "paving_mix"              # hot/cold asphaltic mixtures for surfacing
    tape = "tape"                          # narrow self-adhesive flashing strips
    board = "board"                        # rigid/semi-rigid bituminous protection/insulation boards
    other = "other"

# ---------------------------------------
# ----------- COMPOSITE ENUMS -----------
# ---------------------------------------

class CompositeType(str, Enum):
    # Cementitious-centric
    reinforced_concrete = "reinforced_concrete"         # conventional RC with steel rebar/mesh
    fiber_reinforced_concrete = "fiber_reinforced_concrete"  # steel, glass, PP, basalt, etc.
    polymer_modified_cementitious = "polymer_modified_cementitious"  # PMC/PCC
    polymer_concrete = "polymer_concrete"               # PC: resin binder + mineral filler/aggregate
    # Wood/cement & fiber/cement families
    wood_cement_composite = "wood_cement_composite"     # wood wool cement board, CBPB, etc.
    fiber_cement_composite = "fiber_cement_composite"   # “Eternit”-type sheets/boards
    # Polymer-based composites
    wood_plastic_composite = "wood_plastic_composite"   # WPC decking, profiles
    fiber_reinforced_polymer = "fiber_reinforced_polymer"  # FRP (GFRP, CFRP, BFRP)
    particulate_filled_polymer = "particulate_filled_polymer"
    laminated_polymeric_composite = "laminated_polymeric_composite"  # HPL, CPL, DPL, decorative laminates
    # Hybrid/other
    metal_polymer_composite = "metal_polymer_composite" # metal-filled polymers, MML without clear base
    linoleum = "linoleum"
    other = "other"
    unknown = "unknown"
class CompositeMatrix(str, Enum):
    cementitious = "cementitious"       # Portland/blended cement, etc.
    polymer_thermoset = "polymer_thermoset"   # epoxy, polyester, vinyl ester, phenolic
    polymer_thermoplastic = "polymer_thermoplastic"  # PE, PP, PVC, PA, etc.
    bituminous = "bituminous"           # asphalt/bitumen binders (rare in structural products but possible)
    metal = "metal"                     # for MMC-like hybrids or metal/adhesive hybrids
    ceramic = "ceramic"                 # high-temp ceramics (niche in buildings)
    mineral = "mineral"
    other = "other"
class CompositeReinforcement(str, Enum):
    steel_rebar = "steel_rebar"         # RC
    steel_fibers = "steel_fibers"       # FRC
    glass_fibers = "glass_fibers"       # GFRP or fiber-cement
    carbon_fibers = "carbon_fibers"     # CFRP
    basalt_fibers = "basalt_fibers"     # BFRP
    aramid_fibers = "aramid_fibers"     # AFRP (Kevlar)
    polypropylene_fibers = "polypropylene_fibers"   # PP fibers in FRC
    cellulose_fibers = "cellulose_fibers"           # fiber-cement and boards
    wood_particles = "wood_particles"   # WPC, CBPB variants
    mineral_aggregate = "mineral_aggregate" # quartz, limestone, etc. (acts as filler/aggregate in PC)
    metal_particles = "metal_particles" # metal-polymer composites
    fabric_glass = "fabric_glass"       # woven/stitched glass fabrics
    fabric_carbon = "fabric_carbon"     # woven/stitched carbon fabrics
    other = "other"
class CompositeArchitecture(str, Enum):
    monolithic = "monolithic"                 # single continuous matrix (incl. FRP laminates, PC without core)
    rebar_reinforced = "rebar_reinforced"     # RC (concrete + steel rebar/mesh)
    fiber_reinforced = "fiber_reinforced"     # fibers dispersed (FRC) or oriented (FRP)
    particulate_filled = "particulate_filled" # mineral aggregate, metal particles, etc. (e.g., polymer concrete)
    layered_bonded = "layered_bonded"         # multi-layer stackup bonded/laminated (backing insulation, etc.)
    other = "other"
class CompositeForm(str, Enum):
    # Flat goods / boards / sheets / panels
    sheet = "sheet"                     # thin flat product
    board = "board"                     # thicker flat product (fiber-cement, CBPB, WWCB)
    sandwich_panel = "sandwich_panel"   # explicit sandwich construction (skins + core)
    # Linear / profiles / rebar
    profile = "profile"                 # pultruded/extruded WPC/FRP shapes
    tube = "tube"                       # FRP tubes, polymer concrete pipes
    # Blocks / precast
    masonry_unit = "masonry_unit"                     # shuttering block, masonry-like unit
    precast_element = "precast_element" # beams, slabs, cladding elements
    # Repair/strengthening systems
    wrap = "wrap"                       # FRP wraps/laminates for retrofits
    other = "other"

# -----------------------------------------
# ----------- COMPONENT ENUMS -------------
# -----------------------------------------

class ComponentType(str, Enum):
    # Envelope components
    window = "window"
    window_fitting = "window_fitting"
    door = "door"
    curtain_wall = "curtain_wall"
    shading_device = "shading_device"
    roof = "roof"
    railing = "railing"
    infill = "infill"
    insulation_element = "insulation_element"
    # Interior components
    ceiling = "ceiling"
    stairs = "stairs"
    # Technical systems
    building_service = "building_services"
    conveyor = "conveyor"
    # Miscellaneous
    other = "other"
    unknown = "unknown"

# -----------------------------------------
# ----------- DOOR ENUMS ------------------
# -----------------------------------------

class DoorType(str, Enum):
    aluminium = "aluminium"
    steel = "steel"
    wood = "wood"
    wood_aluminium = "wood_aluminium"
    pvc = "pvc"
    polyurethane = "polyurethane"
    glass = "glass"
    mixed_composite = "mixed_composite"
    other = "other"
    unknown = "unknown"
class DoorOperation(str, Enum):
    swing_hinged = "swing_hinged"
    sliding = "sliding"
    folding = "folding"
    revolving = "revolving"
    sectional = "sectional"
    rolling_shutter = "rolling_shutter"
    up_and_over = "up_and_over"
    other = "other"
class SafetyFunction(str, Enum):
    fire_protection = "fire_protection"
    smoke_protection = "smoke_protection"
    high_speed_operation = "high_speed_operation"
    security_access_control = "security_access_control"
    other = "other"

# -----------------------------------------
# ----------- WINDOW ENUMS ----------------
# -----------------------------------------

class FrameType(str, Enum):
    aluminium = "aluminium"
    steel = "steel"
    stainless_steel = "stainless_steel"
    bronze = "bronze"
    pvc = "pvc"
    wood = "wood"
    wood_aluminium = "wood_aluminium"
    glass = "glass"
    composite_other = "composite_other"
    other = "other"
    unknown = "unknown"
class GlazingCount(str, Enum):
    single_glazing = "single_glazing"
    double_glazing = "double_glazing"
    triple_glazing = "triple_glazing"
    other = "other"
class WindowOperation(str, Enum):
    fixed = "fixed"
    skylight = "skylight"
    casement_side_hung = "casement_side_hung"
    tilt_turn = "tilt_turn"
    sliding = "sliding"
    lift_sliding = "lift_sliding"
    folding = "folding"
    other = "other"

# -------------------------------------------------
# ----------- WINDOW FITTING ENUMS ----------------
# -------------------------------------------------

class WindowFittingType(str, Enum):
    aluminium = "aluminium"
    brass = "brass"
    plastic = "plastic"
    steel = "steel"
    zinc = "zinc"
    other = "other"
    unknown = "unknown"


# -------------------------------------------------
# ----------- INFILL ENUMS ----------------
# -------------------------------------------------

class InfillType(str, Enum):
    transparent = "transparent"
    opaque = "opaque"
    translucent = "translucent"
    unknown = "unknown"
class InfillMaterialFamily(str, Enum):
    float_glass = "float_glass"          # standard soda-lime flat glass
    glass_ceramic = "glass_ceramic"      # MAGNA glass ceramic etc.
    other_glass = "other_glass"          # wired glass, patterned, special compositions
    plastic_glazing = "plastic_glazing"  # PMMA, polycarbonate, etc.
    other = "other"
    unknown = "unknown"
class InfillConstruction(str, Enum):
    monolithic = "monolithic"                    # single sheet / plate
    insulating_glass_unit = "insulating_glass_unit"  # IGU, double/triple
    laminated = "laminated"                      # laminated glass (PVB, etc.)
    laminated_igu = "laminated_insulating_unit" # IGU that includes laminated panes
    other = "other"
class InfillSafetyType(str, Enum):                             # no explicit safety function
    thermally_toughened = "thermally_toughened"  # toughened / tempered safety glass
    laminated_safety = "laminated_safety"        # laminated safety glass
    combined = "combined"                        # laminated + toughened panes
    other = "other"
class InfillCoating(str, Enum):
    uncoated = "uncoated"
    coated_generic = "coated_generic"            # coated, type not specified
    low_e = "low_e"                              # low-emissivity
    solar_control = "solar_control"
    other = "other"

# -------------------------------------------------
# ----------- SANDWICH ENUMS ----------------
# -------------------------------------------------

class InsulationElementType(str, Enum):
    layered_bonded = "layered_bonded"
    masonry_unit_with_infill = "masonry_unit_with_infill"
    etics = "etics"
    other = "other"
    unknown = "unknown"

class InsulationCore(str, Enum):
    polyurethane = "polyurethane"              # PUR / PIR
    polystyrene = "polystyrene"                # EPS / XPS
    mineral_wool = "mineral_wool"              # rock wool / glass wool
    cellulose_fibre = "cellulose_fibre"        # cellulose, recycled paper, loosefill core
    wood_fibre = "wood_fibre"                  # wood fibre insulation boards
    biofibre = "biofibre"                      # hemp, flax, jute, wool blends
    aerogel = "aerogel"                        # silica aerogel boards / plasters
    honeycomb = "honeycomb"                    # aluminium or polymer honeycomb
    other = "other"
    unknown = "unknown"

class InsulationFacing(str, Enum):
    steel = "steel"
    aluminium = "aluminium"
    clay = "clay"                           # clay for bricks
    concrete = "concrete"                   # concrete for precast panels/blocks
    frp = "frp"                                 # fiberglass reinforced plastic / GRP
    magnesium_oxide = "magnesium_oxide"         # MgO boards (SIPs, façade panels)
    cement_board = "cement_board"               # fibre-cement / cementitious skins
    plywood = "plywood"
    mdf = "mdf"                                 # medium density fibreboard
    wood_panel = "wood_panel"                   # generic OSB, HDF, composite wood skins
    gypsum_board = "gypsum_board"               # for ETICS and laminated interior boards
    particle_board = "particle_board"
    polymer_film = "polymer_film"               # aluminium-foil-faced or polymer-faced boards
    mineral_fleece = "mineral_fleece"   # MW mat facings on some panels
    other = "other"
    unknown = "unknown"

# -------------------------------------------------
# ----------- RAILING ENUMS ----------------
# -------------------------------------------------

class RailingType(str, Enum):
    balustrade = "balustrade"             # Traditional vertical posts (balusters) with a handrail
    glass_panel = "glass_panel"           # Framed or frameless glass infill panels
    cable = "cable"                       # Horizontal or vertical tensioned cables as infill
    perforated_panel = "perforated_panel" # Metal sheet or mesh infill (perforated, expanded, or wire mesh)
    guard_wall = "guard_wall"             # Solid parapet or low wall acting as a guardrail
    # optional fallbacks
    unknown = "unknown"


# ----------------------------------------
# ----------- STAIR ENUMS ----------------
# ----------------------------------------

class StairType(str, Enum):
    straight = "straight"                 # Single flight, no change in direction
    quarter_turn = "quarter_turn"         # Turns 90°, with or without landing (L-shaped)
    half_turn = "half_turn"               # 180° reversal (U-shaped), often with landing
    spiral = "spiral"                     # Circular/helix around a central post
    winder = "winder"                     # Turns with wedge-shaped treads instead of a landing
    # optional fallbacks
    other = "other"
    unknown = "unknown"

# -------------------------------------------------
# ----------- CURTAIN WALL ENUMS ------------------
# -------------------------------------------------

class CurtainWallType(str, Enum):
    aluminium = "aluminium"              # standard stick or unitized aluminium systems
    steel = "steel"                      # heavy-duty or fire-rated systems
    timber_aluminium = "timber_aluminium"  # hybrid systems with wood frame and aluminium cladding
    ceramic = "ceramic"                  # structural ceramic panels or rainscreens
    glass = "glass"                      # structural glazing or glass-fin systems
    composite = "composite"              # FRP, GFRP, or hybrid polymer-based frames
    other = "other"
    unknown = "unknown"
class CurtainWallForm(str, Enum):
    stick_construction = "stick_construction"     # frame built on site, infill glazed onsite
    unitized = "unitized"                         # factory-assembled panels installed as units
    semi_unitized = "semi_unitized"               # hybrid: partly factory-assembled
    panelized = "panelized"                       # modular panel façade systems
    structural_glazing = "structural_glazing"     # bonded glazing or point-fixed glass systems
    other = "other"

# ---------------------------------------------
# ----------- CONVEYOR ENUMS ------------------
# ---------------------------------------------

class ConveyorType(str, Enum):
    elevator = "elevator"
    escalator = "escalator"
    other = "other"
    unknown = "unknown"

# -----------------------------------------
# ----------- ROOF ENUMS ------------------
# -----------------------------------------

class RoofType(str, Enum):
    green_roof = "green_roof"
    flat_roof = "flat_roof"
    pitched_roof = "pitched_roof"
    other = "other"
    unknown = "unknown"


# ---------------------------------------------
# ----------- CEILING ENUMS ------------------
# ---------------------------------------------

class CeilingType(str, Enum):
    gypsum_board = "gypsum_board"                # Standard drywall or plasterboard ceiling
    mineral_fiber_tile = "mineral_fiber_tile"    # Typical lay-in acoustic tiles
    metal_panel = "metal_panel"                  # Aluminum, steel, or perforated metal ceiling systems
    wood_panel = "wood_panel"                    # Veneered or solid wood slats/panels
    fabric_panel = "fabric_panel"                # Textile-covered ceiling systems
    pvc_panel = "pvc_panel"                      # Vinyl or plastic ceiling systems
    cement_board = "cement_board"                # Cementitious board ceilings, often in wet areas
    concrete_slab = "concrete_slab"              # Exposed or painted structural concrete ceiling
    acoustic_fiberboard = "acoustic_fiberboard"  # Fiberboard with acoustic properties
    glass_panel = "glass_panel"                  # Translucent or transparent glass ceiling elements
    stretch_membrane = "stretch_membrane"        # Tensioned PVC or fabric membranes
    metal_mesh = "metal_mesh"                    # Open metal mesh or grid ceiling
    composite_panel = "composite_panel"          # Multi-material (e.g., aluminum-plastic composite) panels
    other = "other"                              # Fallback for rare or custom types
    unknown = "unknown"
class CeilingForm(str, Enum):
    suspended = "suspended"               # Hung below the structure, typically with a grid or framing system
    direct_applied = "direct_applied"     # Material fastened directly to structure (e.g., drywall on concrete slab)
    exposed_structure = "exposed_structure" # No separate ceiling; structure itself is visible and may be painted/finished
    stretch_membrane = "stretch_membrane" # Tensioned flexible membrane or film ceiling
    coffered = "coffered"                 # Ceiling with recessed panels or grid of beams
    vaulted = "vaulted"                   # Angled or arched ceiling following roof slope
    dropped_bulkhead = "dropped_bulkhead" # Partial lowered section (often for services or aesthetic zoning)
    integrated_panel = "integrated_panel" # Ceiling panels integrated with lighting/HVAC modules (monolithic systems)
    other = "other"                       # For rare or custom configurations

# --------------------------------------------
# ----------- SHADING DEVICE ENUMS  ----------
# --------------------------------------------

class ShadingDeviceType(str, Enum):
    external_fixed = "external_fixed"               # Fixed external elements (e.g., brise-soleil, fins)
    external_adjustable = "external_adjustable"     # Motorized or manually operable external louvers/shutters
    external_screen = "external_screen"             # Fabric or mesh screen mounted externally
    internal_blind = "internal_blind"               # Venetian, roller, or vertical blinds inside the glazing
    internal_screen = "internal_screen"             # Interior textile screen (manual or motorized)
    between_glazing = "between_glazing"             # Shading device integrated within double/triple glazing cavity
    overhang = "overhang"                           # Architectural fixed projection above openings
    pergola = "pergola"                             # Roof-mounted or free-standing shading frame system
    dynamic_facade = "dynamic_facade"               # Adaptive façade modules with integrated shading control
    curtain = "curtain"                             # Fabric curtain system used for shading or privacy
    other = "other"                                 # Catch-all for custom or uncommon shading products
    unknown = "unknown"
class ShadingDeviceMaterial(str, Enum):
    metal = "metal"
    wood = "wood"
    fabric = "fabric"
    glass = "glass"
    composite = "composite"
    other = "other"

# ----------------------------------------
# ----------- BUILDING SERVICES  ---------
# ----------------------------------------

class BuildingServiceType(str, Enum):
    pv_panels = "pv_panels"
    solar_thermal_panels = "solar_thermal_panels"
    heat_generation = "heat_generation"
    heat_distribution = "heat_distribution"
    heat_storage = "heat_storage"
    air_conditioning = "air_conditioning"
    ventilation = "ventilation"
    lighting = "lighting"
    sanitary = "sanitary"
    water_distribution = "water_distribution"
    electrical = "electrical"
    building_automation = "building_automation"
    fire_protection = "fire_protection"
    other = "other"
    unknown = "unknown"

