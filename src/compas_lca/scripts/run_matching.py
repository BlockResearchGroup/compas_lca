from pathlib import Path
import json

from compas_lca.workflows.matching import score_items_to_element

# -------------------------------------------------------------------
# CONFIGURATION — specify here
# -------------------------------------------------------------------

INVENTORY_DIR = Path("temp/obd_ground_truth")

# Root directory of the extracted and serialized LcaElements
INPUT_ROOT = Path("temp/ifc_extracted/1072_HiLo_Model-Architecture")

# Root directory where matched LcaElements will be written
OUTPUT_ROOT = Path("temp/ifc_extracted_matched/1072_HiLo_Model-Architecture")  # <-- change if you like

# First-level subdirectories to process
ALLOWED_ELEMENT_DIRS = {
    "abstract_components",
    "layered_elements",
    "single_materials",
    "undefined_elements",
}

# How many top matches to keep
TOP_K = 100

# If the output should include the explanation of the score
INCLUDE_EXPLAIN = False

# If there should be a score-floor for items attached to the LcaElement
SCORE_THRESHOLD = 0.5

# -------------------------------------------------------------------
# LOADING HELPERS
# -------------------------------------------------------------------

def load_inventory_items(directory: Path, pattern: str = "*.json"):
    """Load all inventory items from directory (recursively), 
    skipping llm_metadata.json."""
    items = []
    for file in directory.rglob(pattern):

        # Skip the unwanted metadata file
        if file.name == "llm_metadata.json":
            continue

        try:
            with file.open("r", encoding="utf-8") as f:
                items.append(json.load(f))
        except Exception as e:
            print(f"[WARN] Could not load inventory file {file}: {e}")

    return items



def iter_element_files(root: Path):
    """
    Iterate over all element JSON files under INPUT_ROOT, 
    skipping metadata dir and llm_metadata.json, and only keeping
    files in the allowed first-level subdirectories.
    """
    for file in root.rglob("*.json"):
        # Skip the root-level llm_metadata.json explicitly
        if file.name == "llm_metadata.json" and file.parent == root:
            continue

        try:
            rel = file.relative_to(root)
        except ValueError:
            # File is not under root, ignore
            continue

        # We expect something like: <subdir>/.../file.json
        parts = rel.parts
        if not parts:
            continue

        first_level = parts[0]
        if first_level not in ALLOWED_ELEMENT_DIRS:
            # This will automatically skip "metadata" and any other unknown dir
            continue

        # At this point it's a valid element JSON
        try:
            with file.open("r", encoding="utf-8") as f:
                yield file, json.load(f)
        except Exception as e:
            print(f"[WARN] Could not load element file {file}: {e}")


# -------------------------------------------------------------------
# MAIN RUNNER
# -------------------------------------------------------------------

def main():
    # --- Load all candidate InventoryItems once ---
    items = load_inventory_items(INVENTORY_DIR)
    print(f"Loaded {len(items)} inventory items from {INVENTORY_DIR}")

    # --- Loop over all element JSON files in the allowed subdirectories ---
    for element_path, element in iter_element_files(INPUT_ROOT):
        print(f"\n=== Processing element file: {element_path} ===")

        matched_element = score_items_to_element(
            items=items,
            element=element,
            top_k=TOP_K,
            include_explain=INCLUDE_EXPLAIN,
            score_threshold=SCORE_THRESHOLD
        )

        # --- Print summary for this element ---
        print("\n--- MATCH RESULTS ---")
        for core_matches in matched_element.matched_items or []:
            print(f"\nCore ID: {core_matches.core_id}")
            for m in core_matches.matches:
                print(f"  - {m.item_name}  →  score={m.match_score:.3f}")

        # --- Build output path mirroring INPUT_ROOT structure ---
        relative = element_path.relative_to(INPUT_ROOT)
        out_path = OUTPUT_ROOT / relative
        out_path.parent.mkdir(parents=True, exist_ok=True)

        out_path.write_text(
            matched_element.model_dump_json(indent=2, exclude_none=True),
            encoding="utf-8"
        )
        print(f"→ Written matched element to {out_path}")


# -------------------------------------------------------------------
if __name__ == "__main__":
    main()
