import json

import csv

import pandas as pd

from pathlib import Path

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Iterable

# ----------------------------
# Constants
# ----------------------------
MISSING_STAGE_AS_ZERO = True
ALLOW_MASS_FROM_DENSITY_X_VOLUME = True
NET_STAGES = ["A1-A3", "A4", "C1", "C2", "C3", "D"]

# ----------------------------

OUTPUT_COLUMNS = [
    "element_eid",
    "layer_number",
    "element_global_id",
    "element_name",
    "entity",
    "object_type",
    "material_descriptor",
    "loadbearing",
    "placement",
    "entry_type",
    "material_type",
    "component_type",
    "facet_type",
    "thickness_m",
    "length_m",
    "area_m2",
    "volume_m3",
    "enriched_status",
    "match_score",
    "epd_id",
    "epd_name",
    "epd_dataset_source",
    "epd_registration_number",
    "epd_url",
    "epd_density",
    "epd_ref_unit",
    "epd_ref_size",
    "epd_indicator",
    "specific_value",
    "net_value",
    "unit",
    "scaling_factor",
    "scaling_basis",
    "note",
]


# ----------------------------
# IO helpers
# ----------------------------
def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_epd_index(epd_root: Path) -> Dict[str, Dict[str, Any]]:
    epd_by_id: Dict[str, Dict[str, Any]] = {}
    for p in epd_root.rglob("*.json"):
        try:
            epd = load_json(p)
            epd_id = epd.get("id")
            if epd_id:
                epd_by_id[epd_id] = epd
        except Exception as e:
            print(f"[WARN] Failed to load EPD {p}: {e}")
    return epd_by_id


def load_elements(elements_dir: Path) -> List[Dict[str, Any]]:
    elements: List[Dict[str, Any]] = []
    for p in elements_dir.rglob("*.json"):
        try:
            elements.append(load_json(p))
        except Exception as e:
            print(f"[WARN] Failed to load element {p}: {e}")
    return elements


def _to_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    s = str(x).strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _to_int_or_none(x: Any) -> Optional[int]:
    if x is None:
        return None
    s = str(x).strip()
    if s == "":
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def load_boq_rows_index(boq_csv: Path) -> Dict[Tuple[str, Optional[int]], List[Dict[str, Any]]]:
    """
    (EID, layer_no) -> [raw CSV row dict, ...]
    layer_no is None if Layer/Material Number is empty.

    Also: if layer_no is None, we additionally index the same row under (eid, 1)
    so single-material elements can lookup (eid, 1).
    """
    idx: Dict[Tuple[str, Optional[int]], List[Dict[str, Any]]] = {}
    with boq_csv.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            eid = (row.get("EID") or "").strip()
            if not eid:
                continue
            layer_no = _to_int_or_none(row.get("Layer/Material Number"))

            idx.setdefault((eid, layer_no), []).append(row)
            if layer_no is None:
                idx.setdefault((eid, 1), []).append(row)

    return idx


def layer_number_for_core_id(element: Dict[str, Any], core_id: str) -> Optional[int]:
    cores = element.get("element_core", []) or []
    for i, c in enumerate(cores):
        if c.get("core_id") == core_id:
            return i + 1
    return None


def pick_boq_row(
    boq_rows_idx: Dict[Tuple[str, Optional[int]], List[Dict[str, Any]]],
    eid: str,
    lookup_layer_no: Optional[int],
) -> Optional[Dict[str, Any]]:
    rows = boq_rows_idx.get((eid, lookup_layer_no))
    if not rows:
        return None
    # If multiple rows exist, choose the first deterministically
    return rows[0]


def boq_value(row: Optional[Dict[str, Any]], col: str) -> Optional[str]:
    if not row:
        return None
    v = row.get(col)
    if v is None:
        return None
    s = str(v).strip()
    return s if s != "" else None


def make_ordered_row(values: Dict[str, Any]) -> Dict[str, Any]:
    # Ensure every output column exists, in the required order
    return {k: values.get(k) for k in OUTPUT_COLUMNS}

def append_note(existing: Optional[str], extra: Optional[str]) -> Optional[str]:
    if not extra:
        return existing
    if not existing:
        return extra
    # keep deterministic, readable
    return f"{existing};{extra}"

