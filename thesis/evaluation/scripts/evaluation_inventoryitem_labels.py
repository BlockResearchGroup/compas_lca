"""
Label-by-label comparison of item_core attributes between ground truth and test samples.

This script compares each attribute in the item_core field of JSON files,
reporting accuracy statistics for four scenarios:
- Overall: All matched UUIDs
- Level 1 correct: Only UUIDs where level 1 category matches (e.g., both "material")
- Level 2 correct: Only UUIDs where full path matches (e.g., both "material/mineral")
- Level 3 correct: Only UUIDs where level 3 type matches (e.g., both "lime" for mineral_type)
"""
from __future__ import annotations

import csv
import json
import math
import sys
from collections import Counter
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Literal
from typing import Optional

from _eval_paths import parse_eval_args

# Define paths (data is not committed; see thesis/evaluation/README.md)
args = parse_eval_args("B", needs_out=True)
gt_root = Path(args.gt)
test_root = Path(args.test)

out_dir = Path(args.out) if args.out else test_root
out_dir.mkdir(parents=True, exist_ok=True)

summary_txt = out_dir / "summary.txt"
output_csv = out_dir / "comparison_label_by_label.csv"

# Attributes to exclude from comparison
EXCLUDED_ATTRIBUTES = {
    "core_id",
    "thickness_source",
    "name"
}

# Patterns for classification fields to exclude (ending with _type)
EXCLUDED_SUFFIXES = ("_type",)
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



CompareKind = Literal["string", "float", "list_str", "bool"]

@dataclass(frozen=True)
class CompareRule:
    kind: CompareKind
    tol: float | None = None
    casefold: bool = True
    strip: bool = True

# Optional: tune these for item_core keys you care about
RULES_BY_KEY: dict[str, CompareRule] = {

    # float:
    "thickness": CompareRule(kind="float", tol=0.01),
    "density": CompareRule(kind="float", tol=0.05),
    "facet.material_facet.yield_strength": CompareRule(kind="float", tol=0.05),
    "areal_density": CompareRule(kind="float", tol=0.01),
    "thermal_conductivity": CompareRule(kind="float", tol=0.01),
    "u_value": CompareRule(kind="float", tol=0.01),
    "facet.component_facet.door_height ": CompareRule(kind="float", tol=0.01),
    "facet.component_facet.door_width ": CompareRule(kind="float", tol=0.01),
    "facet.component_facet.window_height": CompareRule(kind="float", tol=0.01),
    "facet.component_facet.window_width ": CompareRule(kind="float", tol=0.01),


    # list_str:
    "facet.functional_types": CompareRule(kind="list_str"),
    "facet.application_areas": CompareRule(kind="list_str"),
    "facet.insulation_info": CompareRule(kind="list_str"),
    "facet.component_facet.door_operation": CompareRule(kind="list_str"),
    "facet.component_facet.window_operation": CompareRule(kind="list_str"),
    "facet.component_facet.safety_function": CompareRule(kind="list_str"),

    # bool:
    "fire_retardant": CompareRule(kind="bool"),
    "water_vapour_resistant": CompareRule(kind="bool"),
    "facet.material_facet.recycled_content": CompareRule(kind="bool"),
    "facet.material_facet.pre_stressed": CompareRule(kind="bool"),
    "facet.component_facet.door_automatization": CompareRule(kind="bool"),
    "facet.component_facet.industrial_door": CompareRule(kind="bool"),
    "facet.component_facet.acoustic_interlayer": CompareRule(kind="bool")

}

DEFAULT_RULE = CompareRule(kind="string")

def rule_for_key(attr_key: str) -> CompareRule:
    return RULES_BY_KEY.get(attr_key, DEFAULT_RULE)

def normalize_str(s: str, casefold: bool = True, strip: bool = True) -> str:
    if s is None:
        return s
    if strip:
        s = s.strip()
    if casefold:
        s = s.casefold()
    return s

def safe_float(x: Any) -> float | None:
    if x is None:
        return None
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return float(x)
    if isinstance(x, str):
        try:
            return float(x)
        except ValueError:
            return None
    return None

