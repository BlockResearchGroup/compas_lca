from pathlib import Path

from dotenv import load_dotenv

from compas_lca.workflows.raw_extraction.oekobaudat.obd_extraction import extract_inventory_obd
from compas_lca.workflows.raw_extraction.oekobaudat.obd_helpers import _load_epd_parser_config
from compas_lca.workflows.raw_extraction.oekobaudat.obd_helpers import sync_trees
from compas_lca.workflows.raw_extraction.oekobaudat.obd_ingestion import extract_obd_payloads
from compas_lca.workflows.raw_extraction.oekobaudat.obd_smallify import filter_obd
from compas_lca.workflows.raw_extraction.oekobaudat.obd_update_remaining import update_obd_remaining

load_dotenv()

# ==================================================
# 1.) PREPROCESS ENVIRONMENTAL DATA
# ==================================================


def preprocess_obd(
    epd_parser_path: str | Path = "epd_parser.yaml",
    input_csv_path: str | Path = "data/lca_database/csv/OBD_remaining.csv",
) -> None:

    print("")
    print("Preprocessing EPDs...")

    # Load YAML config
    epd_parser_path = Path(epd_parser_path)
    config = _load_epd_parser_config(epd_parser_path)

    temporary_epd_dir = config.get("temporary_epd_dir")
    if not temporary_epd_dir:
        raise RuntimeError(f"'temporary_epd_dir' not found in {epd_parser_path}")

    epd_extracted_dir = Path(temporary_epd_dir)

    # Step 1: Filter OBD with chosen UUIDs
    output_csv_path = epd_extracted_dir / "01_preprocessed" / "OBD_preprocessed.csv"

    filter_obd(
        epd_parser_path=epd_parser_path,
        input_csv_path=input_csv_path,
        output_csv_path=output_csv_path,
    )
    print("")

    # Step 2: Ingest and extract EPDs
    payload_dir = epd_extracted_dir / "01_preprocessed" / "payloads"
    extract_obd_payloads(csv_path=output_csv_path, payload_dir=payload_dir)
    print("")


# ==================================================
# 2.) NORMALIZE ENVIRONMENTAL DATA WITH AI
# ==================================================
def extract_preprocessed_obd(
    epd_parser_path: str | Path = "epd_parser.yaml",
) -> None:
    print("")
    print("Extracting EPDs...")

    # Load config
    epd_parser_path = Path(epd_parser_path)
    config = _load_epd_parser_config(epd_parser_path)
    temporary_epd_dir = config.get("temporary_epd_dir")
    if not temporary_epd_dir:
        raise RuntimeError(f"'temporary_epd_dir' not found in {epd_parser_path}")
    temporary_dir = Path(temporary_epd_dir)

    # Define paths
    payload_dir = temporary_dir / "01_preprocessed" / "payloads"
    csv_path = temporary_dir / "01_preprocessed" / "OBD_preprocessed.csv"
    output_dir = temporary_dir / "02_extracted"

    # Extract and serialized EPDs
    extract_inventory_obd(payload_dir=payload_dir, csv_path=csv_path, write_json=True, output_dir=output_dir)
    print("")


# ==================================================
# 3.) ADD ENVIRONMENTAL DATA TO DATABASE
# ==================================================
def update_obd(
    epd_parser_path: str | Path = "epd_parser.yaml",
    epd_existing_dir: str | Path = "data/lca_database/oekobaudat_2024-I",
    input_csv_path: str | Path = "data/lca_database/csv/OBD_2024_I_A2.csv",
    output_csv_path: str | Path = "data/lca_database/csv/OBD_remaining.csv",
) -> None:
    print("")
    print(f"Updating LCA database: {epd_existing_dir}...")

    # Load working directory:
    epd_parser_path = Path(epd_parser_path)
    epd_existing_dir = Path(epd_existing_dir)

    config = _load_epd_parser_config(epd_parser_path)
    temporary_epd_dir = config.get("temporary_epd_dir")
    if not temporary_epd_dir:
        raise RuntimeError(f"'temporary_epd_dir' not found in {epd_parser_path}")
    temporary_dir = Path(temporary_epd_dir)
    epd_extracted_dir = temporary_dir / "02_extracted"
    log_output_dir = temporary_dir / "03_log"

    # Add extracted EPDs to existing OBD database directory
    sync_trees(epd_extracted_dir, epd_existing_dir, log_output_dir)

    # Update OBD_remaining.csv by removing rows whose UUIDs are present in the extracted EPDs
    update_obd_remaining(
        input_csv_path=input_csv_path,
        epd_directory=epd_existing_dir,
        output_csv_path=output_csv_path,
    )
