"""
Reads:
  (A) an ObjectType+Layer summary CSV in the "object_type, layer_number, ..." format
  (B) an Element-layer CSV in the "element_eid, layer_number, element_name, ..., epd_id, ..., entry_type, material_type, component_type, ..." format

Writes a plain-text report with TWO chapters:

CHAPTER 1 — ObjectType + Layer flags (and ONLY these):
1) Extreme volume (Top 5)
   -> based on volume_m3 outliers (robust z-score) then by magnitude
2) Extreme MEDIAN emissions (Top 5)
   -> based on Total_net_impact_median outliers (robust z-score) then by |median|
3) Extreme MAX emissions (Top 5)
   -> based on Total_net_impact_max outliers (robust z-score) then by |max|
4) Extreme MIN emissions (Top 5)
   -> based on Total_net_impact_min outliers (robust z-score) then by |min|
5) Extreme MIN MAX deviation (Top 5)
   -> based on deviation outliers (robust z-score) then by deviation, where:
        deviation = max(
            abs(median - min),
            abs(max - median),
            abs(max - min)
        )
6) Missing quantities (all)
   -> any of thickness_m/length_m/area_m2/volume_m3 missing for that combo

CHAPTER 2 — Element + Layer flags (and ONLY these):
1) NO EPD matches (all)
   -> unique (element_name, layer_number, element_eid) where epd_id is missing/blank
2) UNDERDEFINED (all)
   -> unique (element_name, layer_number, element_eid) where
      entry_type == "unknown" OR material_type == "unknown" OR component_type == "unknown"
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import List
from typing import Tuple

import pandas as pd

# ----------------------------
# User-editable paths (used in __main__)
# ----------------------------
INPUT_CSV_OBJECTTYPE = r"temp/projects/duplex/06_report/GWPtotal/object_type_summary_dissected_GWPtotal.csv"
INPUT_CSV_ELEMENTS = r"temp/projects/duplex/06_report/GWPtotal/all_impacts_GWPtotal.csv"
OUTPUT_DIR = r"temp/projects/duplex/06_report"


# ----------------------------
# Constants
# ----------------------------
OUTPUT_FILENAME = "flag_report.txt"

GROUP_KEYS = ("object_type", "layer_number")
DISPLAY_KEYS = ("object_type", "layer_number", "entity")

QTY_FIELDS = ("thickness_m", "length_m", "area_m2", "volume_m3")

TOTAL_FIELD_MIN = "Total_net_impact_min"
TOTAL_FIELD_MAX = "Total_net_impact_max"
TOTAL_FIELD_MEDIAN = "Total_net_impact_median"  # printed as: "Total Global Warming Potential (kgCO2)"

# Robust outlier threshold (modified z-score via MAD).
# Higher => fewer outliers. Tune as desired.
Z_OUTLIER = 6.0


# ----------------------------
# Helpers
# ----------------------------
def norm_str(x: Any) -> str | None:
    if pd.isna(x):
        return None
    s = str(x).strip()
    return s if s else None


def norm_str_lower(x: Any) -> str | None:
    s = norm_str(x)
    return s.lower() if s is not None else None


def to_float(x: Any) -> float | None:
    if pd.isna(x):
        return None
    try:
        v = float(x)
        if pd.isna(v):
            return None
        return v
    except Exception:
        return None


def compute_median_mad(values: List[float]) -> Tuple[float, float]:
    """
    Returns (median, MAD). MAD is median(|x - median|).
    """
    if not values:
        return 0.0, 0.0
    s = pd.Series(values)
    med = float(s.median())
    mad = float((s - med).abs().median())
    return med, mad


def modified_z(v: float, median: float, mad: float) -> float:
    # If mad == 0, z-score is not meaningful; return 0 to avoid labeling everything.
    if mad == 0:
        return 0.0
    return 0.6745 * (v - median) / mad


def first_non_null(g: pd.DataFrame, col: str) -> str | None:
    if col not in g.columns:
        return None
    for x in g[col].tolist():
        s = norm_str(x)
        if s is not None:
            return s
    return None


def missing_quantities(g: pd.DataFrame) -> List[str]:
    """
    Returns a list of missing quantity field names for the group,
    based on the group's representative values.

    Representative values:
      - if multiple rows exist, we take the first non-null numeric encountered per field
        (since rows can represent alternative EPDs for the same physical object).
    """
    missing: List[str] = []
    for f in QTY_FIELDS:
        if f not in g.columns:
            missing.append(f)
            continue
        found = None
        for x in g[f].tolist():
            v = to_float(x)
            if v is not None:
                found = v
                break
        if found is None:
            missing.append(f)
    return missing


def representative_numeric_first(g: pd.DataFrame, field: str) -> float | None:
    """
    Representative numeric value for quantity-like fields that should be constant per group:
    - Take the first non-null numeric encountered.
    """
    if field not in g.columns:
        return None
    for x in g[field].tolist():
        v = to_float(x)
        if v is not None:
            return v
    return None


def representative_total(g: pd.DataFrame, field: str) -> float | None:
    """
    Representative numeric value for emissions-like fields where a group might have multiple rows:
    - Take the value with maximum absolute magnitude (most impactful option).
    """
    if field not in g.columns:
        return None
    vals = [to_float(x) for x in g[field].tolist()]
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return max(vals, key=lambda x: abs(x))


def format_group_header(meta: Dict[str, str | None]) -> str:
    base = f"ObjectType: {meta.get('object_type') or ''} | Layer: {meta.get('layer_number') or ''}"
    extras = []
    for k in DISPLAY_KEYS[2:]:
        v = meta.get(k)
        if v:
            extras.append(f"{k}={v}")
    if extras:
        return base + " | " + ", ".join(extras)
    return base


def format_element_key(element_name: str | None, layer_number: str | None, element_eid: str | None) -> str:
    return f"Element: {element_name or ''} | Layer: {layer_number or ''} | EID: {element_eid or ''}"


# ----------------------------
# Chapter 1 — ObjectType processing
# ----------------------------
@dataclass
class GroupRecord:
    key: Tuple[str | None, str | None]
    meta: Dict[str, str | None]

    volume_m3: float | None

    total_min: float | None
    total_median: float | None
    total_max: float | None

    deviation_min_max: float | None  # computed from min/median/max if available

    missing_qty: List[str]


def compute_deviation(total_min: float | None, total_median: float | None, total_max: float | None) -> float | None:
    """
    deviation = max(|median-min|, |max-median|, |max-min|)
    Requires all three; otherwise returns None.
    """
    if total_min is None or total_median is None or total_max is None:
        return None
    return max(
        abs(total_median - total_min),
        abs(total_max - total_median),
        abs(total_max - total_min),
    )


def build_group_records(df: pd.DataFrame) -> List[GroupRecord]:
    grouped = df.groupby(list(GROUP_KEYS), dropna=False, sort=False)
    records: List[GroupRecord] = []

    for (obj_type, layer), g in grouped:
        meta: Dict[str, str | None] = {
            "object_type": norm_str(obj_type),
            "layer_number": norm_str(layer),
        }
        for k in DISPLAY_KEYS[2:]:
            meta[k] = first_non_null(g, k)

        vol = representative_numeric_first(g, "volume_m3")
        tmin = representative_total(g, TOTAL_FIELD_MIN)
        tmed = representative_total(g, TOTAL_FIELD_MEDIAN)
        tmax = representative_total(g, TOTAL_FIELD_MAX)
        dev = compute_deviation(tmin, tmed, tmax)

        rec = GroupRecord(
            key=(meta["object_type"], meta["layer_number"]),
            meta=meta,
            volume_m3=vol,
            total_min=tmin,
            total_median=tmed,
            total_max=tmax,
            deviation_min_max=dev,
            missing_qty=missing_quantities(g),
        )
        records.append(rec)

    return records


def rank_top_outliers_generic(
    records: List[GroupRecord],
    value_getter: Callable[[GroupRecord], float | None],
    top_n: int = 5,
) -> List[Tuple[GroupRecord, float, float]]:
    """
    Generic outlier ranking:
    - Compute global median/MAD over all non-null values
    - Compute modified z-score for each record with a value
    - Keep only records with |z| >= Z_OUTLIER
    - Sort by (|z| desc, |value| desc)
    - Return top N as (record, z, value)
    """
    vals: List[float] = []
    for r in records:
        v = value_getter(r)
        if v is not None:
            vals.append(v)

    median, mad = compute_median_mad(vals)

    scored: List[Tuple[GroupRecord, float, float]] = []
    for r in records:
        v = value_getter(r)
        if v is None:
            continue
        z = modified_z(v, median, mad)
        if abs(z) >= Z_OUTLIER:
            scored.append((r, z, v))

    scored.sort(key=lambda t: (abs(t[1]), abs(t[2])), reverse=True)
    return scored[:top_n]


def write_chapter_objecttype(lines: List[str], records: List[GroupRecord]) -> None:
    lines.append("CHAPTER 1 — OBJECTTYPE + LAYER FLAGS")
    lines.append("=" * 80)
    lines.append(f"Groups evaluated: {len(records)}")
    lines.append("")

    # 1) Extreme volume (Top 5)
    lines.append("1. Extreme volume (Top 5)")
    lines.append("-" * 80)
    top_vol = rank_top_outliers_generic(records, value_getter=lambda r: r.volume_m3, top_n=5)
    if not top_vol:
        lines.append("(none)")
    else:
        for r, z, v in top_vol:
            lines.append(format_group_header(r.meta))
            lines.append(f"  volume_m3: {v}  (outlier score: {z:.2f})")
    lines.append("")

    # 2) Extreme MEDIAN emissions (Top 5)
    lines.append("2. Extreme MEDIAN emissions (Top 5)")
    lines.append("-" * 80)
    top_med = rank_top_outliers_generic(records, value_getter=lambda r: r.total_median, top_n=5)
    if not top_med:
        lines.append("(none)")
    else:
        for r, z, v in top_med:
            lines.append(format_group_header(r.meta))
            lines.append(f"  Total Global Warming Potential (kgCO2) [median]: {v}  (outlier score: {z:.2f})")
    lines.append("")

    # 3) Extreme MAX emissions (Top 5)
    lines.append("3. Extreme MAX emissions (Top 5)")
    lines.append("-" * 80)
    top_max = rank_top_outliers_generic(records, value_getter=lambda r: r.total_max, top_n=5)
    if not top_max:
        lines.append("(none)")
    else:
        for r, z, v in top_max:
            lines.append(format_group_header(r.meta))
            lines.append(f"  Total Global Warming Potential (kgCO2) [max]: {v}  (outlier score: {z:.2f})")
    lines.append("")

    # 4) Extreme MIN emissions (Top 5)
    lines.append("4. Extreme MIN emissions (Top 5)")
    lines.append("-" * 80)
    top_min = rank_top_outliers_generic(records, value_getter=lambda r: r.total_min, top_n=5)
    if not top_min:
        lines.append("(none)")
    else:
        for r, z, v in top_min:
            lines.append(format_group_header(r.meta))
            lines.append(f"  Total Global Warming Potential (kgCO2) [min]: {v}  (outlier score: {z:.2f})")
    lines.append("")

    # 5) Extreme MIN MAX deviation (Top 5)
    lines.append("5. Extreme MIN MAX deviation (Top 5)")
    lines.append("-" * 80)
    top_dev = rank_top_outliers_generic(records, value_getter=lambda r: r.deviation_min_max, top_n=5)
    if not top_dev:
        lines.append("(none)")
    else:
        for r, z, v in top_dev:
            lines.append(format_group_header(r.meta))
            lines.append(f"  deviation (max(|median-min|, |max-median|, |max-min|)): {v}  (outlier score: {z:.2f})")
            # context
            lines.append(f"    min={r.total_min} | median={r.total_median} | max={r.total_max}")
    lines.append("")

    # 6) Missing quantities (all)
    lines.append("6. Missing quantities (all)")
    lines.append("-" * 80)
    miss = [r for r in records if r.missing_qty]
    if not miss:
        lines.append("(none)")
    else:
        miss.sort(key=lambda r: (r.meta.get("object_type") or "", r.meta.get("layer_number") or ""))
        for r in miss:
            lines.append(format_group_header(r.meta))
            lines.append(f"  Missing: {', '.join(r.missing_qty)}")
    lines.append("")


# ----------------------------
# Chapter 2 — Element processing
# ----------------------------
ELEMENT_KEYS = ("element_name", "layer_number", "element_eid")


@dataclass(frozen=True)
class ElementKey:
    element_name: str | None
    layer_number: str | None
    element_eid: str | None


def iter_unique_element_keys(df: pd.DataFrame) -> Iterable[ElementKey]:
    """
    Return unique (element_name, layer_number, element_eid) triplets.
    Keeps None if missing.
    """
    missing_cols = [c for c in ELEMENT_KEYS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Elements CSV missing required columns: {missing_cols}")

    # Normalize columns once for uniqueness stability
    tmp = pd.DataFrame(
        {
            "element_name": df["element_name"].map(norm_str),
            "layer_number": df["layer_number"].map(norm_str),
            "element_eid": df["element_eid"].map(norm_str),
        }
    )
    tmp = tmp.drop_duplicates()

    for _, row in tmp.iterrows():
        yield ElementKey(
            element_name=row["element_name"],
            layer_number=row["layer_number"],
            element_eid=row["element_eid"],
        )


def element_has_any_epd_match(rows: pd.DataFrame) -> bool:
    """
    True if any row has a non-empty epd_id.
    """
    if "epd_id" not in rows.columns:
        return False
    for x in rows["epd_id"].tolist():
        if norm_str(x) is not None:
            return True
    return False


def element_is_underdefined(rows: pd.DataFrame) -> bool:
    """
    Underdefined if ANY row indicates unknown for entry/material/component type.
    We treat case-insensitively and trim whitespace.
    """

    def col_has_unknown(col: str) -> bool:
        if col not in rows.columns:
            # If the column doesn't exist, we do NOT auto-flag as underdefined;
            # change to True if you prefer "missing column => underdefined".
            return False
        for x in rows[col].tolist():
            if norm_str_lower(x) == "unknown":
                return True
        return False

    return col_has_unknown("entry_type") or col_has_unknown("material_type") or col_has_unknown("component_type")


def write_chapter_elements(lines: List[str], df_elements: pd.DataFrame) -> None:
    lines.append("CHAPTER 2 — ELEMENT + LAYER FLAGS")
    lines.append("=" * 80)

    # Group by the triplet so we can reason across multiple EPD-option rows for the same element+layer.
    grouped = df_elements.groupby(list(ELEMENT_KEYS), dropna=False, sort=False)

    # 1) NO EPD matches
    lines.append("1. NO EPD matches (all)")
    lines.append("-" * 80)
    no_epd: List[ElementKey] = []
    for (element_name, layer_number, element_eid), g in grouped:
        if not element_has_any_epd_match(g):
            no_epd.append(ElementKey(norm_str(element_name), norm_str(layer_number), norm_str(element_eid)))

    if not no_epd:
        lines.append("(none)")
    else:
        # stable sort for readability
        no_epd.sort(key=lambda k: (k.element_name or "", k.layer_number or "", k.element_eid or ""))
        lines.append(f"Count: {len(no_epd)}")
        for k in no_epd:
            lines.append(format_element_key(k.element_name, k.layer_number, k.element_eid))
    lines.append("")

    # 2) UNDERDEFINED
    lines.append('2. UNDERDEFINED (all)  [entry_type/material_type/component_type == "unknown"]')
    lines.append("-" * 80)
    under: List[ElementKey] = []
    for (element_name, layer_number, element_eid), g in grouped:
        if element_is_underdefined(g):
            under.append(ElementKey(norm_str(element_name), norm_str(layer_number), norm_str(element_eid)))

    if not under:
        lines.append("(none)")
    else:
        under.sort(key=lambda k: (k.element_name or "", k.layer_number or "", k.element_eid or ""))
        lines.append(f"Count: {len(under)}")
        for k in under:
            lines.append(format_element_key(k.element_name, k.layer_number, k.element_eid))
    lines.append("")


# ----------------------------
# Public API
# ----------------------------
def run_flag_report(
    input_csv_objecttype: str | Path,
    input_csv_elements: str | Path,
    output_dir: str | Path,
) -> None:
    """
    Args:
        input_csv_objecttype: path to ObjectType+Layer summary CSV
        input_csv_elements: path to element-layer CSV
        output_dir: directory to write report into (created if missing)

    Returns:
        Path to written report.
    """
    input_csv_objecttype = Path(input_csv_objecttype)
    input_csv_elements = Path(input_csv_elements)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    out_path = output_dir / OUTPUT_FILENAME

    # --- Read objecttype summary CSV ---
    df_obj = pd.read_csv(input_csv_objecttype, dtype=str)
    df_obj.columns = [c.strip() for c in df_obj.columns]

    for c in GROUP_KEYS:
        if c not in df_obj.columns:
            raise ValueError(f"ObjectType CSV missing required column: {c}")

    records = build_group_records(df_obj)

    # --- Read elements CSV ---
    df_el = pd.read_csv(input_csv_elements, dtype=str)
    df_el.columns = [c.strip() for c in df_el.columns]

    for c in ELEMENT_KEYS:
        if c not in df_el.columns:
            raise ValueError(f"Elements CSV missing required column: {c}")

    # --- Write report ---
    lines: List[str] = []
    lines.append("FLAG REPORT")
    lines.append("=" * 80)
    lines.append(f"ObjectType CSV: {input_csv_objecttype}")
    lines.append(f"Elements   CSV: {input_csv_elements}")
    lines.append("")

    write_chapter_objecttype(lines, records)
    write_chapter_elements(lines, df_el)

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
