import json
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import pandas as pd

from compas_lca.helpers import merge_llm_meta
from compas_lca.inventory.indicator import Indicator
from compas_lca.inventory.indicator import Indicators
from compas_lca.inventory.indicator import IndicatorScenario
from compas_lca.inventory.inventory import Inventory
from compas_lca.inventory.item import InventoryItem
from compas_lca.inventory.metadata import ItemMetadata
from compas_lca.inventory.reference import ReferenceInfo
from compas_lca.matching_core.core import MatchingCore
from compas_lca.workflows.extraction import extract_matching_core
from compas_lca.workflows.raw_extraction.oekobaudat.obd_helpers import COLUMN_MAP
from compas_lca.workflows.raw_extraction.oekobaudat.obd_helpers import infer_bucket
from compas_lca.workflows.raw_extraction.oekobaudat.obd_helpers import parse_num
from compas_lca.workflows.raw_extraction.oekobaudat.obd_helpers import read_payload
from compas_lca.workflows.raw_extraction.oekobaudat.obd_helpers import safe_int
from compas_lca.workflows.raw_extraction.oekobaudat.obd_helpers import safe_str
from compas_lca.workflows.raw_extraction.oekobaudat.obd_helpers import uuids_in_payload_dir
from compas_lca.workflows.raw_extraction.oekobaudat.obd_helpers import write_item
from compas_lca.workflows.raw_extraction.oekobaudat.obd_readers import first_row_for_uuid
from compas_lca.workflows.raw_extraction.oekobaudat.obd_readers import read_csv
from compas_lca.workflows.raw_extraction.oekobaudat.obd_readers import subset_for_uuid
from compas_lca.workflows.raw_extraction.oekobaudat.obd_readers import uuids_in_csv

# =======================================================
# Helper: Scan output directory for existing UUIDs
# =======================================================


def _scan_existing_uuids(base_dir: Path) -> set:
    """
    Recursively scan the output directory for existing JSON files.
    Returns a set of UUIDs (extracted from filenames like {uuid}.json).
    """
    existing = set()
    if not base_dir.exists():
        return existing

    for json_file in base_dir.rglob("*.json"):
        # Skip metadata files
        if json_file.name == "llm_metadata.json":
            continue
        # UUID is the filename without extension
        uuid = json_file.stem
        existing.add(uuid)

    return existing


# =======================================================
# Extract the matching core from an Oekobaudat entry
# =======================================================


def extract_matching_core_from_payload(obd_item_payload: Dict[str, Any]) -> Tuple[MatchingCore, dict]:
    core, meta = extract_matching_core(
        input_type="inventory_item",
        input_data=obd_item_payload,
        input_format="json",
    )
    return core, meta


# ============================================
# Extract Indicators from an Oekobaudat entry
# ============================================


def extract_indicators_obd(uuid_df: pd.DataFrame) -> Indicators:
    """
    Build an `Indicators` object from rows for a single UUID.
    Keeps all scenarios per stage (no averaging).
    Expects columns:
      - 'Modul' (stage), 'Szenario' (scenario code, optional),
        'Szenariobeschreibung' (scenario description, optional),
        plus indicator columns defined in COLUMN_MAP.

    Special handling:
      - If 'Szenario' equals 'Standard scenario' (case-insensitive), ignore the scenario code
        and the (often very long) description by setting both to None.
    """

    present_cols = [c for c in COLUMN_MAP if c in uuid_df.columns]
    if not present_cols:
        return Indicators(indicators=[])

    # Normalize key fields
    df = uuid_df.copy()
    df["Modul"] = df["Modul"].astype(str).str.strip()

    if "Szenario" in df.columns:
        df["Szenario"] = df["Szenario"].astype(str).str.strip().replace({"": None})
    else:
        df["Szenario"] = None

    if "Szenariobeschreibung" in df.columns:
        df["Szenariobeschreibung"] = df["Szenariobeschreibung"].astype(str).str.strip().replace({"": None})
    else:
        df["Szenariobeschreibung"] = None

    # --- Edge case: drop "Standard scenario" code/description entirely ---
    if "Szenario" in df.columns:
        std_mask = df["Szenario"].fillna("").str.strip().str.casefold().eq("standard scenario")
        df.loc[std_mask, "Szenario"] = None
        df.loc[std_mask, "Szenariobeschreibung"] = None

    # Parse numeric indicators
    for c in present_cols:
        df[c] = df[c].map(parse_num)

    # Build: indicator_name -> stage -> list[IndicatorScenario]
    buckets: Dict[str, Dict[str, List[IndicatorScenario]]] = {}

    for _, row in df.iterrows():
        stage = row["Modul"]
        scen_code = row.get("Szenario")
        scen_desc = row.get("Szenariobeschreibung")

        for csv_col in present_cols:
            obd_name = COLUMN_MAP[csv_col]  # canonical indicator name
            val = row[csv_col]
            if obd_name not in buckets:
                buckets[obd_name] = {}
            if stage not in buckets[obd_name]:
                buckets[obd_name][stage] = []
            buckets[obd_name][stage].append(
                IndicatorScenario(
                    code=scen_code,
                    description=scen_desc,
                    value=None if val is None else float(val),
                )
            )

    # Build scenario summary (ignore None codes, includes "Standard scenario" which we nulled)
    scenario_summary: Dict[str, List[str]] = {}
    for stage in sorted(set(df["Modul"].tolist())):
        codes = sorted({c for c in df.loc[df["Modul"] == stage, "Szenario"].tolist() if c})
        if len(codes) > 1:
            scenario_summary[stage] = codes

    indicators: List[Indicator] = []
    for ind_name, stage_map in buckets.items():
        indicators.append(Indicator(name=ind_name, stages=stage_map))  # type: ignore[arg-type]

    return Indicators(indicators=indicators, scenarios=scenario_summary or None)


