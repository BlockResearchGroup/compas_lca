import os
import json


def collect_strength_classes(directory_path):
    strength_classes = set()

    # Iterate over all files in directory
    for filename in os.listdir(directory_path):
        if not filename.lower().endswith(".json"):
            continue

        file_path = os.path.join(directory_path, filename)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            strength_class = (
                data.get("item_core", {})
                    .get("facet", {})
                    .get("material_facet", {})
                    .get("strength_class")
            )

            if strength_class is not None:
                strength_classes.add(strength_class)

        except (json.JSONDecodeError, OSError) as e:
            print(f"Skipping file {filename}: {e}")

    return strength_classes


if __name__ == "__main__":
    # <<< SET YOUR DIRECTORY PATH HERE >>>
    directory = r"data/lca_database/oekobaudat_2024-I/material/concrete"

    results = collect_strength_classes(directory)

    print("Found strength_class values:")
    for value in sorted(results):
        print(value)