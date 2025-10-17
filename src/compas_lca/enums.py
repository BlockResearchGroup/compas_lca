from enum import Enum

"""Enums for various categorical fields used in the extraction BaseModel classes."""

# -------------------------------------- 
# ----------- COMMON ENUMS -------------
# -------------------------------------- 


class MaterialType(str, Enum):
    mineral = "mineral"             # includes ceramic, stone, glass, etc.
    concrete = "concrete"           # explicit STAND-ALONE class for concrete (not mineral)
    ligneous = "ligneous"           # timber, bamboo, MDF, KVH, cork
    metallic = "metallic"           # steel, aluminum, copper
    polymeric = "polymeric"         # plastics, rubbers, foams, resins
    bituminous = "bituminous"       # asphalt, bitumen membranes, tar
    composite = "composite"         # FRP, sandwich panels, fiber cement
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
    unknown = "unknown"
class ApplicationAreas(str, Enum):
    # Superstructure elements
    beam = "beam"
    column = "column"
    slab = "slab"
    wall = "wall"             # partitions, non-external walls
    core_shaft = "core_shaft"                   # lift/stair cores, shafts
    roof = "roof"
    ceiling = "ceiling"
    stair = "stair"
    ramp = "ramp"
    balcony_terrace = "balcony_terrace"         
    parapet = "parapet"
    railing = "railing"
    # Substructure / ground-contact
    foundation = "foundation"                   # strip, raft, pad
    footing = "footing"                         # keep if you need the granularity
    pile = "pile"
    retaining = "retaining"
    subgrade = "subgrade"                       # below-grade faces, basement walls
    # Envelope layers
    facade = "facade"                           # general façade area (if not distinguishing wall_external)
    floor = "floor"                             # general floor area (if not distinguishing slab/finish)
    # Horizontal surfaces / civil
    pavement = "pavement"                       # exterior walking/driving surfaces, plaza
    plate = "plate"                             # (OPTIONAL) only if your datasets use this term
    window = "window"
    door = "door"
    # Fallbacks
    other = "other"
    unknown = "unknown"
class FunctionalTypes(str, Enum):
    # Load-bearing & force transfer
    structural = "structural"                       # Primary load-bearing elements (concrete, steel sections, CLT, masonry units)
    reinforcement = "reinforcement"                 # Rebar, mesh, fibers, tendons, FRP sheets/plates
    # Thermal / acoustic
    thermal_insulation = "thermal_insulation"       # Mineral wool, EPS/XPS, PIR/PUR, cellulose, foam glass
    acoustic_insulation = "acoustic_insulation"     # Acoustic batts, mats, boards (when primary function is acoustic)
    # Finish / surface-related
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
    # Bonding / shaping / substrate layers
    binder = "binder"                               # Cements, limes
    adhesive = "adhesive"                           # Holds materials together (glue, resins, epoxies, paste)
    mortar = "mortar"                               # Masonry mortar, tile mortar
    grout = "grout"                                 # Often used to fill gaps or to reinforce existing structures
    sealant = "sealant"                             # Blocks passage of fluids through openings in materials
    # Safety & protection (non-fire)
    safety = "safety"                               # Guardrails, safety glazing film (non-structural safety), anti-slip tapes, impact protection
    fire_protection = "fire_protection"
    waterproofing = "waterproofing"
    # Joints & connections
    fastener = "fastener"
    # Groundworks / civil
    geosynthetic = "geosynthetic"                   # Geotextiles, geomembranes (non-waterproofing), geogrids, GCLs for soil functions
    paving_surfacing = "paving_surfacing"           # Asphalt, pavers, surface courses for roads/plazas (finish wearing course)
    # Fallbacks
    other = "other"
    unknown = "unknown"

# -------------------------------------- 
# ----------- CONCRETE ENUMS ----------- 
# -------------------------------------- 

