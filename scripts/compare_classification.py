import os
import csv
from pathlib import Path

# Define paths
gt_root = Path("/Users/lichen7/Github/compas_lca/temp/obd_ground_truth_samples")
test_root = Path("/Users/lichen7/Github/compas_lca/temp/OBD_samples")
output_csv = Path("/Users/lichen7/Github/compas_lca/temp/comparison_result.csv")

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

# Compare and generate results
results = []
for uuid, gt_path in sorted(gt_uuid_to_path.items()):
    if uuid in test_uuid_to_path:
        test_path = test_uuid_to_path[uuid]
        # Compare the category (parent directory path)
        gt_category = gt_path.parent
        test_category = test_path.parent
        correct = gt_category == test_category
        results.append({
            "uuid": uuid,
            "correct": str(correct).lower(),
            "gt_path": str(gt_path),
            "test_path": str(test_path)
        })
    else:
        # UUID not found in test
        results.append({
            "uuid": uuid,
            "correct": "false",
            "gt_path": str(gt_path),
            "test_path": "NOT_FOUND"
        })

# Write to CSV
with open(output_csv, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["uuid", "correct", "gt_path", "test_path"])
    writer.writeheader()
    writer.writerows(results)

print(f"Comparison complete. Results written to: {output_csv}")
print(f"Total UUIDs in ground truth: {len(gt_uuid_to_path)}")
print(f"Total UUIDs in test: {len(test_uuid_to_path)}")
print(f"UUIDs found in both: {sum(1 for r in results if r['test_path'] != 'NOT_FOUND')}")
print(f"Correct matches: {sum(1 for r in results if r['correct'] == 'true')}")
print(f"Incorrect matches: {sum(1 for r in results if r['correct'] == 'false' and r['test_path'] != 'NOT_FOUND')}")
print(f"Not found in test: {sum(1 for r in results if r['test_path'] == 'NOT_FOUND')}")