def safe_bool(x: Any) -> bool | None:
    if x is None:
        return None
    if isinstance(x, bool):
        return x
    if isinstance(x, str):
        s = x.strip().lower()
        if s in {"true", "1", "yes", "y"}:
            return True
        if s in {"false", "0", "no", "n"}:
            return False
    return None

def f1_for_string_lists(gt_list: list[Any] | None, test_list: list[Any] | None, *, casefold=True, strip=True) -> float:
    # NOTE: missing–missing handling is done outside in score_values
    if not gt_list and not test_list:
        return 1.0
    if not gt_list or not test_list:
        return 0.0

    gt_norm = [normalize_str(str(x), casefold=casefold, strip=strip) for x in gt_list]
    test_norm = [normalize_str(str(x), casefold=casefold, strip=strip) for x in test_list]

    gt_c = Counter(gt_norm)
    test_c = Counter(test_norm)

    overlap = sum((gt_c & test_c).values())
    precision = overlap / sum(test_c.values()) if sum(test_c.values()) else 0.0
    recall = overlap / sum(gt_c.values()) if sum(gt_c.values()) else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)

def score_values(gt_value: Any, test_value: Any, rule: CompareRule) -> float | None:
    """
    Returns:
      - None  => ignore (missing–missing)
      - float in [0,1] => score for this field
    Policy:
      - missing–missing => ignore
      - GT missing but test present => 0.0 (penalize)
      - GT present but test missing => 0.0 (penalize)
    """
    if gt_value is None and test_value is None:
        return None
    if gt_value is None or test_value is None:
        return 0.0

    if rule.kind == "bool":
        gb = safe_bool(gt_value)
        tb = safe_bool(test_value)
        if gb is None or tb is None:
            return 0.0
        return 1.0 if gb == tb else 0.0

    if rule.kind == "float":
        tol = rule.tol if rule.tol is not None else 0.0
        gf = safe_float(gt_value)
        tf = safe_float(test_value)
        if gf is None or tf is None or not (math.isfinite(gf) and math.isfinite(tf)):
            return 0.0
        return 1.0 if abs(gf - tf) <= tol else 0.0

    if rule.kind == "list_str":
        if not isinstance(gt_value, list) or not isinstance(test_value, list):
            return 0.0
        return f1_for_string_lists(gt_value, test_value, casefold=rule.casefold, strip=rule.strip)

    # default: string-ish exact match after normalization
    gt_s = normalize_str(str(gt_value), casefold=rule.casefold, strip=rule.strip)
    test_s = normalize_str(str(test_value), casefold=rule.casefold, strip=rule.strip)
    return 1.0 if gt_s == test_s else 0.0



def is_excluded(attr_key: str) -> bool:
    """Check if an attribute should be excluded from comparison."""
    # Check exact matches
    attr_name = attr_key.split(".")[-1]  # Get the last part of dot-notation
    if attr_name in EXCLUDED_ATTRIBUTES:
        return True
    # Check suffixes (classification fields)
    if attr_name.endswith(EXCLUDED_SUFFIXES):
        return True
    return False


# Build a mapping of UUID -> relative path for ground truth
gt_uuid_to_path = {}
for json_file in gt_root.rglob("*.json"):
    uuid = json_file.stem  # filename without extension
    rel_path = json_file.relative_to(gt_root)
    gt_uuid_to_path[uuid] = rel_path

# Build a mapping of UUID -> relative path for test
test_uuid_to_path = {}
for json_file in test_root.rglob("*.json"):
    uuid = json_file.stem
    rel_path = json_file.relative_to(test_root)
    test_uuid_to_path[uuid] = rel_path


def get_level_parts(path: Path) -> list[str]:
    """Get the directory parts of a path (excluding the filename)."""
    return list(path.parent.parts)


def check_level_match(gt_parts: list[str], test_parts: list[str], level: int) -> bool:
    """Check if the first `level` parts match between gt and test."""
    if len(gt_parts) < level or len(test_parts) < level:
        return False
    return gt_parts[:level] == test_parts[:level]


