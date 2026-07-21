"""
Label-by-label comparison of matching_core attributes between ground truth and test samples.

This script compares each attribute in the matching_core field of JSON files,
reporting accuracy statistics for four scenarios:
- Overall: All matched UUIDs
- Level 1 correct: Only UUIDs where level 1 category matches (e.g., both "material")
- Level 2 correct: Only UUIDs where full path matches (e.g., both "material/mineral")
- Level 3 correct: Only UUIDs where level 3 type matches (e.g., both "lime" for mineral_type)
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any
from typing import Optional
from typing import Literal
from dataclasses import dataclass
import sys

from collections import Counter
import math
from compas_lca.matching_core.normalization import normalize_level3_value

from _eval_paths import parse_eval_args


# Define paths (data is not committed; see thesis/evaluation/README.md)
args = parse_eval_args("A", needs_out=True)
gt_root = Path(args.gt)
test_root = Path(args.test)

out_dir = Path(args.out) if args.out else test_root
out_dir.mkdir(parents=True, exist_ok=True)

summary_txt = out_dir / "summary.txt"
output_csv = out_dir / "comparison_label_by_label.csv"

CompareKind = Literal["string", "float", "list_str"]

AUTO_PASS_LEVEL1 = {"unknown"}
AUTO_PASS_LEVEL3_WHEN_LEVEL2 = {"unknown", "other"}

# Attributes to exclude from comparison
EXCLUDED_ATTRIBUTES = {
    "core_id",
    "thickness_source",
    "name",
}

# Patterns for classification fields to exclude (ending with _type)
EXCLUDED_SUFFIXES = ("_type",)



@dataclass(frozen=True)
class CompareRule:
    kind: CompareKind
    tol: float | None = None          # for float
    f1_threshold: float | None = None # optional, if you still want boolean correctness
    casefold: bool = True             # for string/list normalization
    strip: bool = True

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

DEFAULT_RULE = CompareRule(kind="string")  # safe fallback


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
    "window": "frame_type",
}

def norm(s: Optional[str]) -> Optional[str]:
    if not isinstance(s, str):
        return None
    s2 = s.strip().lower()
    return s2 if s2 else None

def norm_l3(x: Any) -> Optional[str]:
    if x is None:
        return None
    if isinstance(x, (list, dict, tuple, set)) and len(x) == 0:
        return None
    if isinstance(x, str):
        s = x.strip().lower()
        return s or None
    return None

def resolve_level3_raw(
    level2: Optional[str],
    facet_dict: dict,
    *,
    overrides=LEVEL3_KEY_OVERRIDES,
    allow_default: bool = True,
    allow_fallback_suffix: bool = False,
) -> Any:
    if not isinstance(facet_dict, dict):
        return None

    key_level2 = (level2 or "").strip().lower()

    # 1) Explicit override
    if key_level2 in overrides:
        key = overrides[key_level2]
        return facet_dict.get(key)

    # 2) Default convention
    if allow_default and key_level2:
        default_key = f"{key_level2}_type"
        if default_key in facet_dict:
            return facet_dict.get(default_key)

    # 3) Optional fallback
    if allow_fallback_suffix:
        for k, v in facet_dict.items():
            if isinstance(k, str) and k.endswith("_type"):
                return v

    return None

def extract_levels_script1_compatible(data: dict) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Returns (level1, level2, level3) in the same way Script 1 does.
    - level1: entry_type
    - level2: facet.material_type or facet.component_type
    - level3: resolved via LEVEL3_KEY_OVERRIDES and normalized with normalize_level3_value
    """
    if not isinstance(data, dict):
        return None, None, None

    facet = data.get("facet") or {}
    level1 = norm(data.get("entry_type"))

    level2 = None
    level3_raw = None

    if level1 == "material":
        level2 = norm(facet.get("material_type"))
        material_facet = facet.get("material_facet") or {}
        if level2:
            level3_raw = resolve_level3_raw(
                level2,
                material_facet,
                overrides=LEVEL3_KEY_OVERRIDES,
                allow_default=False,
                allow_fallback_suffix=False,
            )

    elif level1 == "component":
        level2 = norm(facet.get("component_type"))
        component_facet = facet.get("component_facet") or {}
        if level2:
            level3_raw = resolve_level3_raw(
                level2,
                component_facet,
                overrides=LEVEL3_KEY_OVERRIDES,
                allow_default=False,
                allow_fallback_suffix=False,
            )

    # Script 1 normalization
    level3 = normalize_level3_value(level2, level3_raw)

    return level1, level2, level3




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

