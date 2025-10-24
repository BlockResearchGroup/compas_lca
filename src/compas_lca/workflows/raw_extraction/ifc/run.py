from pathlib import Path
from compas_lca.workflows.raw_extraction.ifc.ifc_extraction import extract_ifc_model


def main():
    # ====================================
    # ============ USER INPUT ============
    # ====================================

    ifc_file = Path(r"data/building_model/1072_HiLo_Model-Architecture.ifc")
    output_parent = "temp"
    exclude_none = False
    max_elements = 10

    # ====================================
    # ====================================
    # ====================================

    # Automatically build the output folder
    output_dir = Path(output_parent) / ifc_file.stem

    # === 3. Run extraction ===
    print(f"Extracting from: {ifc_file}")
    print(f"Output directory: {output_dir}")

    extract_ifc_model( 
        ifc_file, 
        output_dir, 
        exclude_none=exclude_none, 
        max_elements=max_elements
        )

    print(f"Done! JSON files written to: {output_dir / 'elements'}")

if __name__ == "__main__":
    main()
  