"""
Merges JSON files from three directories into one nested JSON file per UUID.
"""

import json
from pathlib import Path

# =======================
# USER SETTINGS
# =======================
DIR_CSV = Path("data/extraction/inventory/04_csv_data")
DIR_URL = Path("data/extraction/inventory/03_scrapes_simple")
DIR_LLM = Path("data/extraction/inventory/06_llm_output")
OUTPUT_DIR = Path("data/extraction/inventory/07_merged_output")
# =======================

def load_json(file: Path):
    if file.exists() and file.is_file():
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_files = {f.stem for f in DIR_CSV.glob("*.json")}
    all_files |= {f.stem for f in DIR_URL.glob("*.json")}

    all_files |= {
        f.stem for f in DIR_LLM.glob("*.json")
        if not f.name.endswith(".telemetry.json")
    }

    for uuid in all_files:
        csv_file = DIR_CSV / f"{uuid}.json"
        url_file = DIR_URL / f"{uuid}.json"
        llm_file = DIR_LLM / f"{uuid}.json"

        merged = {
            "CSV Extraction": load_json(csv_file),
            "URL Extraction": load_json(url_file),
            "LLM Extraction": load_json(llm_file),
        }

        out_file = OUTPUT_DIR / f"{uuid}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)

        print(f"Merged {uuid}.json → {out_file}")


if __name__ == "__main__":
    main()
