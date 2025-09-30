#!/usr/bin/env python3
import pandas as pd
from typing import List

# =======================
# USER SETTINGS
# =======================
INPUT_CSV  = r"data/lca_database/OBD_items.csv"
OUTPUT_CSV = r"temp/inventory_data/dissected/precast_concrete/OBD_precast_concrete.csv"

ENCODING = "cp1252"
DELIMITER = ";"

CATEGORY_COL = "Kategorie (en)"

# Match rows whose category path STARTS WITH this sequence (any deeper levels allowed)
NESTED_PREFIX: List[str] = [
    "Mineral building products",
    "Bricks, blocks and elements",
    "Precast concrete elements and goods"
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

    # Normalize the user-specified prefix too
    prefix = [normalize_part(p) for p in NESTED_PREFIX]

    # Split each row's category path into normalized parts
    paths = df[CATEGORY_COL].fillna("").astype(str).apply(split_hierarchy)

    # Keep rows whose path starts with the given prefix
    mask = paths.apply(lambda parts: len(parts) >= len(prefix) and parts[:len(prefix)] == prefix)

    filtered = df[mask]

    if filtered.empty:
        raise ValueError(
            f"No rows found with category path starting with {prefix} in column '{CATEGORY_COL}'."
        )

    filtered.to_csv(OUTPUT_CSV, index=False, encoding=ENCODING, sep=DELIMITER)
    print(f"Wrote {len(filtered)} rows with prefix {prefix} to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
