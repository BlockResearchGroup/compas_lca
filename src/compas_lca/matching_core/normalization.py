from __future__ import annotations

from typing import Any
from typing import Optional

from compas_lca.enums import (
    BiobasedType,
    BituminousType,
    CompositeType,
    ConcreteType,
    FrameType,
    InsulationElementType,
    MetallicType,
    MineralType,
    PolymericType,
    WindowFittingType,
    WoodType,
)


def _clean(value: Any) -> Optional[str]:
    """Lowercase and normalize separators for incoming enum-like values."""
    if value is None:
        return None
    if hasattr(value, "value"):
        value = value.value  # Enum to str
    if not isinstance(value, str):
        return None
    v = value.strip().lower().replace("-", "_").replace(" ", "_")
    while "__" in v:
        v = v.replace("__", "_")
    return v or None


def _pick(value: Optional[str], allowed: set[str]) -> Optional[str]:
    if value is None:
        return None
    return value if value in allowed else None


# ------------------------
# Polymeric
# ------------------------
# Only abbreviations and spelling variations
POLYMERIC_ALIASES = {
    "pvc": "polyvinyl_chloride",
    "polyvinylchlorid": "polyvinyl_chloride",  # German spelling
    "pe": "polyethylene",
    "pp": "polypropylene",
    "pa": "polyamide",
    "nylon": "polyamide",
    "silicon": "silicone",  # common misspelling
    "pur": "polyurethane",
    "pir": "polyurethane",  # PIR is a subtype of PUR
    "eps": "expanded_polystyrene",
    "xps": "extruded_polystyrene",
}


def normalize_polymeric_type(value: Any) -> Optional[str]:
    v = _clean(value)
    if v is None:
        return None
    v = POLYMERIC_ALIASES.get(v, v)
    allowed = {t.value for t in PolymericType}
    return _pick(v, allowed)


# ------------------------
# Composite
# ------------------------
# Only abbreviations and spelling variations
COMPOSITE_ALIASES = {
    "frp": "fiber_reinforced_polymer",  # abbreviation
    "gfrp": "fiber_reinforced_polymer",  # abbreviation (glass)
    "cfrp": "fiber_reinforced_polymer",  # abbreviation (carbon)
    "fibre_reinforced_polymer": "fiber_reinforced_polymer",  # British spelling
    "fiber_cement": "fiber_cement_composite",  # shortened
    "fibre_cement": "fiber_cement_composite",  # British spelling
    "fibre_cement_composite": "fiber_cement_composite",  # British spelling
    "wpc": "wood_plastic_composite",  # abbreviation
}


def normalize_composite_type(value: Any) -> Optional[str]:
    v = _clean(value)
    if v is None:
        return None
    v = COMPOSITE_ALIASES.get(v, v)
    allowed = {t.value for t in CompositeType}
    return _pick(v, allowed)


# ------------------------
# Metallic
# ------------------------
METALLIC_ALIASES = {
    "aluminium": "aluminum",
    "alu": "aluminum",
    "galvanized_steel": "carbon_steel",
}


def normalize_metallic_type(value: Any) -> Optional[str]:
    v = _clean(value)
    if v is None:
        return None
    v = METALLIC_ALIASES.get(v, v)
    allowed = {t.value for t in MetallicType}
    return _pick(v, allowed)


# ------------------------
# Mineral
# ------------------------
# Only spelling variations and compound word splits
MINERAL_ALIASES = {
    "calcium_sulphate": "gypsum",  # British spelling
    "silica": "silicum_dioxide",
    "silicon_dioxide": "silicum_dioxide",  # alternate naming
    "kalksandstein": "sand_lime_product",  # German term
    "stone_wool": "rock_wool",  # synonym
    "glasswool": "glass_wool",  # compound word
    "foamglass": "foam_glass",  # compound word
    "cellular_glass": "foam_glass",  # technical synonym
}


def normalize_mineral_type(value: Any) -> Optional[str]:
    v = _clean(value)
    if v is None:
        return None
    v = MINERAL_ALIASES.get(v, v)
    allowed = {t.value for t in MineralType}
    return _pick(v, allowed)


# ------------------------
# Concrete
# ------------------------
# Only abbreviations and hyphenation variations
CONCRETE_ALIASES = {
    "ready_mix": "ready_mixed",
    "pre_cast": "precast",  # hyphenation
    "scc": "self_compacting",  # abbreviation
    "aac": "aerated",  # abbreviation (autoclaved aerated concrete)
    "porenbeton": "aerated",  # German term
    "gasbeton": "aerated",  # German term
    "foam_concrete": "foamed_concrete",  # variant
    "calcium_sulphite": "calcium_sulfate",  # spelling
}


def normalize_concrete_type(value: Any) -> Optional[str]:
    v = _clean(value)
    if v is None:
        return None
    v = CONCRETE_ALIASES.get(v, v)
    allowed = {t.value for t in ConcreteType}
    return _pick(v, allowed)


