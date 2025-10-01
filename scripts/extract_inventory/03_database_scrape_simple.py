import json
from pathlib import Path

# =======================
# USER SETTINGS
# =======================
INPUT_DIR = Path("temp/extraction/inventory/02_scrapes_json")
OUTPUT_DIR = Path("temp/extraction/inventory/03_scrapes_simple")
# =======================


KEEP_KEYS = {
    "Description",
    "Technical purpose of product or process",
    "Use advice for data set",
    "Classification number",
    "General comment on data set",
    "Technology description including background system"
}

def simplify_json_file(input_file: Path, output_file: Path):
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    simplified = {k: v for k, v in data.items() if k in KEEP_KEYS}

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(simplified, f, ensure_ascii=False, indent=2)

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for file in INPUT_DIR.glob("*.json"):
        out_file = OUTPUT_DIR / file.name
        simplify_json_file(file, out_file)

    print(f"Simplified JSON files saved in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