def rule_for_key(attr_key: str) -> CompareRule:
    # exact override
    if attr_key in RULES_BY_KEY:
        return RULES_BY_KEY[attr_key]
    return DEFAULT_RULE



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

def f1_for_string_lists(gt_list: list[str] | None, test_list: list[str] | None, *, casefold=True, strip=True) -> float:
    if not gt_list and not test_list:
        return 1.0
    if not gt_list or not test_list:
        return 0.0

    gt_norm = [normalize_str(str(x), casefold=casefold, strip=strip) for x in gt_list]
    test_norm = [normalize_str(str(x), casefold=casefold, strip=strip) for x in test_list]

    # Choose set-based (unique) OR multiset-based (counts). Multiset is often safer.
    gt_c = Counter(gt_norm)
    test_c = Counter(test_norm)

    overlap = sum((gt_c & test_c).values())
    precision = overlap / sum(test_c.values()) if sum(test_c.values()) else 0.0
    recall = overlap / sum(gt_c.values()) if sum(gt_c.values()) else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)

def score_values(gt_value: Any, test_value: Any, rule: CompareRule) -> Optional[float]:
    # 1) missing–missing: IGNORE (do not count)
    if gt_value is None and test_value is None:
        return None

    # 2) GT missing but test present: PUNISH
    if gt_value is None and test_value is not None:
        return 0.0

    # 3) GT present but test missing: PUNISH
    if gt_value is not None and test_value is None:
        return 0.0

    # (Now both sides are present -> apply your existing rules)
    if rule.kind == "string":
        gt_s = normalize_str(str(gt_value), casefold=rule.casefold, strip=rule.strip)
        test_s = normalize_str(str(test_value), casefold=rule.casefold, strip=rule.strip)
        return 1.0 if gt_s == test_s else 0.0

    if rule.kind == "float":
        tol = rule.tol if rule.tol is not None else 0.0
        gt_f = safe_float(gt_value)
        test_f = safe_float(test_value)
        if gt_f is None or test_f is None:
            return 0.0
        return 1.0 if math.isfinite(gt_f) and math.isfinite(test_f) and abs(gt_f - test_f) <= tol else 0.0

    if rule.kind == "list_str":
        if not isinstance(gt_value, list) or not isinstance(test_value, list):
            return 0.0
        return f1_for_string_lists(gt_value, test_value, casefold=rule.casefold, strip=rule.strip)

    return 1.0 if gt_value == test_value else 0.0




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

    avg_accuracy = 100 * total_score / total_comparisons if total_comparisons > 0 else 0.0
    print(f"\n  {'AVERAGE SCORE':<{max_len}}  {avg_accuracy:>5.1f}% ({total_score:.2f}/{total_comparisons})")
    return avg_accuracy


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

file_score_sum_overall = 0.0
file_score_count_overall = 0

file_score_sum_l1 = 0.0
file_score_count_l1 = 0

file_score_sum_l2 = 0.0
file_score_count_l2 = 0

file_score_sum_l3 = 0.0
file_score_count_l3 = 0


# Track excluded attributes for reporting
excluded_attrs_found = set()