def extract_level3_type(item_core: Optional[dict]) -> Optional[str]:
    """
    Extract the level 3 type from item_core's component_facet or material_facet.
    
    The level 3 type is found at:
    - For materials: facet.material_facet.{material_type}_type
    - For components: facet.component_facet.{component_type}_type
    """
    if item_core is None:
        return None
    
    facet = item_core.get("facet", {})
    if not facet:
        return None
    
    # Determine if it's material or component based on which type field exists
    if "material_type" in facet:
        level2_type = facet.get("material_type")  # e.g., "mineral"
        material_facet = facet.get("material_facet", {})
        if level2_type and material_facet:
            # e.g., mineral_type -> "lime"
            return material_facet.get(f"{level2_type}_type")
    elif "component_type" in facet:
        level2_type = facet.get("component_type")  # e.g., "ceiling"
        component_facet = facet.get("component_facet", {})
        if level2_type and component_facet:
            # e.g., ceiling_type -> "cement_board"
            return component_facet.get(f"{level2_type}_type")
    
    return None


def flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """
    Recursively flatten a nested dictionary into dot-notation keys.
    
    Example:
        {"facet": {"material_type": "mineral"}} 
        -> {"facet.material_type": "mineral"}
    """
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep))
        else:
            items[new_key] = v
    return items


