from pathlib import Path

import traceback

from compas_lca.workflows.extraction import to_matching_core
from compas_lca.workflows.extraction import InputFormat

from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    # === EDIT THESE ARGUMENTS ==========================================
    input_dir = Path("temp/matching_core/in")
          # directory with input files
    output_dir = Path("temp/matching_core/out")    # directory where results are saved
    write_output = True
    write_meta = False
    input_format = InputFormat.json                   # options: InputFormat.json / .pdf / .txt
    # ===================================================================

    # Make sure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all files with the correct extension
    ext = {
        InputFormat.json: "*.json",
        InputFormat.pdf: "*.pdf",
        InputFormat.txt: "*.txt"
    }[input_format]

    input_files = list(input_dir.glob(ext))

    if not input_files:
        print(f"[WARN] No input files found in {input_dir} matching pattern '{ext}'")
        return

    print(f"[INFO] Found {len(input_files)} input files. Starting conversion...\n")

    # Iterate through all files
    for i, input_path in enumerate(input_files, start=1):
        print(f"[{i}/{len(input_files)}] Processing: {input_path.name}")
        try:
            matching_core = to_matching_core(
                input_path=input_path,
                output_dir=output_dir,
                write_output=write_output,
                write_meta=write_meta,
                input_format=input_format
            )
            print(f"    [OK] {matching_core.name} (ID: {matching_core.id})")
        except Exception as e:
            print(f"    [ERROR] Failed to process {input_path.name}: {e}")
            traceback.print_exc()

    print("\n====================================")
    print("[DONE] Batch conversion complete.")
    print(f"Results saved to: {output_dir.resolve()}")
    print("====================================")


if __name__ == "__main__":
    main()
