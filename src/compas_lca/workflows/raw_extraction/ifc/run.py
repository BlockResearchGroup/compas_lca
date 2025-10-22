from pathlib import Path
from compas_lca.workflows.raw_extraction.ifc.ifc_extraction import extract_ifc_model


def main():
    # === 1. Define your IFC file path here ===
    ifc_file = Path(r"data/ifc_model/Duplex_A_20110907.ifc")  # 👈 change this

    # === 2. Automatically build the output folder ===
    # e.g. "temp/MyModel" if IFC file is "model.ifc"
    output_dir = Path("temp") / ifc_file.stem

    # === 3. Run extraction ===
    print(f"Extracting from: {ifc_file}")
    print(f"Output directory: {output_dir}")

    extract_ifc_model(ifc_file, output_dir, exclude_none=False)

    print(f"✅ Done! JSON files written to: {output_dir / 'elements'}")

if __name__ == "__main__":
    main()
  