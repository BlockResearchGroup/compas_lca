from pathlib import Path
import json

from compas_lca.workflows.matching import score_items_to_element

# -------------------------------------------------------------------
# CONFIGURATION — specify here
# -------------------------------------------------------------------

# Path to the directory containing all serialized InventoryItem JSONs
INVENTORY_DIR = Path("temp/obd_batch1_gpt5_organized/material")

# Path to input LcaElement JSON file

"""
# metal
ELEMENT_FILE = Path("src/compas_lca/scripts/samples/79006056-3f25-41f8-b643-98aea10bf95b.json")
"""
# multilayer
ELEMENT_FILE = Path("src/compas_lca/scripts/samples/3fc12c56-83df-40cc-b4e7-69a8ea8fbbdb.json")

# Path to output LcaElement JSON file
OUT_FILE = Path("src/compas_lca/scripts/samples/test_out/test_multilayer.json")

# How many top matches to keep
TOP_K = 2

# If the scoring should consider the overspec penalties found in compas_lca/match_rules.py (beta)
APPLY_OVERSPEC = False

# If the output should include the explanation of the score
INCLUDE_EXPLAIN = False

# If there should be a floor for items attached to the LcaElement
SCORE_THRESHOLD = 0.49

# -------------------------------------------------------------------
# LOADING HELPERS
# -------------------------------------------------------------------

def load_json_files_from_dir(directory: Path, pattern: str = "*.json"):
    """Yield each JSON object from a directory."""
    for file in directory.rglob(pattern):
        try:
            with file.open("r", encoding="utf-8") as f:
                yield json.load(f)
        except Exception as e:
            print(f"[WARN] Could not load {file.name}: {e}")

# -------------------------------------------------------------------
# MAIN RUNNER
# -------------------------------------------------------------------

def main():
    # --- Load the LcaElement ---
    with ELEMENT_FILE.open("r", encoding="utf-8") as f:
        element = json.load(f)

    # --- Load all candidate InventoryItems ---
    items = list(load_json_files_from_dir(INVENTORY_DIR))
    print(f"Loaded {len(items)} inventory items from {INVENTORY_DIR}")

    # --- Score ---
    matched_element = score_items_to_element(
        items=items,
        element=element,
        top_k=TOP_K,
        apply_overspec=APPLY_OVERSPEC,
        include_explain=INCLUDE_EXPLAIN,
        score_threshold=SCORE_THRESHOLD
    )

    # --- Print summary ---
    print("\n=== MATCH RESULTS ===")
    for core_matches in matched_element.matched_items or []:
        print(f"\nCore ID: {core_matches.core_id}")
        for m in core_matches.matches:
            print(f"  - {m.item_name}  →  score={m.score:.3f}")


    # --- Dump model ---
    out_path = OUT_FILE
    out_path.parent.mkdir(parents=True, exist_ok=True)  # ✅ ensure folder exists
    out_path.write_text(
        matched_element.model_dump_json(indent=2, exclude_none=True),
        encoding="utf-8"
    )


# -------------------------------------------------------------------
if __name__ == "__main__":
    main()
