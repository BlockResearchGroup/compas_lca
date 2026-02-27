from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable, Set


def _iter_json_files(root: Path) -> Iterable[Path]:
    """Yield all .json files under root (recursive)."""
    yield from root.rglob("*.json")


def _collect_dataset_uuids(json_root: Path) -> Set[str]:
    """
    Scan all JSON files under json_root and collect values at:
      metadata.dataset_uuid

    Any JSON parse errors or missing keys are skipped.
    """
    uuids: Set[str] = set()

    for p in _iter_json_files(json_root):
        try:
            with p.open("r", encoding="utf-8") as f:
                obj = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue

        if not isinstance(obj, dict):
            continue

        metadata = obj.get("metadata")
        if not isinstance(metadata, dict):
            continue

        dataset_uuid = metadata.get("dataset_uuid")
        if isinstance(dataset_uuid, str) and dataset_uuid.strip():
            uuids.add(dataset_uuid.strip())

    return uuids


def update_obd_remaining(
    input_csv_path: str | Path = "data/lca_database/csv/OBD_2024_I_A2.csv",
    epd_directory: str | Path = "data/lca_database/oekobaudat_2024-I",
    output_csv_path: str | Path = "data/lca_database/csv/OBD_remaining.csv",
) -> None:
    """
    Copy input CSV to output CSV, deleting rows whose UUID (first column header 'UUID')
    matches any metadata.dataset_uuid found in JSON files under epd_directory.

    Notes:
    - Assumes the CSV delimiter is ';' (as in your example).
    - Preserves the header row.
    - Preserves original row order.
    """
    input_csv_path = Path(input_csv_path)
    epd_directory = Path(epd_directory)
    output_csv_path = Path(output_csv_path)

    dataset_uuids = _collect_dataset_uuids(epd_directory)

    with input_csv_path.open("r", encoding="latin-1", newline="") as fin:
        reader = csv.DictReader(fin, delimiter=";")
        if not reader.fieldnames:
            raise ValueError("Input CSV appears to have no header row.")

        uuid_col = "UUID"
        if uuid_col not in reader.fieldnames:
            raise ValueError(
                f"Input CSV header does not contain '{uuid_col}'. "
                f"Found columns: {reader.fieldnames}"
            )

        # Ensure output directory exists
        output_csv_path.parent.mkdir(parents=True, exist_ok=True)

        with output_csv_path.open("w", encoding="latin-1", newline="") as fout:
            writer = csv.DictWriter(fout, fieldnames=reader.fieldnames, delimiter=";")
            writer.writeheader()

            for row in reader:
                uuid_val = (row.get(uuid_col) or "").strip()
                if uuid_val and uuid_val in dataset_uuids:
                    continue
                writer.writerow(row)