# ===============================================================================================
# Extract Reference Quantities (Bezugsgroesse) and unit (Bezugseinheit) from an Oekobaudat entry
# ===============================================================================================


def extract_reference_obd(uuid_series: pd.Series) -> ReferenceInfo:
    """
    Extract the declared reference information from a per-UUID OBD series.

    This function reads the declared reference size and unit
    (``Bezugsgroesse`` and ``Bezugseinheit``) from the first row of the
    dataframe, builds a validated :class:`ReferenceInfo` object.

    Parameters
    ----------
    uuid_series : pandas.Series
        First row of a slice of the OBD dataset containing all rows for a single UUID.

    Returns
    -------
    ReferenceInfo
        A validated reference information object containing ``size`` and ``unit``.
    """

    size = safe_int(uuid_series["Bezugsgroesse"])
    unit = safe_str(uuid_series["Bezugseinheit"])

    return ReferenceInfo(size=size, unit=unit)


# =======================================================
# Extract data for EnvDataSource from an Oekobaudat entry
# =======================================================


def extract_metadata_obd(uuid_series: pd.Series) -> ItemMetadata:
    """
    Return the ItemMetadata for provenance/metadata (e.g., 'Ökobau.dat', 'KBOB', publisher, version).
    Empty cells are mapped to None (consistent with Optional fields in the model).
    """

    source = "OEKOBAUDAT 2024-I"  # hardcoded; update as needed

    # Extract from series
    uuid = safe_str(uuid_series.get("UUID"))
    url = safe_str(uuid_series.get("URL"))
    registration = safe_str(uuid_series.get("Registrierungsnummer"))
    location_code = safe_str(uuid_series.get("Laenderkennung"))
    ref_year = safe_int(uuid_series.get("Referenzjahr"))
    valid_until = safe_int(uuid_series.get("Gueltig bis"))
    owner = safe_str(uuid_series.get("Declaration owner"))

    # Parse compliance field (list of strings or None)
    raw_compliance = safe_str(uuid_series.get("Konformitaet"))
    if raw_compliance:
        compliance = [part.strip().strip("'").strip('"') for part in raw_compliance.split("/") if part.strip()] or None
    else:
        compliance = None

    return ItemMetadata(
        dataset_source=source,
        dataset_uuid=uuid,
        dataset_url=url,
        registration_number=registration,
        location_code=location_code,
        reference_year=ref_year,
        valid_until=valid_until,
        dataset_owner=owner,
        compliance_system_name=compliance,
    )


# ==========================================================
# Extract and build an Inventory object from Oekobaudat CSV
# ==========================================================


def _process_single_uuid_from_payload(
    obd: pd.DataFrame,
    payload_dir: Path,
    uuid: str,
    index: int,
    total: int,
    write_json: bool,
    base_dir: Optional[Path],
) -> Tuple[int, Optional[InventoryItem], Optional[dict], Optional[str]]:
    print(f"\n[{index}/{total}] UUID={uuid} -> building InventoryItem (from payload)...")
    try:
        # load payload for LLM extraction
        obd_item_payload = read_payload(payload_dir, uuid)
        core, llm_meta = extract_matching_core_from_payload(obd_item_payload)

        # keep existing CSV-derived steps (minimal change)
        uuid_df: pd.DataFrame = subset_for_uuid(obd, uuid)
        uuid_series: pd.Series = first_row_for_uuid(uuid_df, uuid)

        indicators = extract_indicators_obd(uuid_df)
        metadata = extract_metadata_obd(uuid_series)
        reference = extract_reference_obd(uuid_series)

        item = InventoryItem(
            item_core=core,
            reference=reference,
            metadata=metadata,
            indicators=indicators,
        )

        if write_json and base_dir is not None:
            entry_type, subdir = infer_bucket(item)
            path = write_item(item, base_dir, entry_type, subdir)
            print(f"[OK] Wrote JSON -> {path.as_posix()}")
        else:
            print(f"[OK] Built InventoryItem object for uuid: {uuid}")

        return (index, item, llm_meta, None)

    except Exception:
        error_msg = traceback.format_exc()
        print(f"[FAIL] Couldn't process InventoryItem for uuid: {uuid}")
        traceback.print_exc()
        return (index, None, None, error_msg)


