import csv
import json
import sys
from collections import Counter
from collections import defaultdict
from pathlib import Path
from typing import Any
from typing import Optional
from typing import Tuple

from _eval_paths import parse_eval_args

from compas_lca.matching_core.normalization import normalize_level3_value

# Define paths (data is not committed; see thesis/evaluation/README.md)
args = parse_eval_args("A", needs_out=True)
gt_root = Path(args.gt)
test_root = Path(args.test)

out_dir = Path(args.out) if args.out else test_root
out_dir.mkdir(parents=True, exist_ok=True)

# Static filenames derived from out_dir
output_csv = out_dir / "comparison_result.csv"
misclassified_csv = out_dir / "misclassified_items4.csv"
confusion_report = out_dir / "misclassified_confusions.txt"
summary_txt = out_dir / "summary.txt"

class Tee:
    def __init__(self, *files):
        self.files = files

    def write(self, data):
        for f in self.files:
            f.write(data)
            f.flush()

    def flush(self):
        for f in self.files:
            f.flush()


AUTO_PASS_LEVEL1 = {"unknown"}
AUTO_PASS_LEVEL3_WHEN_LEVEL2 = {"unknown", "other"}
LEVEL3_KEY_OVERRIDES: dict[str, str] = {
    # materials
    "biobased": "biobased_type",
    "bituminous": "bituminous_type",
    "composite": "composite_type",
    "concrete": "concrete_type",
    "metallic": "metallic_type",
    "mineral": "mineral_type",
    "polymeric": "polymeric_type",
    "wood": "wood_type",

    # components
    "building_services": "building_service_type",
    "ceiling": "ceiling_type",
    "conveyor": "conveyor_type",
    "curtain_wall": "curtain_wall_type",
    "door": "door_type",
    "infill": "infill_type",
    "insulation_element": "insulation_element_type",
    "railing": "railing_type",
    "roof": "roof_type",
    "shading_device": "shading_device_type",
    "stairs": "stair_type",
    "window_fitting": "window_fitting_type",
    "window": "frame_type"
}

def resolve_level3_raw(
    level2: Optional[str],
    facet_dict: dict,
    *,
    overrides=LEVEL3_KEY_OVERRIDES,
    allow_default: bool = True,
    allow_fallback_suffix: bool = False,
) -> Any:
    """
    Resolve the raw level-3 value from a facet dict.

    Resolution order:
      1) overrides[level2] (explicit, one-to-one)
      2) default f"{level2}_type" (optional)
      3) fallback: first *_type key (optional)
    """
    if not isinstance(facet_dict, dict):
        return None

    key_level2 = (level2 or "").strip().lower()

    # 1) Explicit override (preferred)
    if key_level2 in overrides:
        key = overrides[key_level2]
        return facet_dict.get(key)

    # 2) Default convention
    if allow_default and key_level2:
        default_key = f"{key_level2}_type"
        if default_key in facet_dict:
            return facet_dict.get(default_key)

    # 3) Optional last-resort fallback
    if allow_fallback_suffix:
        for k, v in facet_dict.items():
            if isinstance(k, str) and k.endswith("_type"):
                return v

    return None

def norm_l3(x: Any) -> Optional[str]:
    # Treat None / empty containers as missing
    if x is None:
        return None
    if isinstance(x, (list, dict, tuple, set)) and len(x) == 0:
        return None
    if isinstance(x, str):
        s = x.strip().lower()
        return s or None
    # If you never expect non-strings here, treat everything else as missing
    return None

# Build a mapping of UUID -> relative path for ground truth
gt_uuid_to_path = {}
for json_file in gt_root.rglob("*.json"):
    uuid = json_file.stem  # filename without extension
    rel_path = json_file.relative_to(gt_root)
    gt_uuid_to_path[uuid] = rel_path

# Build a mapping of UUID -> relative path for test
test_uuid_to_path = {}
for json_file in test_root.rglob("*.json"):
    if json_file.name == "llm_metadata.json":
        continue  # explicitly ignore LLM metadata
    uuid = json_file.stem
    rel_path = json_file.relative_to(test_root)
    test_uuid_to_path[uuid] = rel_path


def load_json(file_path: Path) -> Optional[dict]:
    """Load JSON with a few fallback encodings."""
    for encoding in ["utf-8", "utf-8-sig", "latin-1"]:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return json.load(f)
        except UnicodeDecodeError:
            continue
        except (json.JSONDecodeError, FileNotFoundError):
            return None
    return None

