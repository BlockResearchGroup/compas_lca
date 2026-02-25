from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from compas_lca.helpers import load_json
from compas_lca.workflows.raw_extraction.ifc.ifc_extraction import extract_lca_element_ifc
from compas_lca.model.lca_element import LcaElement

INPUT_JSON = Path("temp/projects/duplex/02_representatives/elements/no_material/22492.json")
OUTPUT_JSON = Path("temp/a/output_lca_element.json")
OUTPUT_PATH = Path("temp/a")


def main():
    input_path = INPUT_JSON
    payload = load_json(input_path)

    llm_out, meta = extract_lca_element_ifc(
        input_json=payload,
        input_dir=None,
        mode="single",
        model_metadata = None,
        output_dir=OUTPUT_PATH
    )

    lca_element = LcaElement.model_validate(
    llm_out.model_dump()
    )

    output_path = OUTPUT_JSON 
    output_path.write_text(
        lca_element.model_dump_json(indent=2),
        encoding="utf-8"
    )

    print("Done.")
    print("Meta:", meta)


if __name__ == "__main__":
    main()