"""
Runner file for extraction of a matching core object from a JSON file input
"""

from compas_lca.workflows.extraction import extract_matching_core
from compas_lca.helpers import load_json

from pathlib import Path

import json

from typing import Any

from dotenv import load_dotenv
load_dotenv()

# element input
element_input_dir = Path("temp/ifc_preprocessed/0_samples/gemini_rerun/elements")
element_output_dir = Path("temp/ifc_extracted/0_samples/260107/260107_gemini_3_pro_preview/elements_rest")

# layer input
layer_input_dir = Path("temp/ifc_preprocessed/0_samples/gemini_rerun/layers")
layer_output_dir = Path("temp/ifc_extracted/0_samples/260107/260107_gemini_3_pro_preview/layers")
# metadata output
meta_output_dir = Path("temp/ifc_extracted/0_samples/260107/260107_gemini_3_pro_preview")

def merge_llm_meta(all_llm_meta: dict, llm_meta: dict) -> dict:
    """
    Merge numeric key-value pairs from `llm_meta` into `all_llm_meta`.
    Returns the updated `all_llm_meta` dictionary.
    """
    for key, value in llm_meta.items():
        if isinstance(value, (int, float)):
            all_llm_meta[key] = all_llm_meta.get(key, 0) + value
        else:
            all_llm_meta[key] = value
    return all_llm_meta


def extract_elements():

    all_llm_meta: dict[str, Any] = {}
    print(f"extracting ELEMENT JSON files from directory: {element_input_dir}")
    print("")
    for element_json in element_input_dir.glob("*.json"):

        # Load JSON file
        element_data = load_json(element_json)

        # Extract matching core
        matching_core, llm_meta = extract_matching_core(
            input_type="building_element",
            input_data=element_data,
            input_format="json",
        )

        # append individual llm metadata to all_llm_meta
        all_llm_meta = merge_llm_meta(all_llm_meta, llm_meta)  

        # Use input filename for output
        output_path = element_output_dir / element_json.name
        print(f"saving matching core to: {output_path}")

        output_path.write_text(
            matching_core.model_dump_json(indent=2),
            encoding="utf-8"
        )

    print("")
    print("ELEMENT extraction complete!")

    return all_llm_meta

def extract_layers():

    all_llm_meta: dict[str, Any] = {}
    print(f"extracting LAYER JSON files from directory: {layer_input_dir}")
    print("")
    for element_json in layer_input_dir.glob("*.json"):

        # Load JSON file
        element_data = load_json(element_json)

        # Extract matching core
        matching_core, llm_meta = extract_matching_core(
            input_type="layer",
            input_data=element_data,
            input_format="json",
            force_entry_type="material"
        )

        # append individual llm metadata to all_llm_meta
        all_llm_meta = merge_llm_meta(all_llm_meta, llm_meta)  

        # Use input filename for output
        output_path = layer_output_dir / element_json.name
        print(f"saving matching core to: {output_path}")

        output_path.write_text(
            matching_core.model_dump_json(indent=2),
            encoding="utf-8"
        )

    print("")
    print("LAYER extraction complete!")

    return all_llm_meta


def main():
    # Ensure output directories exist
    element_output_dir.mkdir(parents=True, exist_ok=True)
    layer_output_dir.mkdir(parents=True, exist_ok=True)
    meta_output_dir.mkdir(parents=True, exist_ok=True)

    element_llm_meta = extract_elements()
    layer_llm_meta = extract_layers()

    # Merge without mutating element_llm_meta
    total_llm_meta = merge_llm_meta(element_llm_meta.copy(), layer_llm_meta)

    meta_path = meta_output_dir / "llm_metadata.json"
    meta_path.write_text(json.dumps(total_llm_meta, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()