def load_item_core(file_path: Path) -> Optional[dict]:
    """Load a JSON file and return the item_core field."""
    try:
        # Try utf-8 first, then fall back to latin-1
        for encoding in ["utf-8", "utf-8-sig", "latin-1"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    data = json.load(f)
                    return data.get("item_core", {})
            except UnicodeDecodeError:
                continue
        print(f"Warning: Could not decode {file_path} with any encoding")
        return None
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Warning: Could not load {file_path}: {e}")
        return None


def print_attr_stats(scenario_name: str, stats: dict, sample_count: int):
    print(f"\n--- {scenario_name} ({sample_count} samples) ---")

    if not stats:
        print("  No data available")
        return 0.0

    sorted_attrs = sorted(stats.keys())
    max_len = max(len(attr) for attr in sorted_attrs) if sorted_attrs else 0

    total_score = 0.0
    total_comparisons = 0

    for attr in sorted_attrs:
        data = stats[attr]
        total = data["total"]
        sum_score = data["sum_score"]
        total_score += sum_score
        total_comparisons += total
        if total > 0:
            pct = 100 * sum_score / total
            print(f"  {attr:<{max_len}}  {pct:>5.1f}% ({sum_score:.2f}/{total})")

    avg = 100 * total_score / total_comparisons if total_comparisons > 0 else 0.0
    print(f"\n  {'AVERAGE SCORE':<{max_len}}  {avg:>5.1f}% ({total_score:.2f}/{total_comparisons})")
    return avg



# Compare and generate results
label_comparisons = []  # Store per-attribute comparisons

# Track attribute statistics for each scenario
# Structure: {scenario: {attribute: {"match": count, "total": count}}}
attr_stats = {
    "overall": defaultdict(lambda: {"sum_score": 0.0, "total": 0}),
    "level_1_correct": defaultdict(lambda: {"sum_score": 0.0, "total": 0}),
    "level_2_correct": defaultdict(lambda: {"sum_score": 0.0, "total": 0}),
    "level_3_correct": defaultdict(lambda: {"sum_score": 0.0, "total": 0}),
}

# Track counts for summary
found_count = 0
level_1_match_count = 0
level_2_match_count = 0
level_3_match_count = 0

# Track excluded attributes for reporting
excluded_attrs_found = set()

for uuid, gt_path in sorted(gt_uuid_to_path.items()):
    if uuid not in test_uuid_to_path:
        continue
    
    found_count += 1
    test_path = test_uuid_to_path[uuid]
    gt_parts = get_level_parts(gt_path)
    test_parts = get_level_parts(test_path)
    
    # Check match at each level
    level_1_match = check_level_match(gt_parts, test_parts, 1)
    full_match = check_level_match(gt_parts, test_parts, 2)
    # Level 2 match: only check level 2 accuracy when level 1 is already correct
    level_2_match = level_1_match and full_match
    
    if level_1_match:
        level_1_match_count += 1
    if level_2_match:
        level_2_match_count += 1
    
    # Load JSON files and compare item_core attributes
    gt_file = gt_root / gt_path
    test_file = test_root / test_path
    
    gt_item_core = load_item_core(gt_file)
    test_item_core = load_item_core(test_file)
    
    if gt_item_core is None or test_item_core is None:
        continue
    
    # Extract and compare level 3 (from JSON content)
    gt_level3 = extract_level3_type(gt_item_core)
    test_level3 = extract_level3_type(test_item_core)
    level_3_values_match = gt_level3 is not None and gt_level3 == test_level3
    # Level 3 match: only check level 3 accuracy when level 2 is already correct
    level_3_match = level_2_match and level_3_values_match
    
    if level_3_match:
        level_3_match_count += 1
    
    # Flatten both item_core structures
    gt_flat = flatten_dict(gt_item_core)
    test_flat = flatten_dict(test_item_core)
    
    # Compare each attribute over the UNION of keys so test-only fields can be penalized
    all_keys = set(gt_flat.keys()) | set(test_flat.keys())

    for attr_key in all_keys:
        # Exclusions apply to the key name (same logic as before)
        if is_excluded(attr_key):
            excluded_attrs_found.add(attr_key)
            continue

        gt_value = gt_flat.get(attr_key)     # may be None / missing
        test_value = test_flat.get(attr_key) # may be None / missing

        rule = rule_for_key(attr_key)
        score = score_values(gt_value, test_value, rule)

        # missing–missing => ignore completely (no CSV row, no denominator increment)
        if score is None:
            continue

        is_match = (score == 1.0)  # keep boolean flag if you want it

        # Store detailed comparison (only for counted comparisons)
        label_comparisons.append({
            "uuid": uuid,
            "attribute": attr_key,
            "gt_value": str(gt_value),
            "test_value": str(test_value),
            "score": f"{score:.4f}",
            "match": str(is_match).lower(),
            "level_1_correct": str(level_1_match).lower(),
            "level_2_correct": str(level_2_match).lower(),
            "level_3_correct": str(level_3_match).lower(),
        })

        # Update statistics for each scenario
        # Overall
        attr_stats["overall"][attr_key]["total"] += 1
        attr_stats["overall"][attr_key]["sum_score"] += score

        if level_1_match:
            attr_stats["level_1_correct"][attr_key]["total"] += 1
            attr_stats["level_1_correct"][attr_key]["sum_score"] += score

        if level_2_match:
            attr_stats["level_2_correct"][attr_key]["total"] += 1
            attr_stats["level_2_correct"][attr_key]["sum_score"] += score

        if level_3_match:
            attr_stats["level_3_correct"][attr_key]["total"] += 1
            attr_stats["level_3_correct"][attr_key]["sum_score"] += score



# Write label-by-label comparison to CSV
fieldnames = ["uuid", "attribute", "gt_value", "test_value", "score", "match",
              "level_1_correct", "level_2_correct", "level_3_correct"]

with open(output_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(label_comparisons)

with open(summary_txt, "w", encoding="utf-8") as summary_file:
    original_stdout = sys.stdout
    sys.stdout = Tee(sys.stdout, summary_file)
    try:
        # Print summary
        print(f"Label-by-label comparison complete. Results written to: {output_csv}")
        print("\n=== Summary ===")
        print(f"Total UUIDs in ground truth: {len(gt_uuid_to_path)}")
        print(f"Total UUIDs in test: {len(test_uuid_to_path)}")
        print(f"UUIDs found in both: {found_count}")
        print(f"Level 1 correct: {level_1_match_count}")
        print(f"Level 2 correct: {level_2_match_count}")
        print(f"Level 3 correct: {level_3_match_count}")

        # Print excluded attributes
        print("\n=== Excluded Attributes ===")
        for attr in sorted(excluded_attrs_found):
            print(f"  - {attr}")

        # Print label-by-label statistics
        print(f"\n{'='*60}")
        print("=== Label-by-Label Accuracy ===")

        print_attr_stats("Overall", attr_stats["overall"], found_count)
        print_attr_stats("Level 1 Correct", attr_stats["level_1_correct"], level_1_match_count)
        print_attr_stats("Level 2 Correct", attr_stats["level_2_correct"], level_2_match_count)
        print_attr_stats("Level 3 Correct", attr_stats["level_3_correct"], level_3_match_count)
    finally:
        sys.stdout = original_stdout