def extract_levels(data: dict) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Returns (level1, level2, level3) from JSON content.

    Level 1: entry_type ("material" or "component")
    Level 2: facet.material_type or facet.component_type
    Level 3: facet.material_facet.{level2}_type or facet.component_facet.{level2}_type
    """
    if not isinstance(data, dict):
        return None, None, None

    level1 = data.get("entry_type")
    facet = data.get("facet") or data.get("item_core", {}).get("facet", {}) or {}

    # Normalize to strings (or None)
    level1 = str(level1).strip().lower() if level1 is not None else None

    level2 = None
    level3_raw = None

    if level1 == "material":
        level2_val = facet.get("material_type")
        level2 = str(level2_val).strip().lower() if level2_val is not None else None

        material_facet = facet.get("material_facet") or {}
        if level2:
            level3_raw = resolve_level3_raw(
                level2,
                material_facet,
                overrides=LEVEL3_KEY_OVERRIDES,
                allow_default=False,          # set True if you want fallback to f"{level2}_type"
                allow_fallback_suffix=False,  # keep strict
            )

    elif level1 == "component":
        level2_val = facet.get("component_type")
        level2 = str(level2_val).strip().lower() if level2_val is not None else None

        component_facet = facet.get("component_facet") or {}
        if level2:
            level3_raw = resolve_level3_raw(
                level2,
                component_facet,
                overrides=LEVEL3_KEY_OVERRIDES,
                allow_default=False,          # set True if you want fallback to f"{level2}_type"
                allow_fallback_suffix=False,  # keep strict
            )

    # If you want strict “identical string value” comparison, do NOT normalize here.
    # If you still want your domain normalization, keep the next line.
    level3 = normalize_level3_value(level2, level3_raw)

    # If you want strict string equality of the raw value, use this instead:
    # level3 = str(level3_raw).strip().lower() if level3_raw is not None else None

    return level1, level2, level3


def store_misclassified_items(
    results: list[dict],
    output_path: Path,
    level: Optional[int] = None
) -> list[dict]:
    """
    Store a list of all misclassified items to a CSV file.
    
    Parameters
    ----------
    results : list[dict]
        The comparison results from the classification comparison.
    output_path : Path
        The path where the misclassified items CSV will be saved.
    level : int, optional
        If specified, only items misclassified at this specific level are stored.
        If None, all items that don't have a full match are stored.
        Level can be 1, 2, or 3.
    
    Returns
    -------
    list[dict]
        The list of misclassified items.
    """
    misclassified = []
    
    for r in results:
        # Skip items not found in test
        if r["test_path"] == "NOT_FOUND":
            continue
        
        if level is None:
            # Store all items that don't have a full match
            if r["full_match"] != "true":
                misclassified.append(r)
        elif level == 1:
            # Store items that failed at level 1
            if r["level_1_match"] != "true":
                misclassified.append(r)
        elif level == 2:
            # Store items that passed level 1 but failed at level 2
            if r["level_1_match"] == "true" and r["level_2_match"] != "true":
                misclassified.append(r)
        elif level == 3:
            # Store items that passed level 2 but failed at level 3
            if r["level_2_match"] == "true" and r["level_3_match"] != "true":
                misclassified.append(r)
    
    # Write to CSV
    if misclassified:
        fieldnames = [
            "uuid",
            "level_1_match", "level_2_match", "level_3_match", "full_match",
            "gt_path", "test_path",
            "gt_level1", "test_level1",
            "gt_level2", "test_level2",
            "gt_level3", "test_level3",
        ]
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(misclassified)
    
    return misclassified


def summarize_confusions(misclassified: list[dict], output_path: Path) -> None:
    """
    Aggregate confusion counts for level-3 values (only where level 2 matched).
    Writes a short text report to `output_path`.
    """
    pair_counter: Counter[tuple[str, str]] = Counter()
    by_level2: defaultdict[str, Counter[tuple[str, str]]] = defaultdict(Counter)

    for row in misclassified:
        if row.get("test_path") == "NOT_FOUND":
            continue
        if row.get("level_2_match") != "true":
            continue

        level2 = (row.get("gt_level2") or "").strip().lower()
        gt = normalize_level3_value(level2, row.get("gt_level3"))
        test = normalize_level3_value(level2, row.get("test_level3"))
        gt_key = gt or "<missing>"
        test_key = test or "<missing>"

        pair_counter[(gt_key, test_key)] += 1
        by_level2[level2][(gt_key, test_key)] += 1

    lines = ["Level-3 confusions where level 2 matched:\n"]
    lines.append("Top overall confusions (gt -> test):")
    for (gt, test), count in pair_counter.most_common(20):
        lines.append(f"- {gt} -> {test}: {count}")

    lines.append("\nBy level-2 bucket:")
    for lvl2, counter in sorted(by_level2.items()):
        lines.append(f"[{lvl2}]")
        for (gt, test), count in counter.most_common(10):
            lines.append(f"  - {gt} -> {test}: {count}")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def norm(s: Optional[str]) -> Optional[str]:
    return s.strip().lower() if isinstance(s, str) and s.strip() != "" else None
# Compare and generate results
results = []
for uuid, gt_path in sorted(gt_uuid_to_path.items()):
    if uuid in test_uuid_to_path:
        test_path = test_uuid_to_path[uuid]
        gt_data = load_json(gt_root / gt_path)
        test_data = load_json(test_root / test_path)

        gt_l1, gt_l2, gt_l3 = extract_levels(gt_data or {})
        test_l1, test_l2, test_l3 = extract_levels(test_data or {})

        gt_l1n, test_l1n = norm(gt_l1), norm(test_l1)
        gt_l2n, test_l2n = norm(gt_l2), norm(test_l2)

        # Level 1: normal equality
        level_1_match = (gt_l1n is not None and gt_l1n == test_l1n)

        # Rule: entry_type "unknown" => L2 and L3 automatically correct if L1 matched
        if level_1_match and gt_l1n in AUTO_PASS_LEVEL1:
            level_2_match = True
            level_3_match = True
        else:
            # Level 2: normal equality
            level_2_match = (level_1_match and gt_l2n is not None and gt_l2n == test_l2n)

            # Rule: if L2 is "unknown" or "other" AND L2 matched => L3 automatically correct
            if level_2_match and gt_l2n in AUTO_PASS_LEVEL3_WHEN_LEVEL2:
                level_3_match = True
            else:
                gt_l3c = norm_l3(gt_l3)
                test_l3c = norm_l3(test_l3)
                # Level 3: normal equality
                # (Recommended: do NOT require gt_l3 is not None, so missing==missing counts as match)
                level_3_match = (level_2_match and gt_l3c == test_l3c)


        full_match = level_3_match
        
        results.append({
            "uuid": uuid,
            "level_1_match": str(level_1_match).lower(),
            "level_2_match": str(level_2_match).lower(),
            "level_3_match": str(level_3_match).lower(),
            "full_match": str(full_match).lower(),
            "gt_path": str(gt_path),
            "test_path": str(test_path),
            "gt_level3": gt_l3 or "",
            "test_level3": test_l3 or "",
            "gt_level1": gt_l1 or "",
            "test_level1": test_l1 or "",
            "gt_level2": gt_l2 or "",
            "test_level2": test_l2 or "",
        })
    else:
        # UUID not found in test
        results.append({
            "uuid": uuid,
            "level_1_match": "not_found",
            "level_2_match": "not_found",
            "level_3_match": "not_found",
            "full_match": "not_found",
            "gt_path": str(gt_path),
            "test_path": "NOT_FOUND",
            "gt_level3": "",
            "test_level3": ""
        })

# Write to CSV
fieldnames = [
    "uuid",
    "level_1_match", "level_2_match", "level_3_match", "full_match",
    "gt_path", "test_path",
    "gt_level1", "test_level1",
    "gt_level2", "test_level2",
    "gt_level3", "test_level3",
]
with open(output_csv, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

# Calculate statistics
found_results = [r for r in results if r["test_path"] != "NOT_FOUND"]
not_found_count = sum(1 for r in results if r["test_path"] == "NOT_FOUND")

level_1_match_count = sum(1 for r in found_results if r["level_1_match"] == "true")
level_2_match_count = sum(1 for r in found_results if r["level_2_match"] == "true")
level_3_match_count = sum(1 for r in found_results if r["level_3_match"] == "true")
full_match_count = sum(1 for r in found_results if r["full_match"] == "true")


misclassified: list[dict] = store_misclassified_items(results, misclassified_csv)
summarize_confusions(misclassified, confusion_report)

with open(summary_txt, "w", encoding="utf-8") as summary_file:
    original_stdout = sys.stdout
    sys.stdout = Tee(sys.stdout, summary_file)
    try:
        print(f"Comparison complete. Results written to: {output_csv}")
        print("\n=== Summary ===")
        print(f"Total UUIDs in ground truth: {len(gt_uuid_to_path)}")
        print(f"Total UUIDs in test: {len(test_uuid_to_path)}")
        print(f"UUIDs found in both: {len(found_results)}")
        print(f"UUIDs not found in test: {not_found_count}")
        print(f"\n=== Accuracy (for {len(found_results)} matched UUIDs) ===")
        print(f"Level 1 match (e.g., material vs component): {level_1_match_count}/{len(found_results)} ({100*level_1_match_count/len(found_results):.1f}%)")
        l1_den = level_1_match_count if level_1_match_count > 0 else 1
        l2_den = level_2_match_count if level_2_match_count > 0 else 1
        print(f"Level 2 match (level 2 accuracy when level 1 is correct): {level_2_match_count}/{l1_den} ({100*level_2_match_count/l1_den:.1f}%)")
        print(f"Level 3 match (level 3 accuracy when level 2 is correct): {level_3_match_count}/{l2_den} ({100*level_3_match_count/l2_den:.1f}%)")
        print(f"Full match (level 3 correct): {full_match_count}/{len(found_results)} ({100*full_match_count/len(found_results):.1f}%)")

        print("\n=== Misclassified Items ===")
        print(f"Total misclassified items: {len(misclassified)}")
        print(f"Misclassified items written to: {misclassified_csv}")
        print(f"Confusion summary written to: {confusion_report}")
    finally:
        sys.stdout = original_stdout