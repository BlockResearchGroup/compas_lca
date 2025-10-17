"""
Script for running "to_lca_material" on a chosen file
insert API key in .env to run
"""

from pathlib import Path

from compas_lca.workflows.extraction import to_lca_material
from compas_lca.workflows.extraction import InputFormat
from dotenv import load_dotenv

load_dotenv()

def main() -> None:
    # === EDIT THESE ARGUMENTS ==========================================
    input_path = Path("temp/lca_material_test/in/concrete.json")       # path to your input file
    output_dir = Path("temp/lca_material_test/out")                 # directory where results are saved
    write_output = True 
    write_meta = True                             # whether to write a metadata file
    input_format = InputFormat.json              # options: InputFormat.json / .pdf / .txt
    # ===================================================================

    # Run the pipeline
    lca_material = to_lca_material(
        input_path=input_path,
        output_dir=output_dir,
        write_output=write_output,
        write_meta=write_meta,
        input_format=input_format
    )

    # Print a short summary
    print("\n[OK] LCA material successfully assembled.")
    print(f"Name: {lca_material.name}")
    print(f"Type: {lca_material.facet.material_type}")
    print(f"ID:   {lca_material.id}")
    print("====================================")


if __name__ == "__main__":
    main()
