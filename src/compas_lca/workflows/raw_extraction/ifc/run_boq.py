from compas_lca.workflows.raw_extraction.ifc.ifc_processing import process_ifc_model_boq
from pathlib import Path

if __name__ == "__main__":
    # For testing: run the BOQ processing step standalone
    process_ifc_model_boq(Path("temp/projects/hilo"))