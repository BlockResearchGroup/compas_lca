from __future__ import annotations

from typing import Any, Optional

from compas_lca.enums import (
    BiobasedType,
    BituminousType,
    CompositeType,
    ConcreteType,
    FrameType,
    MetallicType,
    MineralType,
    PolymericType,
    WindowFittingType,
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
POLYMERIC_ALIASES = {
    "pvc": "polyvinyl_chloride",
    "polyvinylchlorid": "polyvinyl_chloride",
    "polyvinyl_chlorid": "polyvinyl_chloride",
    "vinyl": "polyvinyl_chloride",
    "pe": "polyethylene",
    "hdpe": "polyethylene",
    "ldpe": "polyethylene",
    "u_pe": "polyethylene",
    "pet": "polyester",
    "pp": "polypropylene",
    "pa": "polyamide",
    "nylon": "polyamide",
    "epdm": "rubber",
    "silicon": "silicone",
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
COMPOSITE_ALIASES = {
    "frp": "fiber_reinforced_polymer",
    "gfrp": "fiber_reinforced_polymer",
    "cfrp": "fiber_reinforced_polymer",
    "bfrp": "fiber_reinforced_polymer",
    "fiberglass": "fiber_reinforced_polymer",
    "glass_fiber_reinforced_polymer": "fiber_reinforced_polymer",
    "glass_fibre_reinforced_polymer": "fiber_reinforced_polymer",
    "carbon_fiber_reinforced_polymer": "fiber_reinforced_polymer",
    "carbon_fibre_reinforced_polymer": "fiber_reinforced_polymer",
    "fiber_reinforced_plastic": "fiber_reinforced_polymer",
    "fibre_reinforced_plastic": "fiber_reinforced_polymer",
    "fiber_cement": "fiber_cement_composite",
    "fibre_cement": "fiber_cement_composite",
    "wpc": "wood_plastic_composite",
    "wood_plastic": "wood_plastic_composite",
    "polymer_concrete_resin": "polymer_concrete",
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
MINERAL_ALIASES = {
    "gypsum_board": "gypsum",
    "calcium_sulfate": "gypsum",
    "calcium_sulphate": "gypsum",
    "silica": "silicum_dioxide",
    "silicon_dioxide": "silicum_dioxide",
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
CONCRETE_ALIASES = {
    "ready_mix": "ready_mixed",
    "ready_mixed_concrete": "ready_mixed",
    "pre_cast": "precast",
    "pre_cast_concrete": "precast",
    "self_compacting_concrete": "self_compacting",
    "aac": "aerated",
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
BITUMINOUS_ALIASES = {
    "mastic": "mastic_asphalt",
}


def normalize_bituminous_type(value: Any) -> Optional[str]:
    v = _clean(value)
    if v is None:
        return None
    v = BITUMINOUS_ALIASES.get(v, v)
    allowed = {t.value for t in BituminousType}
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
    if key == "window_fitting":
        return normalize_window_fitting_type(value)
    if key == "window":
        return normalize_frame_type(value)
    return _clean(value)

