"""
Runner file for LCA model extraction.
"""

from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
from compas_lca.workflows.raw_extraction.ifc.ifc_extraction import extract_lca_model_ifc

# --- configuration ------------------------------------------------------------
input_dir = Path("temp/Duplex_A_20110907")   # directory with metadata/model.json + elements/
output_dir = Path("temp/Duplex_A_20110907_LcaModel_3")       # optional; set to None if you don’t want to write files
# ------------------------------------------------------------------------------

def main():
    """
    Run the LCA model extraction from a preprocessed IFC directory.
    """
    extract_lca_model_ifc(input_dir, output_dir)

if __name__ == "__main__":
    main()
