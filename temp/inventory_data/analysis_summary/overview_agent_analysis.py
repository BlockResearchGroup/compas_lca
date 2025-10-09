#!/usr/bin/env python3
import os
import json
from glob import glob
from typing import Dict, Set, TypedDict

class FieldAgg(TypedDict):
    count: int
    document_ids: Set[str]

# =======================
# USER SETTINGS
# =======================
INPUT_DIR = r"temp/matching_core_LLM_analysis/mineral_building_products/plasters_mortar_screed/llm_output"     # directory containing your JSON files
OUTPUT_JSON = r"temp/matching_core_LLM_analysis/mineral_building_products/plasters_mortar_screed/plasters_mortars_fields_overview.json"
RECURSIVE = True                      # set to False to only scan the top-level of INPUT_DIR
GLOB_PATTERN = "*.json"               # adjust if needed
# =======================


def iter_json_files(root: str, pattern: str, recursive: bool):
    if recursive:
        return glob(os.path.join(root, "**", pattern), recursive=True)
    else:
        return glob(os.path.join(root, pattern), recursive=False)


def safe_load_json(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Skipping {path}: {e}")
        return None


def main():
    files = iter_json_files(INPUT_DIR, GLOB_PATTERN, RECURSIVE)
    if not files:
        raise SystemExit(f"No JSON files found in: {INPUT_DIR}")

    # field_name -> { "count": int, "document_ids": set() }
    index: Dict[str, FieldAgg] = {}

    docs_seen = 0
    for path in files:
        data = safe_load_json(path)
        if not isinstance(data, dict):
            continue

        doc_id = data.get("document_id")
        if not doc_id:
            # Fallback: derive from filename (without extension)
            doc_id = os.path.splitext(os.path.basename(path))[0]

        fields = data.get("fields", [])
        if not isinstance(fields, list):
            continue

        docs_seen += 1

        # Collect unique field names within this single document
        names_in_this_doc: Set[str] = set()
        for f in fields:
            if not isinstance(f, dict):
                continue
            name = f.get("name")
            if not name:
                continue
            names_in_this_doc.add(str(name))

        # Update index (count per *document*, not per instance)
        for name in names_in_this_doc:
            slot = index.get(name)
            if slot is None:
                slot = {"count": 0, "document_ids": set()}
                index[name] = slot
            if doc_id not in slot["document_ids"]:
                slot["document_ids"].add(doc_id)
                slot["count"] += 1

    if not index:
        raise SystemExit("No fields found in the provided JSON files.")

    # Convert sets to sorted lists for JSON serialization
    sorted_items = sorted(
        index.items(),
        key=lambda kv: (-kv[1]["count"], kv[0].lower())
    )

    fields_out = {
        name: {
            "count": slot["count"],
            "document_ids": sorted(slot["document_ids"]),
        }
        for name, slot in sorted_items
    }

    out_payload = {
        "_meta": {
            "source_dir": os.path.abspath(INPUT_DIR),
            "total_documents_scanned": docs_seen,
            "total_unique_fields": len(fields_out),
            "note": "count = number of distinct documents containing this field name",
        },
        "fields": fields_out,
    }

    os.makedirs(os.path.dirname(os.path.abspath(OUTPUT_JSON)), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, ensure_ascii=False, indent=2)

    print(f"Wrote summary with {len(fields_out)} unique fields to: {OUTPUT_JSON}")
    print(f"Scanned {docs_seen} JSON file(s) from: {os.path.abspath(INPUT_DIR)}")


if __name__ == "__main__":
    main()
