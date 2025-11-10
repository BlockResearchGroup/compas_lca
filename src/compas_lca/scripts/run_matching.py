from pathlib import Path
import json

# Import your existing matching function and helpers
from compas_lca.workflows.matching import score_items_to_element

# -------------------------------------------------------------------
# CONFIGURATION — specify here
# -------------------------------------------------------------------

# Path to the directory containing all InventoryItem JSONs
INVENTORY_DIR = Path("temp/obd_batch1_gpt5_organized/material")

# Path to one LcaElement JSON file
ELEMENT_FILE = Path("src/compas_lca/scripts/samples/79006056-3f25-41f8-b643-98aea10bf95b.json")

# How many top matches to keep
TOP_K = 10

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
        apply_overspec=False,
        include_explain=False,
    )

    # --- Print summary ---
    print("\n=== MATCH RESULTS ===")
    for core_matches in matched_element.matched_items or []:
        print(f"\nCore ID: {core_matches.core_id}")
        for m in core_matches.matches:
            print(f"  - {m.item_name}  →  score={m.score:.3f}")


    # --- Dump model ---
    out_path = Path("src/compas_lca/scripts/samples/test_out/test_metal.json")
    out_path.write_text(
        matched_element.model_dump_json(indent=2, exclude_none=True),
        encoding="utf-8"
    )


# -------------------------------------------------------------------
if __name__ == "__main__":
    main()
