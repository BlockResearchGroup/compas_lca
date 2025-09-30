
import pandas as pd
import json
from pathlib import Path
from compas_lca.inventory.item import InventoryItemEPD

# =======================
# USER SETTINGS
# =======================
INPUT_CSV = Path("temp/inventory_data/dissected/precast_concrete/OBD_precast_concrete_sample.csv")
OUTPUT_DIR = Path("temp/inventory_data/dissected/precast_concrete/raw/04_csv_data")
ENCODING = "cp1252"   # or "utf-8-sig" depending on your file
DELIMITER = ";"       # or "," or "\t"

COLUMN_MAP = {
    "UUID": "uuid",
    "Name (en)": "dataset_name",
    "Kategorie (en)": "category",
    "Laenderkennung": "location_code",
    "Typ": "dataset_type",
    "Declaration owner": "dataset_owner",
    "Rohdichte (kg/m3)": "density",
    "Schichtdicke (m)": "layer_thickness",
}
# =======================

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_CSV, encoding=ENCODING, delimiter=DELIMITER)
    if "UUID" not in df.columns:
        raise ValueError(f"CSV is missing required column 'UUID'. Found columns: {df.columns.tolist()}")

    for _, row in df.iterrows():
        data = {}
        for col, attr in COLUMN_MAP.items():
            if col in row and pd.notna(row[col]):
                data[attr] = row[col]

        try:
            item = InventoryItemEPD(**data)
        except Exception as e:
            print(f"Skipping row with UUID={row.get('UUID')} due to validation error: {e}")
            continue

        out_path = OUTPUT_DIR / f"{item.uuid}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(item.dict(), f, ensure_ascii=False, indent=2)

    print(f"Saved metadata from Oekobaudat CSV file to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()