def _round_floats_in_row(row: Dict[str, Any]) -> Dict[str, Any]:
    rounded = {}
    for k, v in row.items():
        if isinstance(v, float):
            rounded[k] = round(v, 4)
        else:
            rounded[k] = v
    return rounded
# ----------------------------
# Impact calculation helpers
# ----------------------------
def get_indicator(epd: Dict[str, Any], indicator_name: str) -> Optional[Dict[str, Any]]:
    inds = epd.get("indicators", {}).get("indicators", []) or []
    for ind in inds:
        if ind.get("name") == indicator_name:
            return ind
    return None

def _as_float_or_none(x: Any) -> Optional[float]:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        s = x.strip()
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None
    return None

def _average(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / float(len(values))

def stage_value(stages: Dict[str, Any], stage: str) -> Optional[float]:
    """
    Returns (value, used_scenario_average).

    Supported formats:
      - number/string: 12.3 / "12.3"
      - list of scenario dicts: [{"code": "...", "value": 12.3}, ...] -> average(value)
      - list of numbers/strings: [12.3, "44.1"] -> average
      - dict-of-scenarios (rare): {"Scenario A": 12.3, "Scenario B": 44.1} -> average(values)

    used_scenario_average == True iff the stage value had multiple scenario values and we averaged them.
    """
    v = stages.get(stage)
    if v is None:
        return None, False

    # Plain scalar
    scalar = _as_float_or_none(v)
    if scalar is not None:
        return scalar, False

    # List = scenarios or multiple values => average
    if isinstance(v, list):
        nums: List[float] = []
        for item in v:
            if isinstance(item, dict):
                n = _as_float_or_none(item.get("value"))
                if n is not None:
                    nums.append(n)
            else:
                n = _as_float_or_none(item)
                if n is not None:
                    nums.append(n)

        avg = _average(nums)
        # "multiple scenarios exist" disclaimer only if there were 2+ numeric values
        used_avg = len(nums) >= 2
        return avg, used_avg

    # Dict-of-scenarios => average its numeric leaf values
    if isinstance(v, dict):
        nums: List[float] = []
        for vv in v.values():
            n = _as_float_or_none(vv)
            if n is not None:
                nums.append(n)

        avg = _average(nums)
        used_avg = len(nums) >= 2
        return avg, used_avg

    return None, False

COMPOSITE_STAGES = {
    "A1-A3": ["A1", "A2", "A3"],
    # If you ever need more later:
    # "C1-C4": ["C1", "C2", "C3", "C4"],
}

def aggregate_net(indicator: Dict[str, Any], stages_to_use: List[str]) -> Tuple[Optional[float], List[str]]:
    """
    Returns:
      (net_value_or_none, stages_where_scenario_avg_was_used)
    """
    stages = indicator.get("stages", {}) or {}
    total = 0.0
    any_present = False
    scenario_avg_stages: List[str] = []

    for s in stages_to_use:
        v, used_avg = stage_value(stages, s)

        # Composite fallback: e.g. if "A1-A3" missing, sum A1 + A2 + A3
        if v is None and s in COMPOSITE_STAGES:
            parts = COMPOSITE_STAGES[s]
            part_sum = 0.0
            part_any = False
            part_used_avg_any = False

            for p in parts:
                pv, p_used_avg = stage_value(stages, p)
                if pv is None:
                    if MISSING_STAGE_AS_ZERO:
                        continue
                    part_sum = 0.0
                    part_any = False
                    part_used_avg_any = False
                    break

                part_any = True
                part_sum += pv
                part_used_avg_any = part_used_avg_any or p_used_avg
                if p_used_avg and p not in scenario_avg_stages:
                    scenario_avg_stages.append(p)

            if part_any:
                v = part_sum
                used_avg = part_used_avg_any

        if v is None:
            if MISSING_STAGE_AS_ZERO:
                continue
            return None, scenario_avg_stages

        any_present = True
        total += v
        if used_avg and s not in scenario_avg_stages:
            scenario_avg_stages.append(s)

    return (total if any_present else None), scenario_avg_stages

def scaling_factor_for_epd_reference_from_boq(
    boq_quantities: Dict[str, Optional[float]],
    epd: Dict[str, Any],
) -> Tuple[Optional[Tuple[float, str]], Optional[str]]:
    """
    Quantities are taken ONLY from BoQ.

    Returns:
      ( (factor, basis_string) or None, note_code or None )
    """
    ref = epd.get("reference", {}) or {}
    ref_size = ref.get("size")
    ref_unit = ref.get("unit")

    if ref_size in (None, 0) or ref_unit is None:
        return None, "EPD_REFERENCE_MISSING"

    try:
        ref_size_f = float(ref_size)
    except Exception:
        return None, "EPD_REFERENCE_MISSING"

    ref_unit_s = str(ref_unit).strip()

    vol = boq_quantities.get("volume")
    area = boq_quantities.get("area")
    length = boq_quantities.get("length")

    if ref_unit_s == "m3":
        if vol is None:
            return None, "BOQ_REQUIRED_QUANTITY_MISSING"
        return (
            float(vol) / ref_size_f,
            f"BoQ.volume_m3({float(vol):.4f}) / ref_m3({ref_size_f:.1f})",
        ), None

    if ref_unit_s == "m2":
        if area is None:
            return None, "BOQ_REQUIRED_QUANTITY_MISSING"
        return (
            float(area) / ref_size_f,
            f"BoQ.area_m2({float(area):.4f}) / ref_m2({ref_size_f:.1f})",
        ), None

    if ref_unit_s == "m":
        if length is None:
            return None, "BOQ_REQUIRED_QUANTITY_MISSING"
        return (
            float(length) / ref_size_f,
            f"BoQ.length_m({float(length):.4f}) / ref_m({ref_size_f:.1f})",
        ), None

    if ref_unit_s == "kg":
        if not ALLOW_MASS_FROM_DENSITY_X_VOLUME:
            return None, "EPD_REF_UNIT_UNSUPPORTED"
        if vol is None:
            return None, "BOQ_REQUIRED_QUANTITY_MISSING"
        density = epd.get("item_core", {}).get("density")
        if density is None:
            return None, "EPD_DENSITY_MISSING"
        mass = float(density) * float(vol)
        return (
            mass / ref_size_f,
            f"BoQ.mass_kg(density({float(density):.1f})*BoQ.vol({float(vol):.4f})={mass:.4f}) / ref_kg({ref_size_f:.1f})",
        ), None
    if ref_unit_s == "pcs":
        boq_pcs = 1.0
        return (
            boq_pcs / ref_size_f,
            f"BoQ.pcs({boq_pcs:.4f}) / ref_pcs({ref_size_f:.1f})",
        ), None
    return None, "EPD_REF_UNIT_UNSUPPORTED"


def compute_element_match_rows(
    element: Dict[str, Any],
    epd_by_id: Dict[str, Dict[str, Any]],
    indicators: List[str],
    boq_rows_idx: Dict[Tuple[str, Optional[int]], List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    desc = element.get("descriptor", {}) or {}
    elem_name = desc.get("element_name")
    eid = str(desc.get("element_eid") or "").strip()
    global_id = desc.get("element_global_id")
    obj_type = desc.get("object_type")
    is_multilayer = bool(desc.get("is_multilayer"))

    cores = element.get("element_core", []) or []
    all_core_ids: List[Optional[str]] = [c.get("core_id") for c in cores]

    matched_items = element.get("matched_items", []) or []
    matches_by_core_id: Dict[Optional[str], List[Dict[str, Any]]] = {
        mi.get("core_id"): (mi.get("matches", []) or [])
        for mi in matched_items
    }

    if not all_core_ids:
        all_core_ids = [mi.get("core_id") for mi in matched_items]

    for core_id in all_core_ids:
        if is_multilayer:
            lookup_layer_no = layer_number_for_core_id(element, core_id) if core_id else None
            output_layer_no: Optional[int] = lookup_layer_no
        else:
            lookup_layer_no = 1
            output_layer_no = None

        boq_row = pick_boq_row(boq_rows_idx, eid, lookup_layer_no)

        boq_quantities: Optional[Dict[str, Optional[float]]] = None
        if boq_row is not None:
            boq_quantities = {
                "thickness": _to_float(boq_row.get("Thickness [m]")),
                "length": _to_float(boq_row.get("Length [m]")),
                "area": _to_float(boq_row.get("Area [m2]")),
                "volume": _to_float(boq_row.get("Volume [m3]")),
            }

        core_matches = matches_by_core_id.get(core_id, [])

        # BoQ fields (safe even if boq_row is None)
        common = {
            "element_eid": eid,
            "layer_number": output_layer_no,
            "element_global_id": global_id,
            "element_name": elem_name,
            "entity": boq_value(boq_row, "Entity"),
            "object_type": obj_type,
            "material_descriptor": boq_value(boq_row, "Material Name"),
            "loadbearing": boq_value(boq_row, "Loadbearing"),
            "placement": boq_value(boq_row, "Placement"),
            "entry_type": boq_value(boq_row, "Entry Type"),
            "material_type": boq_value(boq_row, "Material Type"),
            "component_type": boq_value(boq_row, "Component Type"),
            "facet_type": boq_value(boq_row, "Facet Type"),
            "thickness_m": _to_float(boq_value(boq_row, "Thickness [m]")),
            "length_m": _to_float(boq_value(boq_row, "Length [m]")),
            "area_m2": _to_float(boq_value(boq_row, "Area [m2]")),
            "volume_m3": _to_float(boq_value(boq_row, "Volume [m3]")),
            "enriched_status": boq_value(boq_row, "Enriched"),
        }

        if not core_matches:
            note = "NO_MATCHES" if boq_row is not None else "BOQ_ROW_NOT_FOUND"
            rows.append(make_ordered_row({**common, "note": note}))
            continue

        if boq_quantities is None:
            for m in core_matches:
                rows.append(make_ordered_row({
                    **common,
                    "match_score": m.get("match_score"),
                    "epd_id": m.get("item_id"),
                    "epd_name": m.get("item_name"),
                    "epd_dataset_source": m.get("dataset_source"),
                    "epd_registration_number": m.get("registration_number"),
                    "note": "BOQ_ROW_NOT_FOUND",
                }))
            continue

        for m in core_matches:
            epd_id = m.get("item_id")
            epd = epd_by_id.get(epd_id)

            if epd is None:
                rows.append(make_ordered_row({
                    **common,
                    "match_score": m.get("match_score"),
                    "epd_id": epd_id,
                    "epd_name": m.get("item_name"),
                    "epd_dataset_source": m.get("dataset_source"),
                    "epd_registration_number": m.get("registration_number"),
                    "note": "EPD_NOT_FOUND",
                }))
                continue

            # EPD core + metadata fields
            epd_item_core = epd.get("item_core", {}) or {}
            epd_meta = epd.get("metadata", {}) or {}
            epd_ref = epd.get("reference", {}) or {}

            epd_core_fields = {
                "epd_id": epd_id,
                "epd_name": epd_item_core.get("name", m.get("item_name")),
                "epd_dataset_source": epd_meta.get("dataset_source", m.get("dataset_source")),
                "epd_registration_number": epd_meta.get("registration_number", m.get("registration_number")),
                "epd_url": epd_meta.get("dataset_url"),
                "epd_density": epd_item_core.get("density"),
                "epd_ref_unit": epd_ref.get("unit"),
                "epd_ref_size": epd_ref.get("size"),
            }

            scale, scale_err = scaling_factor_for_epd_reference_from_boq(boq_quantities, epd)
            if scale is None:
                rows.append(make_ordered_row({
                    **common,
                    "match_score": m.get("match_score"),
                    **epd_core_fields,
                    "note": scale_err or "NO_COMPATIBLE_QUANTITY_FOR_REFERENCE_UNIT",
                }))
                continue

            factor, basis = scale

            for ind_name in indicators:
                ind = get_indicator(epd, ind_name)
                if ind is None:
                    rows.append(make_ordered_row({
                        **common,
                        "match_score": m.get("match_score"),
                        **epd_core_fields,
                        "epd_indicator": ind_name,
                        "scaling_factor": factor,
                        "scaling_basis": basis,
                        "note": "INDICATOR_NOT_FOUND",
                    }))
                    continue

                # "specific_value" = per-reference net (before scaling)
                net_per_ref, scenario_avg_stages = aggregate_net(ind, NET_STAGES)
                scenario_note = None
                if scenario_avg_stages:
                    # deterministic ordering (already in encountered order; you can sort() if you prefer)
                    scenario_note = f"SCENARIO_AVG_USED({','.join(scenario_avg_stages)})"
                unit = ind.get("unit")

                if net_per_ref is None:
                    rows.append(make_ordered_row({
                        **common,
                        "match_score": m.get("match_score"),
                        **epd_core_fields,
                        "epd_indicator": ind_name,
                        "unit": unit,
                        "scaling_factor": factor,
                        "scaling_basis": basis,
                        "note": append_note("NET_STAGE_VALUES_MISSING", scenario_note),
                    }))
                    continue

                rows.append(make_ordered_row({
                    **common,
                    "match_score": m.get("match_score"),
                    **epd_core_fields,
                    "epd_indicator": ind_name,
                    "specific_value": net_per_ref,
                    "net_value": net_per_ref * factor,
                    "unit": unit,
                    "scaling_factor": factor,
                    "scaling_basis": basis,
                    "note": append_note(None, scenario_note),
                }))

    return rows

# ----------------------------
# Aggregated emissions (by object type + layer)
# ----------------------------

import pandas as pd
from pathlib import Path
from typing import Optional, List, Any

OUTPUT_COLUMNS_AGG = [
    "object_type",
    "layer_number",
    "entity",
    "material_descriptor",
    "loadbearing",
    "placement",
    "entry_type",
    "material_type",
    "component_type",
    "facet_type",
    "thickness_m",
    "length_m",
    "area_m2",
    "volume_m3",
    "enriched_status",
    "match_score",
    "epd_id",
    "epd_name",
    "epd_dataset_source",
    "epd_registration_number",
    "epd_url",
    "epd_density",
    "epd_ref_unit",
    "epd_ref_size",
    "epd_indicator",
    "specific_value",
    "net_value",
    "unit",
    "scaling_factor",
    "scaling_basis",
    "note",
]

_NUM_SUM_COLS = ["length_m", "area_m2", "volume_m3", "net_value"]
_NUM_FIRST_COLS = ["thickness_m", "epd_density", "epd_ref_size", "specific_value", "scaling_factor"]

_TEXT_FIRST_COLS = [
    "entity",
    "material_descriptor",
    "loadbearing",
    "placement",
    "entry_type",
    "material_type",
    "component_type",
    "facet_type",
    "epd_id",
    "epd_name",
    "epd_dataset_source",
    "epd_registration_number",
    "epd_url",
    "epd_ref_unit",
    "epd_indicator",
    "unit",
    "scaling_basis",
]

def _first_non_null(s: pd.Series) -> Any:
    s2 = s.dropna()
    if s2.empty:
        return None
    # also treat empty strings as null-ish
    for v in s2.tolist():
        if isinstance(v, str):
            vv = v.strip()
            if vv != "":
                return vv
        else:
            return v
    return None

def _sum_numeric(s: pd.Series) -> Optional[float]:
    # Coerce to numeric; ignore non-numeric garbage
    nums = pd.to_numeric(s, errors="coerce")
    if nums.isna().all():
        return None
    return float(nums.sum(skipna=True))

def _max_numeric(s: pd.Series) -> Optional[float]:
    nums = pd.to_numeric(s, errors="coerce")
    if nums.isna().all():
        return None
    return float(nums.max(skipna=True))

def _enriched_status_agg(s: pd.Series) -> Optional[str]:
    vals = []
    for v in s.dropna().tolist():
        if isinstance(v, str):
            vv = v.strip()
            if vv != "":
                vals.append(vv)
        else:
            vals.append(str(v))
    if not vals:
        return None
    uniq = list(dict.fromkeys(vals))  # stable unique
    return uniq[0] if len(uniq) == 1 else "MIXED"

def _note_agg(s: pd.Series) -> Optional[str]:
    vals: List[str] = []
    for v in s.dropna().tolist():
        if v is None:
            continue
        vv = str(v).strip()
        if vv:
            vals.append(vv)
    if not vals:
        return None
    uniq = list(dict.fromkeys(vals))  # stable unique
    return ";".join(uniq)

def write_agg_impacts_csv(
    all_impacts_csv: Path,
    out_csv: Optional[Path] = None,
) -> Path:
    """
    Read all_impacts_{indicator}.csv and write agg_impacts_{indicator}.csv.

    Aggregation grain:
      one row per (object_type, layer_number, epd_id, epd_indicator)

    Rationale:
      - you want one row per matched EPD per object_type+layer_number bucket
      - quantities and net_value are summed across contributing elements
    """
    all_impacts_csv = Path(all_impacts_csv)
    if out_csv is None:
        name = all_impacts_csv.name
        if name.startswith("all_impacts_"):
            out_name = name.replace("all_impacts_", "agg_impacts_", 1)
        else:
            out_name = f"agg_{name}"
        out_csv = all_impacts_csv.with_name(out_name)

    df = pd.read_csv(all_impacts_csv)

    required = {"object_type", "layer_number", "epd_id"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Input CSV missing required columns: {sorted(missing)}")

    # Clean key columns a bit (avoid whitespace keys)
    df["object_type"] = df["object_type"].astype(str).str.strip()
    df["epd_id"] = df["epd_id"].astype(str).str.strip()

    # Treat empty strings as missing
    df.loc[df["object_type"] == "", "object_type"] = pd.NA
    df.loc[df["epd_id"] == "", "epd_id"] = pd.NA
    df = df[df["epd_id"].notna()].copy()

    # If epd_indicator exists, include it in the key for robustness.
    key_cols = ["object_type", "layer_number", "epd_id"]
    if "epd_indicator" in df.columns:
        df["epd_indicator"] = df["epd_indicator"].astype(str).str.strip()
        df.loc[df["epd_indicator"] == "", "epd_indicator"] = pd.NA
        key_cols.append("epd_indicator")

    group_keys = set(key_cols)

    agg_spec = {}

    # sums: quantities + net_value
    for c in _NUM_SUM_COLS:
        if c in df.columns and c not in group_keys:
            agg_spec[c] = _sum_numeric

    # first-non-null numeric fields (thickness etc.)
    for c in _NUM_FIRST_COLS:
        if c in df.columns and c not in group_keys:
            agg_spec[c] = _first_non_null

    # first-non-null text fields
    for c in _TEXT_FIRST_COLS:
        if c in df.columns and c not in group_keys:
            agg_spec[c] = _first_non_null

    # specials
    if "match_score" in df.columns:
        agg_spec["match_score"] = _max_numeric
    if "enriched_status" in df.columns:
        agg_spec["enriched_status"] = _enriched_status_agg
    if "note" in df.columns:
        agg_spec["note"] = _note_agg

    g = df.groupby(key_cols, dropna=False, sort=True)
    out = g.agg(agg_spec).reset_index()

    # Force layer_number to nullable integer
    out["layer_number"] = pd.to_numeric(out["layer_number"], errors="coerce").astype("Int64")

    # Round aggregated numeric outputs to 3 decimals
    round_cols = [
        "length_m",
        "area_m2",
        "volume_m3",
        "net_value",
        "thickness_m",
        "match_score",
        "epd_density",
        "epd_ref_size",
        "specific_value",
        "scaling_factor",
    ]
    for c in round_cols:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce").round(3)

    # Ensure columns + order
    for col in OUTPUT_COLUMNS_AGG:
        if col not in out.columns:
            out[col] = None
    out = out[OUTPUT_COLUMNS_AGG]

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_csv, index=False, encoding="utf-8")
    return out_csv

# ----------------------------
# CSV writing
# ----------------------------
def write_csv(path: Path, rows: List[Dict[str, Any]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            rounded_row = _round_floats_in_row(r)
            w.writerow(rounded_row)


def calculate_impacts(
    *,
    project_root: Path,
    epd_root: Path = Path("data/lca_database/oekobaudat_2024-I"),
    indicators: Optional[List[str]] = None,
    net_stages: Optional[List[str]] = None,
    out_dir: Optional[Path] = None,
    boq_csv: Optional[Path] = None,
    elements_dirs: Optional[List[Path]] = None,
    missing_stage_as_zero: bool = True,
    allow_mass_from_density_x_volume: bool = True,
) -> List[Path]:
    """
    compute impact CSVs from matched elements + enriched BoQ.

    Returns: list of written CSV paths (one per indicator).
    """
    print("")
    print("Calculating impacts...")

    if indicators is None:
        indicators = ["GWPtotal", "GWPbiogenic"]

    if net_stages is None:
        net_stages = ["A1-A3", "A4", "C1", "C2", "C3", "D"]

    if out_dir is None:
        out_dir = project_root / "06_report"

    if boq_csv is None:
        boq_csv = project_root / "04_enriched" / "BoQ_enriched.csv"

    if elements_dirs is None:
        elements_dirs = [
            project_root / "05_matched" / "single_materials",
            project_root / "05_matched" / "abstract_components",
            project_root / "05_matched" / "undefined_elements",
            project_root / "05_matched" / "layered_elements",
        ]

    # set module-level knobs used by your existing helper functions
    global MISSING_STAGE_AS_ZERO, ALLOW_MASS_FROM_DENSITY_X_VOLUME, NET_STAGES
    MISSING_STAGE_AS_ZERO = missing_stage_as_zero
    ALLOW_MASS_FROM_DENSITY_X_VOLUME = allow_mass_from_density_x_volume
    NET_STAGES = net_stages

    out_dir.mkdir(parents=True, exist_ok=True)

    epd_by_id = build_epd_index(epd_root)
    boq_rows_idx = load_boq_rows_index(boq_csv)

    elements: List[Dict[str, Any]] = []
    for d in elements_dirs:
        elements.extend(load_elements(d))

    written: List[Path] = []
    for ind_name in indicators:
        all_rows: List[Dict[str, Any]] = []
        for el in elements:
            all_rows.extend(compute_element_match_rows(el, epd_by_id, [ind_name], boq_rows_idx))

        safe_ind = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in ind_name)
        out_path = out_dir / f"all_impacts_{safe_ind}.csv"
        write_csv(out_path, all_rows)
        agg_path = write_agg_impacts_csv(out_path)  # auto-names to agg_impacts_{indicator}.csv
        print(f"Wrote {safe_ind} impact report {out_path} ({len(all_rows)} rows)")
        print(f"Wrote aggregated impact report {agg_path}")
        written.append(out_path)

    return written


# ----------------------------
# SUMMARY (for all_impacts_*.csv)
# ----------------------------

STABLE_COLS_ALL: list[str] = [
    "element_eid",
    "layer_number",
    "element_global_id",
    "element_name",
    "entity",
    "object_type",
    "material_descriptor",
    "loadbearing",
    "placement",
    "entry_type",
    "material_type",
    "component_type",
    "facet_type",
    "thickness_m",
    "length_m",
    "area_m2",
    "volume_m3",
    "enriched_status",
]

NUMERIC_STABLE_COLS: tuple[str, ...] = (
    "thickness_m",
    "length_m",
    "area_m2",
    "volume_m3",
)

GROUP_COLS_ALL: tuple[str, ...] = (
    "element_eid",
    "layer_number",
    "epd_indicator",
    "unit",
)

# ----------------------------
# SUMMARY (for agg_impacts_*.csv)
# ----------------------------

STABLE_COLS_AGG: list[str] = [
    "object_type",
    "layer_number",
    "entity",
    "material_descriptor",
    "loadbearing",
    "placement",
    "entry_type",
    "material_type",
    "component_type",
    "facet_type",
    "thickness_m",
    "length_m",
    "area_m2",
    "volume_m3",
    "enriched_status",
]

GROUP_COLS_AGG: tuple[str, ...] = (
    "object_type",
    "layer_number",
    "epd_indicator",
    "unit",
)

def _count_unique_elements_for_agg_summary(
    agg_impacts_path: Path,
) -> pd.DataFrame:
    """
    Returns a dataframe with columns:
      object_type, layer_number, elements_count

    Computed from the corresponding all_impacts_*.csv file sitting next to agg_impacts_*.csv.
    """
    all_path = agg_impacts_path.with_name(
        agg_impacts_path.name.replace("agg_impacts_", "all_impacts_", 1)
    )
    if not all_path.exists():
        raise FileNotFoundError(
            f"Cannot compute unique element counts: missing corresponding all_impacts file: {all_path}"
        )

    df_all = pd.read_csv(all_path, dtype=str)

    _ensure_required_columns(df_all, ["object_type", "layer_number", "element_eid"])

    df_all["object_type"] = df_all["object_type"].fillna("").astype(str).str.strip()
    df_all["layer_number"] = df_all["layer_number"].fillna("").astype(str).str.strip()
    df_all["element_eid"] = df_all["element_eid"].fillna("").astype(str).str.strip()

    # Drop empty element ids (shouldn't happen, but defensive)
    df_all = df_all[df_all["element_eid"] != ""]

    counts = (
        df_all.groupby(["object_type", "layer_number"], dropna=False)["element_eid"]
        .nunique()
        .reset_index()
        .rename(columns={"element_eid": "elements_count"})
    )
    return counts

def _ensure_required_columns(df: pd.DataFrame, required: Iterable[str]) -> None:
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def summarize_impacts(input_csv_path: str | Path, output_directory: str | Path) -> Path:
    """
    Summarize candidate EPD rows into key metrics.

    - all_impacts_*.csv  -> all_summary_*.csv  (grouped by element_eid + layer_number + indicator)
    - agg_impacts_*.csv  -> agg_summary_*.csv  (grouped by object_type + layer_number + indicator)
    """
    input_path = Path(input_csv_path).expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    is_all = input_path.name.startswith("all_impacts_")
    is_agg = input_path.name.startswith("agg_impacts_")

    if not (is_all or is_agg):
        raise ValueError("Input filename must start with 'all_impacts_' or 'agg_impacts_'")

    output_dir = Path(output_directory).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if is_all:
        stable_cols = STABLE_COLS_ALL
        group_cols = GROUP_COLS_ALL
        output_filename = input_path.name.replace("all_impacts_", "all_summary_", 1)
    else:
        stable_cols = STABLE_COLS_AGG
        group_cols = GROUP_COLS_AGG
        output_filename = input_path.name.replace("agg_impacts_", "agg_summary_", 1)

    output_path = output_dir / output_filename

    # Read as strings, then coerce numerics explicitly (keeps behavior deterministic)
    df = pd.read_csv(input_path, dtype=str)

    _ensure_required_columns(df, stable_cols + ["epd_indicator", "unit", "net_value"])

    # Normalize grouping column (layer_number may be empty for single-material cases)
    df["layer_number"] = df["layer_number"].fillna("").astype(str).str.strip()

    # Coerce numeric columns
    df["net_value"] = pd.to_numeric(df["net_value"], errors="coerce")
    for col in NUMERIC_STABLE_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Build aggregation spec
    agg_spec = {col: (col, "first") for col in stable_cols}
    agg_spec.update(
        {
            "net_impact_min": ("net_value", "min"),
            "net_impact_median": ("net_value", "median"),
            "net_impact_max": ("net_value", "max"),
        }
    )

    grouped = (
        df.groupby(list(group_cols), dropna=False, as_index=False)
        .agg(**agg_spec)
    )

    # If this is an aggregated impacts file, add unique element counts
    if is_agg:
        counts = _count_unique_elements_for_agg_summary(input_path)

        # Ensure same key normalization as above
        grouped["object_type"] = grouped["object_type"].fillna("").astype(str).str.strip()
        grouped["layer_number"] = grouped["layer_number"].fillna("").astype(str).str.strip()

        grouped = grouped.merge(
            counts,
            on=["object_type", "layer_number"],
            how="left",
        )

        # Optional: make it an integer column (nullable)
        grouped["elements_count"] = (
            pd.to_numeric(grouped["elements_count"], errors="coerce")
            .astype("Int64")
        )

    # Append requested indicator columns
    grouped["indicator_name"] = grouped["epd_indicator"]
    grouped["indicator_unit"] = grouped["unit"]

    # Round all float columns to 3 decimals
    float_cols = grouped.select_dtypes(include=["float64", "float32"]).columns
    grouped[float_cols] = grouped[float_cols].round(3)

    # Final column order
    output_columns = stable_cols + [
        "indicator_name",
        "net_impact_min",
        "net_impact_median",
        "net_impact_max",
        "indicator_unit",
    ]

    if is_agg:
        output_columns.append("elements_count")

    output_columns = [c for c in output_columns if c in grouped.columns]

    grouped[output_columns].to_csv(output_path, index=False)
    return output_path