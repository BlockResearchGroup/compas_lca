#!/usr/bin/env python3
import pandas as pd

# =======================
# USER SETTINGS
# =======================
INPUT_CSV  = r"temp/inventory_data/dissected/mineral_building_products/plasters_mortar_screed/OBD_mortars_plasters.csv"
OUTPUT_CSV = r"temp/inventory_data/dissected/mineral_building_products/plasters_mortar_screed/OBD_mortars_plasters_sample.csv"

ENCODING = "cp1252"
DELIMITER = ";"

SAMPLE_SIZE = 25
RANDOM_SEED = 13
# =======================

def main():
    df = pd.read_csv(INPUT_CSV, encoding=ENCODING, delimiter=DELIMITER)

    replace = len(df) < SAMPLE_SIZE  # ensure we can always return SAMPLE_SIZE rows
    sample_df = df.sample(
        n=SAMPLE_SIZE,
        replace=replace,
        random_state=RANDOM_SEED
    )

    sample_df.to_csv(OUTPUT_CSV, index=False, encoding=ENCODING, sep=DELIMITER)

    note = " (with replacement)" if replace else ""
    print(f"Wrote {SAMPLE_SIZE} random rows{note} to {OUTPUT_CSV}")
    if RANDOM_SEED is not None:
        print(f"(Random seed = {RANDOM_SEED})")

if __name__ == "__main__":
    main()