class ConcreteType(str, Enum):
    ready_mixed = "ready_mixed"
    precast = "precast"
    printed_concrete = "printed_concrete"
    self_compacting = "self_compacting"
    lightweight = "lightweight"
    aerated = "aerated" # insulation
    binder = "binder"
    calcium_silicate = "calcium_silicate" # insulation
    foamed_concrete = "foamed_concrete" # insulation
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
    block = "block"                       # masonry (aerated, foamed, calcium silicate)
    tile = "tile"                         # smaller surface units (aerated, lightweight)
    generic_element = "generic_element"   # generic for precast elements, pavers, etc.
    # Insulating / specialized forms
    board = "board"                       # insulation board (aerated, calcium silicate, foamed)
    fill = "fill"                         # lightweight/foamed fill applications
    spray = "spray"                       # sprayed / shotcrete (ready-mixed, lightweight)
    printed = "printed"                   # additive manufacturing (printed_concrete)
    # Other / fallback
    other = "other"
    unknown = "unknown"

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
    unknown = "unknown"

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
    unknown = "unknown"
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
    unknown = "unknown"
class MetallicForm(str, Enum):
    sheet = "sheet"                      # thin flat rolled, typically <3 mm
    plate = "plate"                      # thick flat rolled (>3 mm)
    foil = "foil"                        # very thin sheet (<0.2 mm)
    coil = "coil"                        # continuous rolled strip wound in coils
    profile = "profile"                  # extruded or rolled shape (I-beam, angle, channel)
    bar = "bar"                          # solid long product, square or rectangular section
    rod = "rod"                          # round long product, smaller diameter than bar
    wire = "wire"                        # drawn long product, very small diameter
    tube = "tube"                        # hollow cylindrical or prismatic section (includes pipe)
    mesh = "mesh"                        # woven or welded metallic net
    rebar = "rebar"                      # ribbed/deformed reinforcing bar for concrete
    billet = "billet"                    # semi-finished cast form before rolling or extrusion
    ingot = "ingot"                      # cast form for remelting/rolling
    casting = "casting"                  # final cast component (drain cover, fitting, etc.)
    forging = "forging"                  # shaped by hammering or pressing
    powder = "powder"                    # metallic powder or granulate
    sheet_system = "sheet_system"        # assemblies of sheets (e.g., sandwich/composite panels)
    bolt = "bolt"
    screw = "screw"
    nail = "nail"
    rivet = "rivet"
    staple = "staple"
    anchor = "anchor"
    pin = "pin"
    other = "other"
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
# ----------- LIGNEOUS ENUMS -------------
# ----------------------------------------

class LigneousType(str, Enum):
    # Natural
    natural_softwood = "natural_softwood"      # sawn or planed softwood (e.g., spruce, pine)
    natural_hardwood = "natural_hardwood"      # sawn or planed hardwood (e.g., oak, beech)
    # Modified
    modified_wood = "modified_wood"            # thermally/chemically modified wood
    # Engineered / composite
    finger_jointed_structural_timber = "finger_jointed_structural_timber"
    glue_laminated_timber = "glue_laminated_timber"   # glulam
    cross_laminated_timber = "cross_laminated_timber" # CLT
    plywood = "plywood"
    laminated_veneer_lumber = "laminated_veneer_lumber" # LVL
    oriented_strand_board = "oriented_strand_board"     # OSB
    particleboard = "particleboard"                     # corrected naming (no underscore)
    softboard = "softboard"
    medium_density_fiberboard = "medium_density_fiberboard" # MDF
    high_density_fiberboard = "high_density_fiberboard"     # HDF
    hardboard = "hardboard"                               # sometimes distinguished from HDF
    # Insulation
    cellulose = "cellulose"
    cotton = "cotton"
    cork = "cork"
    flax = "flax"
    hemp = "hemp"
    sheep_wool = "sheep_wool"
    straw = "straw"
    wood_fibre = "wood_fibre"
    wood_wool = "wood_wool"
    # Fallbacks
    other = "other"
    unknown = "unknown"
class LigneousForm(str, Enum):
    lumber = "lumber"
    beam = "beam"
    plank = "plank"
    board = "board"
    flooring = "flooring"
    mat = "mat"
    roll = "roll"
    loose_fill = "loose_fill"
    other = "other"
class LigneousProcessing(str, Enum):
    unprocessed = "unprocessed"
    rough_sawn = "rough_sawn"
    planed_surfaced = "planed_surfaced"
    machine_graded = "machine_graded"
    finger_jointed = "finger_jointed"
    glued_panels = "glued_panels"
    other = "other"
    unknown = "unknown"
class BaseSpecies(str, Enum):
    spruce = "spruce"
    pine = "pine"
    larch = "larch"
    fir = "fir"
    oak = "oak"
    birch = "birch"
    mixed = "mixed"
    other = "other"
    unknown = "unknown"
