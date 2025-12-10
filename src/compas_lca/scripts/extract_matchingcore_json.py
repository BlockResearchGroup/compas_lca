"""
Runner file for extraction of a matching core object from a JSON file input
"""

from compas_lca.workflows.extraction import extract_matching_core
from compas_lca.helpers import load_json

from pathlib import Path

from dotenv import load_dotenv
load_dotenv()


input_dir = Path("temp/ifc_preprocessed/0_samples/Duplex")
output_dir = Path("temp/samples_extracted/duplex/elements/251209_gpt_5_1")


def main():

    print(f"extracting JSON files from directory: {input_dir}")
    print("")
    for element_json in input_dir.glob("*.json"):

        # Load JSON file
        element_data = load_json(element_json)

        # Get GlobalId
        meta = element_data.get("metadata")
        global_id = meta.get("global_id")

        # Extract matching core
        matching_core, llm_meta = extract_matching_core(
            input_type = "building_element",
            input_data = element_data,
            input_format = "json",
            )
        
        # Save matching core with global_id as filename
        print(f"saving matching core for element with global_id: {global_id}")
        (output_dir / f"{global_id}.json").write_text(matching_core.model_dump_json(indent=2), encoding="utf-8")

    print("")
    print("extraction complete!")

if __name__ == "__main__":
    main()