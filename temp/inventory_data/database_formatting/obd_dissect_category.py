import pandas as pd

# =======================
# USER SETTINGS
# =======================
INPUT_CSV = r"data/lca_database/OBD_items.csv"
OUTPUT_CSV = r"temp/inventory_data/dissected/wood/OBD_wood.csv"

ENCODING = "cp1252" 
DELIMITER = ";" 

CATEGORY_COL = "Kategorie (en)"
TOP_CATEGORY = "Wood"
# =======================


def normalize_part(s: str) -> str:
    """Remove quotes and extra spaces from a category part."""
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in {"'", '"'}:
        s = s[1:-1]
    return s.strip()


def main():
    df = pd.read_csv(INPUT_CSV, encoding=ENCODING, delimiter=DELIMITER)

    if CATEGORY_COL not in df.columns:
        raise ValueError(
            f"Column '{CATEGORY_COL}' not found. Available columns: {df.columns.tolist()}"
        )

    # Normalize the category column
    categories = df[CATEGORY_COL].astype(str).str.strip()

    # Split on " / " and clean each part
    split_cats = categories.str.split(r"\s*/\s*")

    # Find rows where the first part (after cleaning quotes) == TOP_CATEGORY
    mask = split_cats.apply(lambda parts: normalize_part(parts[0]) == TOP_CATEGORY if parts else False)

    filtered = df[mask]

    if filtered.empty:
        raise ValueError(
            f"No rows found with top-level category '{TOP_CATEGORY}' in column '{CATEGORY_COL}'."
        )

    # Save filtered rows
    filtered.to_csv(OUTPUT_CSV, index=False, encoding=ENCODING, sep=DELIMITER)

    print(f"Wrote {len(filtered)} rows under '{TOP_CATEGORY}' to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()

