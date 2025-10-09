import re
import json
from pathlib import Path

# =======================
# USER SETTINGS
# =======================
INPUT_DIR = Path("temp/extraction/inventory/01_scrapes_txt")
OUTPUT_DIR = Path("temp/extraction/inventory/02_scrapes_json")
DROP_KEYS = {}
# =======================

def parse_table_text(text: str) -> dict:
    data = {}
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    current_key = None
    current_value = []

    for line in lines:
        match = re.match(r"^\|\s*(.*?)\s*\|\s*(.*?)\s*\|?$", line)
        if match:
            key, value = match.groups()
            if current_key:
                data[current_key] = " ".join(current_value).strip() or None
            current_key = key
            current_value = [value] if value else []
        else:
            if current_key:
                current_value.append(line)

    if current_key:
        data[current_key] = " ".join(current_value).strip() or None

    return data


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    txt_files = list(INPUT_DIR.glob("*.txt"))
    if not txt_files:
        return

    for txt_file in txt_files:
        text = txt_file.read_text(encoding="utf-8")
        parsed = parse_table_text(text)

        for k in list(parsed.keys()):
            if k in DROP_KEYS:
                parsed.pop(k)

        out_file = OUTPUT_DIR / (txt_file.stem + ".json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
    print(f"Processed {len(txt_files)} files from {INPUT_DIR}.")
    print(f"Saved in {OUTPUT_DIR}.")

if __name__ == "__main__":
    main()