for uuid, gt_path in sorted(gt_uuid_to_path.items()):
    if uuid not in test_uuid_to_path:
        continue

    # Per-file accumulators (macro averaging)
    file_sum = 0.0
    file_n = 0

    file_sum_l1 = 0.0
    file_n_l1 = 0

    file_sum_l2 = 0.0
    file_n_l2 = 0

    file_sum_l3 = 0.0
    file_n_l3 = 0

    found_count += 1
    test_path = test_uuid_to_path[uuid]

    # Load JSON files
    gt_file = gt_root / gt_path
    test_file = test_root / test_path

    gt_matching_core = load_json(gt_file)
    test_matching_core = load_json(test_file)

    if gt_matching_core is None or test_matching_core is None:
        continue

    # --- JSON-based Level 1 / 2 / 3 matching (SCRIPT 1 LOGIC) ---
    gt_l1, gt_l2, gt_l3 = extract_levels_script1_compatible(gt_matching_core)
    test_l1, test_l2, test_l3 = extract_levels_script1_compatible(test_matching_core)

    # Level 1: normal equality (requires non-missing GT)
    level_1_match = (gt_l1 is not None and gt_l1 == test_l1)

    # Script 1 auto-pass logic
    if level_1_match and gt_l1 in AUTO_PASS_LEVEL1:
        level_2_match = True
        level_3_match = True
    else:
        # Level 2: normal equality (requires non-missing GT)
        level_2_match = (level_1_match and gt_l2 is not None and gt_l2 == test_l2)

        # If L2 is unknown/other AND matched => L3 auto-pass
        if level_2_match and gt_l2 in AUTO_PASS_LEVEL3_WHEN_LEVEL2:
            level_3_match = True
        else:
            # Level 3: missing==missing counts as match (Script 1 semantics)
            level_3_match = (level_2_match and norm_l3(gt_l3) == norm_l3(test_l3))


    # Update level match counts AFTER computing matches
    if level_1_match:
        level_1_match_count += 1
    if level_2_match:
        level_2_match_count += 1
    if level_3_match:
        level_3_match_count += 1

    # Flatten both structures for attribute-wise scoring
    gt_flat = flatten_dict(gt_matching_core)
    test_flat = flatten_dict(test_matching_core)

    # Compare each attribute in ground truth
    all_keys = set(gt_flat.keys()) | set(test_flat.keys())

    for attr_key in all_keys:
        if is_excluded(attr_key):
            excluded_attrs_found.add(attr_key)
            continue

        gt_value = gt_flat.get(attr_key)     # may be None or missing
        test_value = test_flat.get(attr_key) # may be None or missing

        rule = rule_for_key(attr_key)
        score = score_values(gt_value, test_value, rule)

        # IMPORTANT: skip missing–missing comparisons entirely
        if score is None:
            continue

        is_match = score == 1.0  # keeps your existing "match" semantics in CSV

        # Per-file scoring
        file_sum += score
        file_n += 1

        if level_1_match:
            file_sum_l1 += score
            file_n_l1 += 1
        if level_2_match:
            file_sum_l2 += score
            file_n_l2 += 1
        if level_3_match:
            file_sum_l3 += score
            file_n_l3 += 1

        # Detailed comparison row
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

        # Attribute stats (micro averages within each scenario)
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

    # Macro-average file score accumulation
    if file_n > 0:
        file_score_sum_overall += (file_sum / file_n)
        file_score_count_overall += 1

    if level_1_match and file_n_l1 > 0:
        file_score_sum_l1 += (file_sum_l1 / file_n_l1)
        file_score_count_l1 += 1

    if level_2_match and file_n_l2 > 0:
        file_score_sum_l2 += (file_sum_l2 / file_n_l2)
        file_score_count_l2 += 1

    if level_3_match and file_n_l3 > 0:
        file_score_sum_l3 += (file_sum_l3 / file_n_l3)
        file_score_count_l3 += 1

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
        print(f"\n=== Summary ===")
        print(f"Total UUIDs in ground truth: {len(gt_uuid_to_path)}")
        print(f"Total UUIDs in test: {len(test_uuid_to_path)}")
        print(f"UUIDs found in both: {found_count}")
        print(f"Level 1 correct: {level_1_match_count}")
        print(f"Level 2 correct: {level_2_match_count}")
        print(f"Level 3 correct: {level_3_match_count}")

        # Print excluded attributes
        print(f"\n=== Excluded Attributes ===")
        for attr in sorted(excluded_attrs_found):
            print(f"  - {attr}")

        # Print label-by-label statistics
        print(f"\n{'='*60}")
        print("=== Label-by-Label Accuracy ===")

        print_attr_stats("Overall", attr_stats["overall"], found_count)
        print_attr_stats("Level 1 Correct", attr_stats["level_1_correct"], level_1_match_count)
        print_attr_stats("Level 2 Correct", attr_stats["level_2_correct"], level_2_match_count)
        print_attr_stats("Level 3 Correct", attr_stats["level_3_correct"], level_3_match_count)

        # Print Macro Average
        print(f"\n=== Macro Average File Score ===")
        print(f"Overall:        {100 * file_score_sum_overall / max(file_score_count_overall,1):.1f}%")
        print(f"Level 1 correct:{100 * file_score_sum_l1 / max(file_score_count_l1,1):.1f}%")
        print(f"Level 2 correct:{100 * file_score_sum_l2 / max(file_score_count_l2,1):.1f}%")
        print(f"Level 3 correct:{100 * file_score_sum_l3 / max(file_score_count_l3,1):.1f}%")
    finally:
        sys.stdout = original_stdout