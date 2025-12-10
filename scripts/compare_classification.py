import csv
from pathlib import Path

# Define paths
gt_root = Path("temp/obd_ground_truth_samples")
test_root = Path("temp/OBD_samples")
output_csv = Path("temp/comparison_result.csv")

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


# Compare and generate results
results = []
for uuid, gt_path in sorted(gt_uuid_to_path.items()):
    if uuid in test_uuid_to_path:
        test_path = test_uuid_to_path[uuid]
        gt_parts = get_level_parts(gt_path)
        test_parts = get_level_parts(test_path)
        
        # Check match at each level
        level_1_match = check_level_match(gt_parts, test_parts, 1)
        full_match = check_level_match(gt_parts, test_parts, 2)
        # Level 2 match: only check level 2 accuracy when level 1 is already correct
        level_2_match = level_1_match and full_match
        
        results.append({
            "uuid": uuid,
            "level_1_match": str(level_1_match).lower(),
            "level_2_match": str(level_2_match).lower(),
            "full_match": str(full_match).lower(),
            "gt_path": str(gt_path),
            "test_path": str(test_path)
        })
    else:
        # UUID not found in test
        results.append({
            "uuid": uuid,
            "level_1_match": "not_found",
            "level_2_match": "not_found",
            "full_match": "not_found",
            "gt_path": str(gt_path),
            "test_path": "NOT_FOUND"
        })

# Write to CSV
fieldnames = ["uuid", "level_1_match", "level_2_match", "full_match", "gt_path", "test_path"]
with open(output_csv, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

# Calculate statistics
found_results = [r for r in results if r["test_path"] != "NOT_FOUND"]
not_found_count = sum(1 for r in results if r["test_path"] == "NOT_FOUND")

level_1_match_count = sum(1 for r in found_results if r["level_1_match"] == "true")
level_2_match_count = sum(1 for r in found_results if r["level_2_match"] == "true")
full_match_count = sum(1 for r in found_results if r["full_match"] == "true")

print(f"Comparison complete. Results written to: {output_csv}")
print(f"\n=== Summary ===")
print(f"Total UUIDs in ground truth: {len(gt_uuid_to_path)}")
print(f"Total UUIDs in test: {len(test_uuid_to_path)}")
print(f"UUIDs found in both: {len(found_results)}")
print(f"UUIDs not found in test: {not_found_count}")
print(f"\n=== Accuracy (for {len(found_results)} matched UUIDs) ===")
print(f"Level 1 match (e.g., material vs component): {level_1_match_count}/{len(found_results)} ({100*level_1_match_count/len(found_results):.1f}%)")
print(f"Level 2 match (level 2 accuracy when level 1 is correct): {level_2_match_count}/{level_1_match_count if level_1_match_count > 0 else 1} ({100*level_2_match_count/(level_1_match_count if level_1_match_count > 0 else 1):.1f}%)")
print(f"Full match (e.g., material/mineral): {full_match_count}/{len(found_results)} ({100*full_match_count/len(found_results):.1f}%)")
