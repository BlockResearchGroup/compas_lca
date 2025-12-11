from __future__ import annotations

from typing import Any, Optional

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
POLYMERIC_ALIASES = {
    "pvc": "polyvinyl_chloride",
    "polyvinylchlorid": "polyvinyl_chloride",
    "polyvinyl_chlorid": "polyvinyl_chloride",
    "vinyl": "polyvinyl_chloride",
    "pe": "polyethylene",
    "hdpe": "polyethylene",
    "ldpe": "polyethylene",
    "lldpe": "polyethylene",
    "u_pe": "polyethylene",
    "pet": "polyester",
    "pp": "polypropylene",
    "pa": "polyamide",
    "pa6": "polyamide",
    "pa66": "polyamide",
    "nylon": "polyamide",
    "epdm": "rubber",
    "silicon": "silicone",
    "pur": "polyurethane",
    "pir": "polyurethane",
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
    "gypsum_plaster": "gypsum",
    "calcium_sulphate": "gypsum",
    "silica": "silicum_dioxide",
    "silicon_dioxide": "silicum_dioxide",
    "quartz": "silicum_dioxide",
    "calcium_silicate_board": "sand_lime_product",
    "calcium_silicate_brick": "sand_lime_product",
    "kalksandstein": "sand_lime_product",
    "calcium_silicate": "sand_lime_product",
    "calcium_silicate_unit": "sand_lime_product",
    "calcium_silicate_masonry": "sand_lime_product",
    "calcium_silicate_block": "sand_lime_product",
    "calcium_silicate_element": "sand_lime_product",
    "calcium_silicate_panel": "sand_lime_product",
    "calcium_silicate_slab": "sand_lime_product",
    "calcium_silicate_wall": "sand_lime_product",
    "calcium_silicate_floor": "sand_lime_product",
    "mineralite": "mineral_wool",
    "rock_fiber": "rock_wool",
    "stone_wool": "rock_wool",
    "glasswool": "glass_wool",
    "fiberglass_insulation": "glass_wool",
    "foamglass": "foam_glass",
    "cellular_glass": "foam_glass",
    "portland_cement": "cement",
    "cement_paste": "cement",
    "hydraulic_lime": "lime",
    "quickite": "lime",
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
    "in_situ": "ready_mixed",
    "cast_in_place": "ready_mixed",
    "pre_cast": "precast",
    "pre_cast_concrete": "precast",
    "prefabricated_concrete": "precast",
    "self_compacting_concrete": "self_compacting",
    "scc": "self_compacting",
    "aac": "aerated",
    "autoclaved_aerated_concrete": "aerated",
    "cellular_concrete": "aerated",
    "porenbeton": "aerated",
    "gasbeton": "aerated",
    "ytong": "aerated",
    "hebel": "aerated",
    "foam_concrete": "foamed_concrete",
    "foamed": "foamed_concrete",
    "calcium_sulphite": "calcium_sulfate",
    "gypsum_concrete": "calcium_sulfate",
    "anhydrite": "calcium_sulfate",
    "anhydrite_screed": "calcium_sulfate",
    "calcium_aluminate": "binder",
    "uhpc": "ready_mixed",
    "ultra_high_performance_concrete": "ready_mixed",
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
    "asphalt": "asphalt_mix",
    "asphalt_concrete": "asphalt_mix",
    "hot_mix_asphalt": "asphalt_mix",
    "hma": "asphalt_mix",
    "cold_mix_asphalt": "asphalt_mix",
    "paving_asphalt": "asphalt_mix",
    "road_asphalt": "asphalt_mix",
    "app_modified": "polymer_modified_bitumen",
    "sbs_modified": "polymer_modified_bitumen",
    "modified_bitumen": "polymer_modified_bitumen",
    "pmb": "polymer_modified_bitumen",
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
WOOD_ALIASES = {
    "softwood": "natural_softwood",
    "solid_softwood": "natural_softwood",
    "spruce": "natural_softwood",
    "pine": "natural_softwood",
    "fir": "natural_softwood",
    "larch": "natural_softwood",
    "douglas_fir": "natural_softwood",
    "hardwood": "natural_hardwood",
    "solid_hardwood": "natural_hardwood",
    "oak": "natural_hardwood",
    "beech": "natural_hardwood",
    "ash": "natural_hardwood",
    "birch": "natural_hardwood",
    "maple": "natural_hardwood",
    "walnut": "natural_hardwood",
    "teak": "natural_hardwood",
    "glulam": "glue_laminated_timber",
    "bsh": "glue_laminated_timber",
    "brettschichtholz": "glue_laminated_timber",
    "laminated_timber": "glue_laminated_timber",
    "clt": "cross_laminated_timber",
    "x_lam": "cross_laminated_timber",
    "brettsperrholz": "cross_laminated_timber",
    "bsp": "cross_laminated_timber",
    "cross_lam": "cross_laminated_timber",
    "lvl": "laminated_veneer_lumber",
    "furnierschichtholz": "laminated_veneer_lumber",
    "kerto": "laminated_veneer_lumber",
    "osb": "oriented_strand_board",
    "osb_3": "oriented_strand_board",
    "osb_4": "oriented_strand_board",
    "mdf": "medium_density_fiberboard",
    "mdf_board": "medium_density_fiberboard",
    "hdf": "high_density_fiberboard",
    "hdf_board": "high_density_fiberboard",
    "chipboard": "particleboard",
    "spanplatte": "particleboard",
    "kvh": "finger_jointed_structural_timber",
    "keilgezinktes_vollholz": "finger_jointed_structural_timber",
    "finger_jointed": "finger_jointed_structural_timber",
    "end_jointed": "finger_jointed_structural_timber",
    "thermowood": "modified_wood",
    "thermally_modified": "modified_wood",
    "accoya": "modified_wood",
    "acetylated_wood": "modified_wood",
    "wood_fiber_insulation": "wood_fibre",
    "holzfaser": "wood_fibre",
    "holzfaserdaemmung": "wood_fibre",
    "holzwolle": "wood_wool",
    "heraklith": "wood_wool",
    "cellulose_insulation": "cellulose",
    "blown_cellulose": "cellulose",
    "zellulose": "cellulose",
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
INSULATION_ELEMENT_ALIASES = {
    "sandwich": "sandwich_panel",
    "sip": "sandwich_panel",
    "structural_insulated_panel": "sandwich_panel",
    "sandwich_construction": "sandwich_panel",
    "composite_panel": "sandwich_panel",
    "bonded_insulation": "layered_bonded",
    "laminated_insulation": "layered_bonded",
    "multi_layer_insulation": "layered_bonded",
    "wdvs": "etics",
    "eifs": "etics",
    "external_thermal_insulation_composite_system": "etics",
    "external_insulation": "etics",
    "insulated_masonry": "masonry_unit_with_infill",
    "filled_block": "masonry_unit_with_infill",
    "insulated_block": "masonry_unit_with_infill",
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

