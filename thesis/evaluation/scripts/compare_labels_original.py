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
from collections import defaultdict
from pathlib import Path
from typing import Optional
from typing import Any, Literal
from dataclasses import dataclass
from collections import Counter
import math

from _eval_paths import parse_eval_args

# Define paths (data is not committed; see thesis/evaluation/README.md)
args = parse_eval_args("B", needs_out=True)
gt_root = Path(args.gt)
test_root = Path(args.test)

out_dir = Path(args.out) if args.out else test_root
out_dir.mkdir(parents=True, exist_ok=True)

output_csv = out_dir / "comparison_label_by_label.csv"

# Attributes to exclude from comparison
EXCLUDED_ATTRIBUTES = {
    "core_id",
    "thickness_source",
    "name"
}

# Patterns for classification fields to exclude (ending with _type)
EXCLUDED_SUFFIXES = ("_type",)


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


def compare_values(gt_value, test_value):
    """
    Compare two values.
    - If BOTH are None => ignore (return None) so it does not affect numerator/denominator.
    - If GT is None and test is present => penalize (return False).
    - If GT is present and test is None => penalize (return False).
    - Otherwise compare values (lists order-independent).
    """
    # Missing–missing: IGNORE (do not count)
    if gt_value is None and test_value is None:
        return None

    # One missing: penalize
    if gt_value is None or test_value is None:
        return False

    # Lists: order-independent compare
    if isinstance(gt_value, list) and isinstance(test_value, list):
        try:
            return sorted(gt_value) == sorted(test_value)
        except TypeError:
            return gt_value == test_value

    return gt_value == test_value


def print_attr_stats(scenario_name: str, stats: dict, sample_count: int):
    """Print attribute statistics for a given scenario and return average accuracy."""
    print(f"\n--- {scenario_name} ({sample_count} samples) ---")
    
    if not stats:
        print("  No data available")
        return 0.0
    
    # Sort attributes for consistent output
    sorted_attrs = sorted(stats.keys())
    
    # Find max attribute name length for alignment
    max_len = max(len(attr) for attr in sorted_attrs) if sorted_attrs else 0
    
    # Track totals for average calculation
    total_matches = 0
    total_comparisons = 0
    
    for attr in sorted_attrs:
        data = stats[attr]
        total = data["total"]
        match = data["match"]
        total_matches += match
        total_comparisons += total
        if total > 0:
            pct = 100 * match / total
            print(f"  {attr:<{max_len}}  {pct:>5.1f}% ({match}/{total})")
    
    # Calculate and print average accuracy
    avg_accuracy = 100 * total_matches / total_comparisons if total_comparisons > 0 else 0.0
    print(f"\n  {'AVERAGE ACCURACY':<{max_len}}  {avg_accuracy:>5.1f}% ({total_matches}/{total_comparisons})")
    
    return avg_accuracy


# Compare and generate results
label_comparisons = []  # Store per-attribute comparisons

# Track attribute statistics for each scenario
# Structure: {scenario: {attribute: {"match": count, "total": count}}}
attr_stats = {
    "overall": defaultdict(lambda: {"match": 0, "total": 0}),
    "level_1_correct": defaultdict(lambda: {"match": 0, "total": 0}),
    "level_2_correct": defaultdict(lambda: {"match": 0, "total": 0}),
    "level_3_correct": defaultdict(lambda: {"match": 0, "total": 0}),
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

        cmp = compare_values(gt_value, test_value)

        # missing–missing => ignore completely (no CSV row, no denominator increment)
        if cmp is None:
            continue

        is_match = cmp  # True/False

        # Store detailed comparison (only for counted comparisons)
        label_comparisons.append({
            "uuid": uuid,
            "attribute": attr_key,
            "gt_value": str(gt_value),
            "test_value": str(test_value),
            "match": str(is_match).lower(),
            "level_1_correct": str(level_1_match).lower(),
            "level_2_correct": str(level_2_match).lower(),
            "level_3_correct": str(level_3_match).lower(),
        })

        # Update statistics for each scenario
        # Overall
        attr_stats["overall"][attr_key]["total"] += 1
        if is_match:
            attr_stats["overall"][attr_key]["match"] += 1

        # Level 1 correct
        if level_1_match:
            attr_stats["level_1_correct"][attr_key]["total"] += 1
            if is_match:
                attr_stats["level_1_correct"][attr_key]["match"] += 1

        # Level 2 correct
        if level_2_match:
            attr_stats["level_2_correct"][attr_key]["total"] += 1
            if is_match:
                attr_stats["level_2_correct"][attr_key]["match"] += 1

        # Level 3 correct
        if level_3_match:
            attr_stats["level_3_correct"][attr_key]["total"] += 1
            if is_match:
                attr_stats["level_3_correct"][attr_key]["match"] += 1


# Write label-by-label comparison to CSV
fieldnames = ["uuid", "attribute", "gt_value", "test_value", "match", "level_1_correct", "level_2_correct", "level_3_correct"]
with open(output_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(label_comparisons)

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
