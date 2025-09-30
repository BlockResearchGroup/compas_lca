#!/usr/bin/env python3
import csv
import json
import os
import sys
from typing import Dict, List, Any, TypedDict, Optional

# === USER SETTINGS ===
INPUT_PATH = r"temp/inventory_data/dissected/doors/OBD_doors.csv"
OUTPUT_PATH = r"temp/inventory_data/dissected/doors/steel_and_iron_taxonomy.json"
COLUMN_NAME = "Kategorie (en)"   # Column with the hierarchical path
ENCODING = "cp1252"              # Your CSV encoding
DELIMITER = ";"                  # Your CSV delimiter

# How do you want the final JSON formatted?
# - If False (recommended): keys are the plain category names, and each node has:
#       { "_count": <int>, "children": { ... } }
# - If True: keys become "Name (count)", children keep the same structure.
COUNT_IN_KEYS = False
# ======================

class Node(TypedDict, total=False):
    _count: int
    children: Dict[str, "Node"]

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

def ensure_node() -> Node:
    return {"_count": 0, "children": {}}

def insert_and_count(root: Node, parts: List[str]) -> None:
    """
    For each CSV row, walk the path and increment counts on every node along the path.
    """
    node = root
    for p in parts:
        # Descend/create child
        child = node["children"].get(p)
        if child is None:
            child = ensure_node()
            node["children"][p] = child
        # Increment the child's count (this node represents this category and all under it)
        child["_count"] += 1
        # Continue downwards
        node = child

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

def export_tree_plain_keys(node: Node) -> Dict[str, Any]:
    """
    Export with plain keys. Value for each category is a dict:
      { "_count": int, optionally "children": { ... } }
    """
    out: Dict[str, Any] = {}
    for name in sorted(node["children"].keys()):
        child = node["children"][name]
        child_dict: Dict[str, Any] = {"_count": int(child.get("_count", 0))}
        children_export = export_tree_plain_keys(child)
        if children_export:  # only add if not empty
            child_dict["children"] = children_export
        out[name] = child_dict
    return out

def export_tree_count_in_keys(node: Node) -> Dict[str, Any]:
    """
    Export with keys of the form "Name (count)" for readability.
    Value keeps _count and children (if any).
    """
    out: Dict[str, Any] = {}
    for name in sorted(node["children"].keys()):
        child = node["children"][name]
        count = int(child.get("_count", 0))
        display = f"{name} ({count})"
        child_dict: Dict[str, Any] = {"_count": count}
        children_export = export_tree_count_in_keys(child)
        if children_export:  # only add if not empty
            child_dict["children"] = children_export
        out[display] = child_dict
    return out


def main():
    if not os.path.exists(INPUT_PATH):
        sys.exit(f"Error: input file not found: {INPUT_PATH}")

    root: Node = ensure_node()

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
                insert_and_count(root, parts)

    # Choose export style
    if COUNT_IN_KEYS:
        taxonomy = export_tree_count_in_keys(root)
    else:
        taxonomy = export_tree_plain_keys(root)

    # Helpful metadata at the top level to explain what _count means
    wrapper = {
        "_meta": {
            "_count_definition": "Number of CSV rows that fall under the category (including all nested subcategories).",
            "column_source": COLUMN_NAME
        },
        "taxonomy": taxonomy
    }

    os.makedirs(os.path.dirname(os.path.abspath(OUTPUT_PATH)), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
        json.dump(wrapper, out, ensure_ascii=False, indent=2)

    print(f"Wrote taxonomy with counts to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
