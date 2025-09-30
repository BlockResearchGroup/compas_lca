import pandas as pd

# =======================
# USER SETTINGS
# =======================
INPUT_CSV = r"temp/inventory_data/dissected/doors/OBD_doors.csv"
OUTPUT_CSV = r"temp/inventory_data/dissected/doors/OBD_doors_sample.csv"

ENCODING = "cp1252" 
DELIMITER = ";" 

CATEGORY_COL = "Kategorie (en)"
SAMPLE_SIZE = 15
RANDOM_SEED = 69
# =======================


def main():

    df = pd.read_csv(INPUT_CSV, encoding=ENCODING, delimiter=DELIMITER)

    if CATEGORY_COL not in df.columns:
        raise ValueError(f"Column '{CATEGORY_COL}' not found. Available columns: {df.columns.tolist()}")

    per_category = df.groupby(CATEGORY_COL, group_keys=False).apply(
        lambda g: g.sample(1, random_state=RANDOM_SEED)
    )

    if len(per_category) < SAMPLE_SIZE:
        raise ValueError(
            f"Not enough unique categories ({len(per_category)} found) to sample {SAMPLE_SIZE} rows."
        )

    sample_df = per_category.sample(SAMPLE_SIZE, random_state=RANDOM_SEED)

    sample_df.to_csv(OUTPUT_CSV, index=False, encoding=ENCODING, sep=DELIMITER)

    print(f"Wrote {SAMPLE_SIZE} sampled rows (unique {CATEGORY_COL}) to {OUTPUT_CSV}")
    if RANDOM_SEED is not None:
        print(f"(Random seed = {RANDOM_SEED})")


if __name__ == "__main__":
    main()