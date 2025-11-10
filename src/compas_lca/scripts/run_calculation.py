# run_calculation.py (demo)
# Purpose: Load a serialized LcaElement JSON and print LCA result metrics.
# Adjust the imports to match your project structure if needed.

from pathlib import Path

import json

from typing import Optional
from typing import List

from compas_lca.model.lca_element import LcaElement
from compas_lca.inventory.constants import EN15978_STAGES

# >>>> SET YOUR JSON FILE HERE <<<<
"""
# single layer
JSON_PATH = Path("src/compas_lca/scripts/samples/test_out_matching/test_metal.json")
"""

# multi layer
JSON_PATH = Path("src/compas_lca/scripts/samples/test_out_matching/test_multilayer.json")

# ------- utility printing helpers -------

def _fmt(x: Optional[float], unit: str = "kg CO2e") -> str:
    if x is None:
        return "—"
    if abs(x) >= 1:
        return f"{x:,.2f} {unit}"
    return f"{x:.4g} {unit}"

def _banner(title: str) -> None:
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)

def _kv(label: str, value: str, w: int = 28) -> None:
    print(f"{label:<{w}} {value}")

# ------- main runner -------

def main():
    if not JSON_PATH.exists():
        raise FileNotFoundError(f"JSON file not found: {JSON_PATH}")

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))

    # Pydantic v2 style (your class uses ConfigDict -> v2)
    element = LcaElement.model_validate(data)

    # general info
    name = getattr(element.descriptor, "element_name", None) or getattr(element.descriptor, "object_type", "—")
    is_multilayer = bool(getattr(element.descriptor, "is_multilayer", False))
    cores = element.element_core or []
    n_cores = len(cores)

    _banner("LCA ELEMENT SUMMARY")
    _kv("Element ID:", str(element.id))
    _kv("Element name:", name)
    _kv("Is multilayer:", str(is_multilayer))
    _kv("Core count:", str(n_cores))

    # show ratios if multilayer (uses your internal helper)
    if n_cores >= 2:
        try:
            ratio_map = element._layer_ratio_map()  # private helper, fine for this runner
        except Exception:
            ratio_map = {}
        if ratio_map:
            print("\nLayer thickness ratios (applied only to volume paths):")
            for core in cores:
                cid = str(core.core_id)
                cname = getattr(core, "name", "—")
                ratio = ratio_map.get(cid, 1.0)
                print(f"  - {cname} [{cid}]: {ratio:.4f}")

    # choose a default stages view; adjust as you like
    # Example 1: “Cradle-to-grave excluding D” (common reporting)
    include_stage_D = False
    stages_filter: Optional[List[EN15978_STAGES]] = None  # None => include whatever stages exist (except D if excluded)

    _banner("OVERALL MATCH-LEVEL STATS (single datasets)")
    min_gwp = element.min_gwp(include_stage_D=include_stage_D, stages_filter=stages_filter)
    med_gwp = element.median_gwp(include_stage_D=include_stage_D, stages_filter=stages_filter)
    max_gwp = element.max_gwp(include_stage_D=include_stage_D, stages_filter=stages_filter)

    _kv("Min GWP (any match):", _fmt(min_gwp))
    _kv("Median GWP (any match):", _fmt(med_gwp))
    _kv("Max GWP (any match):", _fmt(max_gwp))

    _banner("ELEMENT-LEVEL TOTALS (sum across cores)")
    min_total = element.min_total_gwp(include_stage_D=include_stage_D, stages_filter=stages_filter)
    max_total = element.max_total_gwp(include_stage_D=include_stage_D, stages_filter=stages_filter)
    _kv("Min TOTAL GWP (sum of per-core minima):", _fmt(min_total))
    _kv("Max TOTAL GWP (sum of per-core maxima):", _fmt(max_total))

    # optional weighted mean (if implemented)
    if hasattr(element, "weighted_mean_total_gwp"):
        try:
            wmean_total = element.weighted_mean_total_gwp(
                include_stage_D=include_stage_D,
                stages_filter=stages_filter,
            )
        except TypeError:
            # method exists but has different signature
            wmean_total = None
        _kv("Weighted-mean TOTAL GWP:", _fmt(wmean_total))

    # per-core stats (useful for multilayer elements)
    if n_cores:
        _banner("PER-CORE STATS")
        for core in cores:
            cid = str(core.core_id)
            cname = getattr(core, "name", "—")
            vmin = element.min_gwp(core_id=cid, include_stage_D=include_stage_D, stages_filter=stages_filter)
            vmed = element.median_gwp(core_id=cid, include_stage_D=include_stage_D, stages_filter=stages_filter)
            vmax = element.max_gwp(core_id=cid, include_stage_D=include_stage_D, stages_filter=stages_filter)
            print(f"\nCore: {cname} [{cid}]")
            _kv("  min:", _fmt(vmin))
            _kv("  median:", _fmt(vmed))
            _kv("  max:", _fmt(vmax))

    # optional: a second view focused on A1-A3 only
    stages_filter_a1a3: Optional[List[EN15978_STAGES]] = ["A1-A3"]  # exact-key match in your current logic
    _banner("ALTERNATE VIEW — PRODUCT STAGE ONLY (A1-A3)")
    min_total_a1a3 = element.min_total_gwp(include_stage_D=False, stages_filter=stages_filter_a1a3)
    max_total_a1a3 = element.max_total_gwp(include_stage_D=False, stages_filter=stages_filter_a1a3)
    _kv("Min TOTAL (A1-A3):", _fmt(min_total_a1a3))
    _kv("Max TOTAL (A1-A3):", _fmt(max_total_a1a3))
    if hasattr(element, "weighted_mean_total_gwp"):
        try:
            wmean_total_a1a3 = element.weighted_mean_total_gwp(include_stage_D=False, stages_filter=stages_filter_a1a3)
        except TypeError:
            wmean_total_a1a3 = None
        _kv("Weighted-mean TOTAL (A1-A3):", _fmt(wmean_total_a1a3))

    print()
    print("Done.")

if __name__ == "__main__":
    main()
