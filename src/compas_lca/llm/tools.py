from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List, Literal
import csv, json, re

"""Initial draft for tools, which for now only focus on material decompositions"""

@dataclass
class DataTable:
    """Holds data tables for decomposition. Loaded once and injected into tools."""
    rebar_defaults: List[Dict[str, Any]]
    densities: Dict[str, float]
    @classmethod
    def from_paths(
        cls,
        rebar_csv: Path,
        densities_json: Path,
    ) -> "DataTable":
        with rebar_csv.open("r", encoding="utf-8") as f:
            rebar_rows = list(csv.DictReader(f))
        densities = json.loads(densities_json.read_text(encoding="utf-8"))
        return cls(rebar_defaults=rebar_rows, densities=densities)


def rebar_mass_fraction(
    element_type: Literal["slab","beam","column","wall","foundation","other"],
    concrete_grade: Optional[str] = None,
    exposure_class: Optional[str] = None,
    country: Optional[str] = None,
    *,
    data_table: DataTable,
) -> float:
    """
    Look up a default **rebar mass fraction** (0..1) for reinforced concrete elements.
    - Input: element_type (slab/beam/column/wall/foundation), optionally concrete_grade (e.g. 'C30/37'),
      exposure_class (e.g. 'XC1', 'XD3'), country (e.g. 'CH', 'DE').
    - Output: recommended **mass fraction of steel** in the composite (e.g., 0.038 for 3.8%).
    - Selection rule: choose the **most specific** matching row (exact element_type + country + exposure + grade substring).
      If multiple rows match, pick the one with the **highest specificity**; if none, return a conservative default (e.g. 0.03).
    """
    def score(row: Dict[str, Any]) -> int:
        sc = 0
        if row.get("element_type","").lower() == element_type:
            sc += 4
        if country and row.get("country","").upper() == country.upper():
            sc += 3
        if exposure_class and row.get("exposure","").upper() == (exposure_class.upper()):
            sc += 2
        if concrete_grade:
            pat = re.escape(concrete_grade)
            if re.search(pat, row.get("grade",""), re.I):
                sc += 1
        return sc

    candidates = sorted(data_table.rebar_defaults, key=score, reverse=True)
    best = candidates[0] if candidates and score(candidates[0]) > 0 else None
    if best:
        try:
            return float(best["mass_fraction"])
        except Exception:
            pass
    return 0.03  # fallback


def density_lookup(
    material_name: str,
    *,
    deps: DataTable,
) -> Optional[float]:
    """
    Return density in kg/m³ for a canonical pure material name (case-insensitive).
    If unknown, return None.
    """
    key = material_name.strip().lower()
    if key in deps.densities:
        return float(deps.densities[key])
    key2 = re.sub(r"[\s\-_]+", " ", key)
    for k, v in deps.densities.items():
        if re.sub(r"[\s\-_]+", " ", k.lower()) == key2:
            return float(v)
    return None


def studs_steel_volume_fraction(
    profile_depth_mm: Optional[float] = None,
    spacing_mm: Optional[float] = None,
    sheet_thickness_mm: Optional[float] = None,
) -> float:
    """
    Estimate **steel volume fraction** for a metal stud cavity wall:
    - If parameters are missing, use common defaults (e.g., 50 mm stud, 0.6 mm sheet, 625 mm spacing).
    - Returns a fraction 0..1 of **steel by volume** within the wall cross-section (e.g., 0.10 = 10%).
    - This is a rule-of-thumb estimator; record assumptions in output.
    """
    d = (profile_depth_mm or 50.0) / 1000.0      # m
    t = (sheet_thickness_mm or 0.6) / 1000.0     # m
    s = (spacing_mm or 625.0) / 1000.0           # m
    # naive “C” stud perimeter ~ 2d + 2*flange (take flange≈d/2 here), cross-section ≈ perimeter * t
    perimeter_m = (2*d + d)                      # very rough
    area_m2 = perimeter_m * t
    frac = min(max(area_m2 / (s * d), 0.0), 1.0)
    return frac
