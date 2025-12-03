"""
Runner file for raw IFC extraction.
"""

from compas_lca.workflows.raw_extraction.ifc.ifc_processing import process_ifc_model
from pathlib import Path

ifc_dir = Path("data/input/ifc")    # takes the first IFC file in this directory as input
output_parent = Path("temp")        # saves output (preprocessed elements) into a directory in "temp" with identical file_name stem
exclude_none = False

def main():
    process_ifc_model(ifc_dir, output_parent, exclude_none)

if __name__ == "__main__":
    main()