def extract_inventory_obd(
    payload_dir: Union[str, Path],
    csv_path: Union[str, Path],
    *,
    write_json: bool = True,  # write one JSON per InventoryItem
    output_dir: Optional[Path | str] = None,  # where to write those JSON files
    max_workers: int = 1,  # number of parallel workers (1 = sequential)
    resume: bool = True,  # skip already processed UUIDs
    uuid_filter: Optional[List[str]] = None,  # only process these UUIDs (if provided)
) -> Inventory:
    """
    Build an Inventory from an OBD CSV.

    - Reads the CSV
    - Iterates all UUIDs (optionally in parallel with max_workers > 1)
    - Extracts an InventoryItem per UUID
    - Optionally writes each item to JSON under a dynamic folder structure:
        {output_dir}/{entry_type}/{material_type|component_type}/{id}.json
      with 'unknown' fallback buckets.
    - Returns an Inventory containing all items.

    Parameters
    ----------
    payload_dir : str | Path
        Directory containing the extracted JSON payloads for each UUID.
    csv_path : str | Path
        Path to the input OBD CSV file.
    write_json : bool
        If True, write each InventoryItem to a JSON file.
    output_dir : Path | str | None
        Output directory for JSON files (required if write_json=True).
    max_workers : int
        Number of parallel workers for extraction. Default is 1 (sequential).
        Set to higher values (e.g., 5) to process multiple items concurrently.
    resume : bool
        If True (default), skip UUIDs that already have output files in output_dir.
        Useful for resuming interrupted extraction sessions.
    uuid_filter : list[str] | None
        If provided, only process UUIDs in this list. Useful for re-running
        extraction on a subset of items (e.g., misclassified items).
    """
    if write_json and output_dir is None:
        raise ValueError("If write_json=True, you must provide an output_dir.")

    payload_dir = Path(payload_dir)
    base_dir: Optional[Path] = Path(output_dir) if output_dir is not None else None

    all_llm_meta: dict[str, Any] = {}

    # read csv
    obd: pd.DataFrame = read_csv(csv_path)

    uuids = uuids_in_payload_dir(payload_dir)
    total_in_dir = len(uuids)
    print(f"\nFound {total_in_dir} payload JSON(s) in {payload_dir}")

    csv_uuid_set = set(uuids_in_csv(obd))
    payload_uuids = uuids_in_payload_dir(payload_dir)

    uuids = [u for u in payload_uuids if u in csv_uuid_set]
    missing = [u for u in payload_uuids if u not in csv_uuid_set]
    if missing:
        print(f"[WARN] {len(missing)} payload UUID(s) not found in CSV; skipping.")

    if uuid_filter is not None:
        s = set(uuid_filter)
        uuids = [u for u in uuids if u in s]
        print(f"UUID filter applied: {len(uuids)} UUID(s) match the filter.")

    if resume and base_dir is not None:
        existing_uuids = _scan_existing_uuids(base_dir)
        if existing_uuids:
            before = len(uuids)
            uuids = [u for u in uuids if u not in existing_uuids]
            print(f"Resume mode: skipping {before - len(uuids)} already processed UUID(s), {len(uuids)} remaining.")

    total = len(uuids)
    if total == 0:
        print("All UUIDs already processed. Nothing to do.")
        return Inventory([])

    indexed_uuids = [(i, uuid) for i, uuid in enumerate(uuids, start=1)]
    items: List[InventoryItem] = []
    results_by_index: Dict[int, Tuple[Optional[InventoryItem], Optional[dict]]] = {}

    if max_workers > 1:
        print(f"Running parallel extraction with {max_workers} workers...")
        lock = threading.Lock()
        completed_count = 0

        executor = ThreadPoolExecutor(max_workers=max_workers)
        try:
            futures = {executor.submit(_process_single_uuid_from_payload, obd, payload_dir, uuid, idx, total, write_json, base_dir): (idx, uuid) for idx, uuid in indexed_uuids}

            for future in as_completed(futures):
                idx, item, llm_meta, error = future.result()
                with lock:
                    completed_count += 1
                    if item is not None:
                        results_by_index[idx] = (item, llm_meta)
                    if llm_meta is not None:
                        all_llm_meta = merge_llm_meta(all_llm_meta, llm_meta)

            print(f"\nAll {completed_count}/{total} futures completed.")

        finally:
            executor.shutdown(wait=False, cancel_futures=True)
            print("Executor shutdown complete.")

        for idx in sorted(results_by_index.keys()):
            item, _ = results_by_index[idx]
            if item is not None:
                items.append(item)

    else:
        for idx, uuid in indexed_uuids:
            idx, item, llm_meta, error = _process_single_uuid_from_payload(obd, payload_dir, uuid, idx, total, write_json, base_dir)
            if item is not None:
                items.append(item)
            if llm_meta is not None:
                all_llm_meta = merge_llm_meta(all_llm_meta, llm_meta)

    if output_dir is not None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        meta_path = out / "llm_metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(all_llm_meta, f, indent=2)
        print(f"Aggregated LLM metadata saved to: {meta_path}")

    return Inventory(items)
