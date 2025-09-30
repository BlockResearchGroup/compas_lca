#!/usr/bin/env python3
import csv
import json
import os
import sys
from typing import Dict, List, Any

# === USER SETTINGS ===
INPUT_PATH = r"data/lca_database/OBD_items.csv"
OUTPUT_PATH = r"temp/inventory_data/database/OBD_taxonomy_simple.json"
COLUMN_NAME = "Kategorie (en)"   # Column with the hierarchical path
ENCODING = "cp1252"              # Your CSV encoding
DELIMITER = ";"                  # Your CSV delimiter
# ======================

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
    value = value.replace("\xa0", " ").strip()
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
            # else: literal slash
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

def insert_path(tree: Dict[str, Any], parts: List[str]) -> None:
    node = tree
    for p in parts:
        node = node.setdefault(p, {})

def find_column(fieldnames: List[str], requested: str) -> str:
    """Find requested column (case-insensitive, BOM-tolerant, with a fuzzy fallback)."""
    cleaned = [(fn or "").replace("\ufeff", "").strip() for fn in fieldnames]
    if requested in cleaned:
        return requested
    lc_map = {fn.lower(): fn for fn in cleaned}
    key = requested.lower()
    if key in lc_map:
        return lc_map[key]
    # fuzzy fallback for variants like "Kategorien (en)"
    for fn in cleaned:
        low = fn.lower()
        if "kategorie" in low and "(en" in low:
            return fn
    raise SystemExit(f"Error: column '{requested}' not found. Available columns: {cleaned}")

def dict_to_dict_or_list(node: Dict[str, Any]) -> Any:
    """Internal nodes => dict; leaves => sorted list of unique child names."""
    if not node:
        return []
    if all(not node[ch] for ch in node):
        return sorted(node.keys())
    out: Dict[str, Any] = {}
    for name in sorted(node.keys()):
        out[name] = dict_to_dict_or_list(node[name])
    return out

def main():
    if not os.path.exists(INPUT_PATH):
        sys.exit(f"Error: input file not found: {INPUT_PATH}")

    tree: Dict[str, Any] = {}

    with open(INPUT_PATH, "r", encoding=ENCODING, newline="") as f:
        reader = csv.DictReader(f, delimiter=DELIMITER)
        if not reader.fieldnames:
            sys.exit("Error: CSV appears to have no header row.")
        reader.fieldnames = [(fn or "").replace("\ufeff", "").strip() for fn in reader.fieldnames]
        col = find_column(reader.fieldnames, COLUMN_NAME)

        for row in reader:
            raw = row.get(col, "")
            if not raw:
                continue
            parts = split_hierarchy(str(raw))
            if parts:
                insert_path(tree, parts)

    taxonomy = dict_to_dict_or_list(tree)

    os.makedirs(os.path.dirname(os.path.abspath(OUTPUT_PATH)), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
        json.dump(taxonomy, out, ensure_ascii=False, indent=2)

    print(f"Wrote taxonomy to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
