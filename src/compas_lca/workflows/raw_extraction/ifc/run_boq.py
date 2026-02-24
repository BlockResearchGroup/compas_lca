from compas_lca.workflows.raw_extraction.ifc.ifc_boq import extract_lca_model_boq
from pathlib import Path

if __name__ == "__main__":
    # For testing: run the BOQ processing step standalone
    extract_lca_model_boq(
        input_csv_path = Path("temp/projects/duplex/01_processed/BoQ_01_dissected.csv"), 
        output_dir = Path("temp/projects/duplex/03_extracted")
        )