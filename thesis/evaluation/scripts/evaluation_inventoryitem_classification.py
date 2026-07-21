import csv
import json
import sys
from collections import Counter
from collections import defaultdict
from pathlib import Path
from typing import Optional

from _eval_paths import parse_eval_args

from compas_lca.matching_core.normalization import normalize_level3_value

# Define paths (data is not committed; see thesis/evaluation/README.md)
args = parse_eval_args("B", needs_out=True)
gt_root = Path(args.gt)
test_root = Path(args.test)

out_dir = Path(args.out) if args.out else test_root
out_dir.mkdir(parents=True, exist_ok=True)

output_csv = out_dir / "comparison_result.csv"
misclassified_csv = out_dir / "misclassified_items.csv"
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


def load_level3_type(file_path: Path) -> Optional[str]:
    """
    Load a JSON file and extract the level 3 type from component_facet or material_facet.
    
    The level 3 type is found at:
    - For materials: item_core.facet.material_facet.{material_type}_type
    - For components: item_core.facet.component_facet.{component_type}_type
    """
    try:
        for encoding in ["utf-8", "utf-8-sig", "latin-1"]:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    data = json.load(f)
                    break
            except UnicodeDecodeError:
                continue
        else:
            return None
        
        item_core = data.get("item_core", {})
        facet = item_core.get("facet", {})
        
        # Determine if it's material or component based on which type field exists
        if "material_type" in facet:
            level2_type = facet.get("material_type")  # e.g., "mineral"
            material_facet = facet.get("material_facet", {})
            if level2_type and material_facet:
                raw = material_facet.get(f"{level2_type}_type")
                return normalize_level3_value(level2_type, raw)
        elif "component_type" in facet:
            level2_type = facet.get("component_type")  # e.g., "ceiling"
            component_facet = facet.get("component_facet", {})
            if level2_type and component_facet:
                raw = component_facet.get(f"{level2_type}_type")
                return normalize_level3_value(level2_type, raw)
        
        return None
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def check_level_match(gt_parts: list[str], test_parts: list[str], level: int) -> bool:
    """Check if the first `level` parts match between gt and test."""
    if len(gt_parts) < level or len(test_parts) < level:
        return False
    return gt_parts[:level] == test_parts[:level]


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
        fieldnames = ["uuid", "level_1_match", "level_2_match", "level_3_match", 
                      "full_match", "gt_path", "test_path", "gt_level3", "test_level3"]
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

        gt_parts = Path(row["gt_path"]).parts
        level2 = gt_parts[1] if len(gt_parts) > 1 else ""
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


# Compare and generate results
results = []
for uuid, gt_path in sorted(gt_uuid_to_path.items()):
    if uuid in test_uuid_to_path:
        test_path = test_uuid_to_path[uuid]
        gt_parts = get_level_parts(gt_path)
        test_parts = get_level_parts(test_path)
        
        # Check match at each level
        level_1_match = check_level_match(gt_parts, test_parts, 1)
        level_2_parts_match = check_level_match(gt_parts, test_parts, 2)
        # Level 2 match: only check level 2 accuracy when level 1 is already correct
        level_2_match = level_1_match and level_2_parts_match
        
        # Extract and compare level 3 (from JSON content)
        gt_level3 = load_level3_type(gt_root / gt_path)
        test_level3 = load_level3_type(test_root / test_path)
        level_3_values_match = gt_level3 == test_level3
        # Level 3 match: only check level 3 accuracy when level 2 is already correct
        level_3_match = level_2_match and level_3_values_match
        
        # Full match: level 3 is correct
        full_match = level_3_match
        
        results.append({
            "uuid": uuid,
            "level_1_match": str(level_1_match).lower(),
            "level_2_match": str(level_2_match).lower(),
            "level_3_match": str(level_3_match).lower(),
            "full_match": str(full_match).lower(),
            "gt_path": str(gt_path),
            "test_path": str(test_path),
            "gt_level3": str(gt_level3) if gt_level3 else "",
            "test_level3": str(test_level3) if test_level3 else ""
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
fieldnames = ["uuid", "level_1_match", "level_2_match", "level_3_match", "full_match", "gt_path", "test_path", "gt_level3", "test_level3"]
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
