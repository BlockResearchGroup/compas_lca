#!/usr/bin/env python3
import pandas as pd
from typing import List

# =======================
# USER SETTINGS
# =======================
INPUT_CSV  = r"data/lca_database/OBD_items.csv"
OUTPUT_CSV = r"temp/inventory_data/dissected/mineral_building_products/plasters_mortar_screed/OBD_mortars_plasters.csv"

ENCODING = "cp1252"
DELIMITER = ";"

CATEGORY_COL = "Kategorie (en)"

# Match rows whose category path STARTS WITH this sequence (any deeper levels allowed)
# Match rows whose category path STARTS WITH ANY of these sequences (any deeper levels allowed)
NESTED_PREFIXES: List[List[str]] = [
    ["Mineral building products", "Mortar and Concrete", "Adhesive and adhesive mortar"],
    ["Mineral building products", "Mortar and Concrete", "Mortar (masonry)"],
    ["Mineral building products", "Mortar and Concrete", "Renders and plasters"],
    ["Mineral building products", "Mortar and Concrete", "Screed dry mortar"],
    ["Mineral building products", "Bricks, blocks and elements", "Substrate"]
]
# =======================


def normalize_part(s: str) -> str:
    """Trim spaces, strip surrounding quotes, normalize NBSPs."""
    s = s.replace("\xa0", " ")
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in {"'", '"'}:
        s = s[1:-1]
    s = " ".join(s.split())
    return s


def split_hierarchy(value: str) -> List[str]:
    """
    Split on ' / ' only when OUTSIDE quotes.
    Examples:
      'A' / 'B/C' / 'D' -> ["A", "B/C", "D"]
      A / B / C         -> ["A", "B", "C"]
      'Digger/digging'  -> ["Digger/digging"]
    """
    value = (value or "").replace("\xa0", " ").strip()
    parts: List[str] = []
    buf: List[str] = []
    in_single = False
    in_double = False
    i = 0
    n = len(value)

    def prev_is_space(idx: int) -> bool:
        return idx >= 0 and value[idx].isspace()

    def next_is_space(idx: int) -> bool:
        return idx < n and value[idx].isspace()

    while i < n:
        ch = value[i]

        if ch == "'" and not in_double:
            in_single = not in_single
            buf.append(ch)
            i += 1
            continue

        if ch == '"' and not in_single:
            in_double = not in_double
            buf.append(ch)
            i += 1
            continue

        if ch == "/" and not in_single and not in_double:
            # treat as a separator ONLY if it's space-slash-space
            if prev_is_space(i - 1) and next_is_space(i + 1):
                token = "".join(buf).strip()
                if token:
                    parts.append(token)
                buf = []
                i += 1
                continue
        buf.append(ch)
        i += 1

    token = "".join(buf).strip()
    if token:
        parts.append(token)

    # clean each piece
    out = []
    for p in parts:
        q = normalize_part(p)
        if q:
            out.append(q)
    return out


def main():
    df = pd.read_csv(INPUT_CSV, encoding=ENCODING, delimiter=DELIMITER)

    if CATEGORY_COL not in df.columns:
        raise ValueError(
            f"Column '{CATEGORY_COL}' not found. Available columns: {df.columns.tolist()}"
        )

    # Normalize all user-specified prefixes
    prefixes = [[normalize_part(p) for p in pref] for pref in NESTED_PREFIXES]

    # Split each row's category path into normalized parts
    paths = df[CATEGORY_COL].fillna("").astype(str).apply(split_hierarchy)

    # Keep rows whose path starts with ANY of the prefixes
    def matches_any_prefix(parts: List[str]) -> bool:
        for pref in prefixes:
            if len(parts) >= len(pref) and parts[:len(pref)] == pref:
                return True
        return False

    mask = paths.apply(matches_any_prefix)
    filtered = df[mask]

    if filtered.empty:
        raise ValueError(
            f"No rows found with category path starting with any of {prefixes} in column '{CATEGORY_COL}'."
        )

    filtered.to_csv(OUTPUT_CSV, index=False, encoding=ENCODING, sep=DELIMITER)
    print(f"Wrote {len(filtered)} rows matching any prefix to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
