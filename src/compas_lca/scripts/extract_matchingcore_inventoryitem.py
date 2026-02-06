from pathlib import Path
from datetime import datetime
from typing import Optional
import csv
import time
from compas_lca.workflows.raw_extraction.oekobaudat.obd_extraction import extract_inventory_obd
from dotenv import load_dotenv

load_dotenv()


def load_misclassified_uuids(misclassified_csv: Path) -> list[str]:
    """
    Load UUIDs from a misclassified items CSV file.
    
    Parameters
    ----------
    misclassified_csv : Path
        Path to the CSV file containing misclassified items (exported from compare_classification.py).
    
    Returns
    -------
    list[str]
        List of UUIDs from the misclassified items.
    """
    uuids = []
    with open(misclassified_csv, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "uuid" in row and row["uuid"]:
                uuids.append(row["uuid"])
    return uuids


def main():
    # --- USER CONFIGURATION ---
    csv_path = "data/lca_database/OBD_samples.csv"  # path to your input CSV
    write_json = True                                      # whether to write JSON per InventoryItem
    output_dir = Path("temp/obd_extracted/tests/gemini_3_pro_preview")   # output directory for JSONs (only used if write_json=True)
    max_workers = 1                                        # parallel workers (1 = sequential, >1 = parallel)
    resume = True                                          # skip already processed UUIDs (resume from interruption)
    

    # misclassified_csv: Optional[Path] = Path("temp/misclassified_items.csv")
    misclassified_csv: Optional[Path] = None  

    # --- LOAD UUID FILTER (if misclassified_csv is set) ---
    uuid_filter: Optional[list[str]] = None
    if misclassified_csv is not None:
        if misclassified_csv.exists():
            uuid_filter = load_misclassified_uuids(misclassified_csv)
            print(f"Loaded {len(uuid_filter)} misclassified UUIDs from {misclassified_csv}")
        else:
            print(f"Warning: Misclassified CSV not found at {misclassified_csv}. Processing all items.")

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
        resume=resume,
        uuid_filter=uuid_filter,
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
