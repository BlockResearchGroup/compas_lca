"""
Runner file for extraction of a single pre-processed IfcBuildingElement into an LcaElement.
"""

from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
from compas_lca.helpers import load_json
from compas_lca.workflows.raw_extraction.ifc.ifc_extraction import extract_lca_element_ifc



# --- configuration ------------------------------------------------------------
input_path = Path("temp/ifc_preprocessed/test/representatives/3mpJQE9LnFVuDsMR9o0UnW.json")   # directory with metadata/model.json + elements/
output_dir = Path("temp/ifc_extracted/testsingle")       # optional; set to None if you don’t want to write files
# ------------------------------------------------------------------------------

def main():
    """
    Run the LCA model extraction from a preprocessed IFC directory.
    """
    input_json = load_json(input_path)
    element, llm_meta = extract_lca_element_ifc(
        input_json=input_json, 
        input_dir=None,
        mode="single",
        output_dir=output_dir
        )
    
if __name__ == "__main__":
    main()