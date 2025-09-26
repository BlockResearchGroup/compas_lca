"""
Merges JSON files from two directories (same UUID filenames)
into a single flat JSON, saved in an output directory.
"""

import json
from pathlib import Path

# =======================
# USER SETTINGS
# =======================
DIR_A = Path("data/extraction/inventory/04_csv_data")
DIR_B = Path("data/extraction/inventory/03_scrapes_simple")
OUTPUT_DIR = Path("data/extraction/inventory/05_merged_input")
# =======================


def merge_json_files(file_a: Path, file_b: Path, output_file: Path):
    with open(file_a, "r", encoding="utf-8") as f:
        data_a = json.load(f)
    with open(file_b, "r", encoding="utf-8") as f:
        data_b = json.load(f)
    merged = {**data_a, **data_b}

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for file_a in DIR_A.glob("*.json"):
        uuid = file_a.stem
        file_b = DIR_B / f"{uuid}.json"

        if not file_b.exists():
            print(f" Skipping {uuid}: no matching file in {DIR_B}")
            continue

        output_file = OUTPUT_DIR / f"{uuid}.json"
        merge_json_files(file_a, file_b, output_file)
    print(f" Merged inventory data for LLM extraction in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
