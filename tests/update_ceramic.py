import json
from pathlib import Path


TARGET_VALUES = {"earthenware", "stoneware", "porcelain"}
REPLACEMENT = "ceramic"


def update_file(filepath: Path) -> bool:
    """
    Updates mineral_type if it matches target values.
    Returns True if the file was modified, False otherwise.
    """
    try:
        with filepath.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        print(f"Skipping invalid JSON: {filepath}")
        return False

    try:
        mineral_type = (
            data["item_core"]["facet"]["material_facet"]["mineral_type"]
        )
    except KeyError:
        # Structure does not match expected schema
        return False

    if mineral_type in TARGET_VALUES:
        data["item_core"]["facet"]["material_facet"]["mineral_type"] = REPLACEMENT

        with filepath.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return True

    return False


def main():
    # 👇 SET YOUR DIRECTORY HERE
    DIRECTORY = Path(r"/Users/wuitee/Documents/BRG/compas_lca/temp/obd_ground_truth/material/mineral")

    if not DIRECTORY.exists() or not DIRECTORY.is_dir():
        print("Invalid directory path.")
        return

    updated_count = 0
    total_json_files = 0

    for filepath in DIRECTORY.rglob("*.json"):
        total_json_files += 1
        if update_file(filepath):
            print(f"Updated: {filepath}")
            updated_count += 1

    print("\n--- Summary ---")
    print(f"JSON files scanned: {total_json_files}")
    print(f"Files updated: {updated_count}")


if __name__ == "__main__":
    main()