class LigneousAdhesive(str, Enum):
    UF = "UF"
    MUF = "MUF"
    PF = "PF"
    pMDI = "pMDI"
    bio_based = "bio_based"
    other = "other"
    pass
class DryingMethod(str, Enum):
    fresh_green = "fresh_green"
    air_dried = "air_dried"
    kiln_dried = "kiln_dried"
    vacuum_dried = "vacuum_dried"
    solar_dried = "solar_dried"
    steam_conditioned = "steam_conditioned"
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
    cement = "cement"
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
    earthenware = "earthenware"
    stoneware = "stoneware"
    porcelain = "porcelain"
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
    masonry_unit_solid = "masonry_unit_solid"   # bricks/blocks with no through voids (clay brick, calcium-silicate brick)
    masonry_unit_hollow = "masonry_unit_hollow" # blocks with cavities/cores (clay block, AAC block, hollow concrete block)
    paver_unit = "paver_unit"                    # paving stones/flags/curbs as discrete units (stone, fired, cast)
    tile = "tile"                                # thin plate units (ceramic/stone tiles for floor/wall/roof)
    # Boards, panels, panes
    board = "board"                         # flat sheet/panel/board (gypsum board, cement/fiber-cement board, stone panels)
    glass_pane = "glass_pane"               # monolithic flat glass (float, patterned, toughened); IGUs handled elsewhere
    plate = "plate"                         # thick natural-stone slab/plate (dimension stone, countertops, façade plates)
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
    unknown = "unknown"


# ----------------------------------------
# ----------- POLYMER ENUMS --------------
# ----------------------------------------

class PolymericType(str, Enum):
    acrylic = "acrylic"
    epoxy = "epoxy"
    eps = "eps" # insulation
    eva = "eva"
    linoleum = "linoleum"
    pvc = "pvc"
    pe = "pe"
    pp = "pp"
    pet = "pet"
    ps = "ps"
    pmma = "pmma"
    phenolic_foam = "phenolic_foam" # insulation
    polyester = "polyester"
    polyethylene = "polyethylene"
    polyurethane = "polyurethane" # insulation (PU)
    polyisocyanurate = "polyisocyanurate" # insulation (PIR)
    polyamide = "polyamide"
    polycarbonate = "polycarbonate"
    silicone = "silicone"
    resin = "resin"
    rubber = "rubber"
    xps = "xps" # insulation
    composite_polymer = "composite_polymer" # insulation
    unknown = "unknown"
class PolymericForm(str, Enum):
    # sheet / film products
    sheet_membrane = "sheet_membrane"      # roll membranes, waterproofing sheets
    foil = "foil"                          # thin polymer/metalized films
    fleece = "fleece"                      # geotextiles, reinforcement fabrics
    floor_roll = "floor_roll"              # resilient flooring rolls (vinyl, linoleum)
    floor_tile = "floor_tile"              # modular flooring (LVT, rubber tile)
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
# ----------- BITUMINOUS ENUMS -----------
# ----------------------------------------

class BituminousType(str, Enum):
    asphalt_mix = "asphalt_mix"                        # asphalt/asphalt concrete (bitumen + aggregate)
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
    etics = "etics" # external thermal insulation composite system
    unknown = "unknown"

class CompositeForm(str, Enum):
    sandwich_panel = "sandwich_panel" # external thermal insulation composite system
    unknown = "unknown"

# -----------------------------------------
# ----------- COMPONENT ENUMS -------------
# -----------------------------------------
# DRAFT
class ComponentType(str, Enum):
    window = "window"
    door = "door"
    roof = "roof"
    wall = "wall"
    ceiling = "ceiling"
    building_system = "building_system"
    conveyor = "conveyor"
    other = "other" # not yet facet
    unknown = "unknown" # problematic?

# ------------------------------
# ----------- MISC -------------
# ------------------------------


class InputFormat(str, Enum):
    json = "json"
    pdf = "pdf"
    txt = "txt"

class PureComposite(str, Enum):
    pure = "pure"
    composite = "composite"
    unknown = "unknown"

class FractionBasis(str, Enum):
    mass = "mass"
    volume = "volume"
    unknown = "unknown"

class LabelOrigin(str, Enum):
    literal="literal"
    canonical="canonical"