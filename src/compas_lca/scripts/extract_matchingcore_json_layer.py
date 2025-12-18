"""
Runner file for extraction of a matching core object from a JSON file input
"""

from compas_lca.workflows.extraction import extract_matching_core
from compas_lca.helpers import load_json

from pathlib import Path

from dotenv import load_dotenv
load_dotenv()


input_dir = Path("temp/ifc_preprocessed/0_samples/raw/zwhatt51/layers")
output_dir = Path("temp/ifc_extracted/0_samples/zwhatt51/layers/251209_gpt_5_1")


def main():

    print(f"extracting JSON files from directory: {input_dir}")
    print("")
    for element_json in input_dir.glob("*.json"):

        # Load JSON file
        element_data = load_json(element_json)

        # Extract matching core
        matching_core, llm_meta = extract_matching_core(
            input_type="layer",
            input_data=element_data,
            input_format="json",
            force_entry_type="material"
        )

        # Use input filename for output
        output_path = output_dir / element_json.name
        print(f"saving matching core to: {output_path}")

        output_path.write_text(
            matching_core.model_dump_json(indent=2),
            encoding="utf-8"
        )

    print("")
    print("extraction complete!")

if __name__ == "__main__":
    main()