# ------------------------
# Biobased
# ------------------------
BIOBASED_ALIASES = {
    "linen": "flax",
    "jute": "flax",
}


def normalize_biobased_type(value: Any) -> Optional[str]:
    v = _clean(value)
    if v is None:
        return None
    v = BIOBASED_ALIASES.get(v, v)
    allowed = {t.value for t in BiobasedType}
    return _pick(v, allowed)


# ------------------------
# Bituminous
# ------------------------
# Only abbreviations
BITUMINOUS_ALIASES = {
    "hma": "asphalt_mix",  # abbreviation (hot mix asphalt)
    "pmb": "polymer_modified_bitumen",  # abbreviation
}


def normalize_bituminous_type(value: Any) -> Optional[str]:
    v = _clean(value)
    if v is None:
        return None
    v = BITUMINOUS_ALIASES.get(v, v)
    allowed = {t.value for t in BituminousType}
    return _pick(v, allowed)


# ------------------------
# Wood
# ------------------------
# Only technical abbreviations and German translations
WOOD_ALIASES = {
    "softwood": "natural_softwood",
    "hardwood": "natural_hardwood",
    "glulam": "glue_laminated_timber",  # common abbreviation
    "bsh": "glue_laminated_timber",  # German abbrev (Brettschichtholz)
    "brettschichtholz": "glue_laminated_timber",  # German term
    "clt": "cross_laminated_timber",  # abbreviation
    "bsp": "cross_laminated_timber",  # German abbrev (Brettsperrholz)
    "brettsperrholz": "cross_laminated_timber",  # German term
    "lvl": "laminated_veneer_lumber",  # abbreviation
    "furnierschichtholz": "laminated_veneer_lumber",  # German term
    "osb": "oriented_strand_board",  # abbreviation
    "mdf": "medium_density_fiberboard",  # abbreviation
    "hdf": "high_density_fiberboard",  # abbreviation
    "chipboard": "particleboard",  # British term
    "spanplatte": "particleboard",  # German term
    "kvh": "finger_jointed_structural_timber",  # German abbrev
    "holzfaser": "wood_fibre",  # German term
    "holzwolle": "wood_wool",  # German term
    "zellulose": "cellulose",  # German term
    "wood_fiber": "wood_fibre",  # American spelling
}


def normalize_wood_type(value: Any) -> Optional[str]:
    v = _clean(value)
    if v is None:
        return None
    v = WOOD_ALIASES.get(v, v)
    allowed = {t.value for t in WoodType}
    return _pick(v, allowed)


# ------------------------
# Insulation Element
# ------------------------
# Only abbreviations
INSULATION_ELEMENT_ALIASES = {
    "sip": "sandwich_panel",  # abbreviation
    "wdvs": "etics",  # German abbreviation
    "eifs": "etics",  # US abbreviation
}


def normalize_insulation_element_type(value: Any) -> Optional[str]:
    v = _clean(value)
    if v is None:
        return None
    v = INSULATION_ELEMENT_ALIASES.get(v, v)
    allowed = {t.value for t in InsulationElementType}
    return _pick(v, allowed)


# ------------------------
# Components
# ------------------------
WINDOW_FITTING_ALIASES = {
    "aluminum": "aluminium",
}


def normalize_window_fitting_type(value: Any) -> Optional[str]:
    v = _clean(value)
    if v is None:
        return None
    v = WINDOW_FITTING_ALIASES.get(v, v)
    allowed = {t.value for t in WindowFittingType}
    return _pick(v, allowed)


FRAME_TYPE_ALIASES = {
    "aluminum": "aluminium",
    "pvc": "pvc",
}


def normalize_frame_type(value: Any) -> Optional[str]:
    v = _clean(value)
    if v is None:
        return None
    v = FRAME_TYPE_ALIASES.get(v, v)
    allowed = {t.value for t in FrameType}
    return _pick(v, allowed)


# ------------------------
# Generic dispatcher
# ------------------------

def normalize_level3_value(level2_type: Optional[str], value: Any) -> Optional[str]:
    """
    Normalize a level-3 value given the level-2 type.
    Keeps the logic centralized for both model validation and evaluation.
    """
    key = (level2_type or "").lower()
    if key == "polymeric":
        return normalize_polymeric_type(value)
    if key == "composite":
        return normalize_composite_type(value)
    if key == "metallic":
        return normalize_metallic_type(value)
    if key == "mineral":
        return normalize_mineral_type(value)
    if key == "concrete":
        return normalize_concrete_type(value)
    if key == "biobased":
        return normalize_biobased_type(value)
    if key == "bituminous":
        return normalize_bituminous_type(value)
    if key == "wood":
        return normalize_wood_type(value)
    if key == "insulation_element":
        return normalize_insulation_element_type(value)
    if key == "window_fitting":
        return normalize_window_fitting_type(value)
    if key == "window":
        return normalize_frame_type(value)
    return _clean(value)

