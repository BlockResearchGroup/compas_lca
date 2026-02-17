import json
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional

from compas_lca.helpers import load_config

# MAPS FOR APPROXIMATE DURATION AND COST ESTIMATION OF AI-BASED EXTRACTION (STEP 01b)
# STATUS: 16. February 2026
# THIS DATA IS BASED ON THE EXTRACTION OF A DIVERSE SET OF 200 DIFFERENT IFC ELEMENTS FROM 8 IFC MODELS USED FOR TESTING
# NOTE: Not so straight-forward to interpolate due to different required tokens depending on model / matching core branch.
# Therefore, the most accurate approximation is received from the test data.

pricing_table = {
    "gpt-5-mini": {"Duration/element [s]": 51.77, "Cost/element [$]": 0.0082},
    "gpt-5.2": {"Duration/element [s]": 4.45, "Cost/element [$]": 0.0253},
    "claude-opus-4-5": {"Duration/element [s]": 11.2, "Cost/element [$]": 0.0998},
    "claude-sonnet-4-5": {"Duration/element [s]": 11.5, "Cost/element [$]": 0.0597},
    "claude-haiku-4-5": {"Duration/element [s]": 4.3, "Cost/element [$]": 0.0205},
    "gemini-3-pro-preview": {"Duration/element [s]": 55.03, "Cost/element [$]": 0.0637},
    "gemini-3-flash-preview": {"Duration/element [s]": 19.73, "Cost/element [$]": 0.01274},
}


def _safe_mkdir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _load_object_type_index(path: Path) -> Dict[str, List[Dict[str, Any]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"object_type.json must be a dict, got: {type(data).__name__}")
    return data


def _pick_representatives(
    object_type_index: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, str]:
    """
    Returns mapping: object_type -> representative_eid
    (always takes first entry in the list).
    """
    reps: Dict[str, str] = {}
    for obj_type, items in object_type_index.items():
        if not items:
            continue
        first = items[0] or {}
        eid = first.get("eid")
        if isinstance(eid, str) and eid.strip():
            reps[obj_type] = eid.strip()
    return reps


def _copy_representation(
    eid: str,
    src_elements_dir: Path,
    dst_elements_dir: Path,
) -> Optional[str]:
    """
    Copy representative identified by eid from source elements buckets into destination.

    Returns the bucket used ("multi_layer" / "multi_material" / "single_material") or None if not found.
    """
    src_multi_layer = src_elements_dir / "multi_layer" / eid
    src_multi_material = src_elements_dir / "multi_material" / eid
    src_single = src_elements_dir / "single_material" / f"{eid}.json"

    # Prefer multi_layer -> multi_material -> single_material
    if src_multi_layer.is_dir():
        dst = dst_elements_dir / "multi_layer" / eid
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src_multi_layer, dst)
        return "multi_layer"

    if src_multi_material.is_dir():
        dst = dst_elements_dir / "multi_material" / eid
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src_multi_material, dst)
        return "multi_material"

    if src_single.is_file():
        dst = dst_elements_dir / "single_material" / f"{eid}.json"
        _safe_mkdir(dst.parent)
        shutil.copy2(src_single, dst)
        return "single_material"

    return None


def _write_cost_estimation(
    out_path: Path,
    copied: int,
    pricing_table: Dict[str, Dict[str, float]],
    selected_model: Optional[str] = None,
    currency: str = "USD",
) -> None:
    """
    Write a human-readable cost and duration estimate for the next extraction step.
    """
    lines: List[str] = []
    lines.append("AI-based extraction cost estimation")
    lines.append("=" * 40)
    lines.append(f"Representative elements: {copied}")
    if selected_model:
        lines.append(f"Configured model (config.yaml): {selected_model}")
    lines.append("")

    # Header
    lines.append(f"{'Model':28s} {'Total duration':>15s} {'Total cost':>15s}")
    lines.append(f"{'-'*28} {'-'*15:>15s} {'-'*15:>15s}")

    def _fmt_seconds(total_s: float) -> str:
        # show both seconds and a rough h:m:s where helpful
        s = int(round(total_s))
        h = s // 3600
        m = (s % 3600) // 60
        sec = s % 60
        if h > 0:
            return f"{h:d}h {m:02d}m {sec:02d}s"
        if m > 0:
            return f"{m:d}m {sec:02d}s"
        return f"{sec:d}s"

    def _fmt_money(x: float) -> str:
        # 4 decimals is usually enough at these scales; bump if tiny
        return f"{x:.4f}"

    # Rows (sorted for stable output)
    for model_name in sorted(pricing_table.keys()):
        per = pricing_table[model_name]
        dur_per = float(per.get("Duration/element [s]", 0.0))
        cost_per = float(per.get("Cost/element [$]", 0.0))

        total_dur = dur_per * copied
        total_cost = cost_per * copied

        marker = "  "
        if selected_model and model_name == selected_model:
            marker = "* "

        lines.append(
            f"{marker}{model_name:26s} {_fmt_seconds(total_dur):>15s} {_fmt_money(total_cost):>15s} {currency}"
        )

    lines.append("")
    lines.append("Notes")
    lines.append("-" * 5)
    lines.append("• Estimates are based on historical test data.")
    lines.append("• Actual duration/cost depends on prompts, token usage, and provider-side variability.")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def create_representatives(
    project_dir: Path,
    cfg: Dict[str, Any],
) -> None:

    """
    Step 02: select and copy unique representative elements for AI extraction.
    `project_dir` is the project root.
    `cfg` is optional; if omitted, defaults are used where possible.
    """
    project_dir = Path(project_dir)

    preprocessed_dir = project_dir / "01_processed"
    src_elements_dir = preprocessed_dir / "elements"
    src_metadata_dir = preprocessed_dir / "metadata"
    object_type_json = src_metadata_dir / "object_type.json"

    if not object_type_json.is_file():
        raise FileNotFoundError(f"Missing: {object_type_json}")

    print("")
    print("Selecting unique building elements for AI-based extraction...")

    reps_dir = project_dir / "02_representatives"
    reps_dir_elements = reps_dir / "elements"
    _safe_mkdir(reps_dir_elements / "multi_layer")
    _safe_mkdir(reps_dir_elements / "multi_material")
    _safe_mkdir(reps_dir_elements / "single_material")

    object_type_index = _load_object_type_index(object_type_json)
    representatives = _pick_representatives(object_type_index)

    copied = 0
    skipped = 0

    for obj_type, eid in representatives.items():
        bucket = _copy_representation(eid, src_elements_dir, reps_dir_elements)
        if bucket is None:
            skipped += 1
        else:
            copied += 1


    cost_report_path = reps_dir / "cost_estimation.txt"
    _write_cost_estimation(
        out_path=cost_report_path,
        copied=copied,
        pricing_table=pricing_table,
        selected_model=cfg.get("model"),
        currency=str(cfg.get("currency", "USD")),
    )

    print("")
    print(f"Unique representative elements required for AI-extraction: {copied}")
    print(f"Representatives stored in: {reps_dir_elements}")
    print(f"Cost estimation written to: {cost_report_path}")
    print("")