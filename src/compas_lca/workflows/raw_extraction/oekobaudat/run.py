from pathlib import Path
from datetime import datetime
import time
from compas_lca.workflows.raw_extraction.oekobaudat.obd_extraction import extract_inventory_obd
from dotenv import load_dotenv

load_dotenv()


def main():
    # --- USER CONFIGURATION ---
    csv_path = "data/lca_database/OBD_samples.csv"  # path to your input CSV
    write_json = True                                      # whether to write JSON per InventoryItem
    output_dir = Path("temp/OBD_samples")                     # output directory for JSONs (only used if write_json=True)
    max_workers = 5                                        # parallel workers (1 = sequential, >1 = parallel)

    # --- START TIMER ---
    start_time = time.time()
    start_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\nStarting extraction at {start_str}\n")

    # --- RUN EXTRACTION ---
    inventory = extract_inventory_obd(
        csv_path=csv_path,
        write_json=write_json,
        output_dir=output_dir,
        max_workers=max_workers,
    )

    # --- END TIMER ---
    end_time = time.time()
    end_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elapsed = end_time - start_time
    minutes, seconds = divmod(elapsed, 60)

    # --- SUMMARY ---
    print("\nExtraction complete.\n")
    print(f"End time: {end_str}")
    print(f"Total runtime: {int(minutes)} min {seconds:.1f} sec")
    print(f"Extracted {len(inventory.root)} inventory items.")
    print(f"JSONs written to: {output_dir.resolve() if write_json else 'None'}\n")


if __name__ == "__main__":
    main()
