"""
Functions to extract all fields for the InventoryItem class
"""

from pathlib import Path

import traceback

import pandas as pd

import json

from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from compas_lca.matching_core.core import MatchingCore

from compas_lca.inventory.inventory import Inventory
from compas_lca.inventory.item import InventoryItem
from compas_lca.inventory.indicator import Indicators
from compas_lca.inventory.metadata import ItemMetadata
from compas_lca.inventory.reference import ReferenceInfo

from compas_lca.inventory.indicator import Indicator
from compas_lca.inventory.indicator import Indicators

from compas_lca.inventory.constants import EN15978_STAGES

from compas_lca.workflows.extraction import extract_matching_core

from compas_lca.workflows.raw_extraction.oekobaudat.obd_ingestion import ingest_obd_item
from compas_lca.workflows.raw_extraction.oekobaudat.obd_readers import read_csv
from compas_lca.workflows.raw_extraction.oekobaudat.obd_readers import uuids_in_csv
from compas_lca.workflows.raw_extraction.oekobaudat.obd_readers import subset_for_uuid
from compas_lca.workflows.raw_extraction.oekobaudat.obd_readers import first_row_for_uuid
from compas_lca.workflows.raw_extraction.oekobaudat.obd_helpers import parse_num
from compas_lca.workflows.raw_extraction.oekobaudat.obd_helpers import safe_str
from compas_lca.workflows.raw_extraction.oekobaudat.obd_helpers import safe_int
from compas_lca.workflows.raw_extraction.oekobaudat.obd_helpers import COLUMN_MAP


# =======================================================
# Extract the matching core from an Oekobaudat entry
# =======================================================

def extract_matching_core_obd(uuid_series: pd.Series, output_dir: Optional[Path | str] = None) -> MatchingCore:
    """
    Parse the EPD payload and construct a MatchingCore.
    Implement source-specific logic here.
    """
    # Build the combined JSON (Series + URL parse) in-memory
    obd_item_payload = ingest_obd_item(uuid_series)

    # Get UUID
    uuid = safe_str(uuid_series["UUID"])

    # Get matching core from hybrid obd payolad (csv and URL based)
    core, meta = extract_matching_core(
        input_type = "inventory_item",
        input_data=obd_item_payload,
        input_format="json",
        write_output=True,  # will prolly be false
        write_meta=True,    # for now true, but might become false and aggregated meta is implemented later (in extract_inventory_obd)
        output_dir=output_dir / "matching_core",
        base_name=uuid
    )

    return core


# ============================================
# Extract Indicators from an Oekobaudat entry
# ============================================

def extract_indicators_obd(uuid_df: pd.DataFrame) -> Indicators:
    """
    Build an `Indicators` object from a DataFrame slice that already contains
    exactly one OBD entry (all rows share the same UUID).

    Rules:
    - Use COLUMN_MAP (plain + A2-specific columns).
    - Average values across scenarios by grouping only on (Modul).
    - Track stages that had multiple distinct Szenariobeschreibung.
    """

    present_cols = [c for c in COLUMN_MAP if c in uuid_df.columns]
    if not present_cols:
        return Indicators(indicators=[])

    # Scenario tracking
    scenarios_map: Optional[Dict[EN15978_STAGES, List[str]]] = None
    scen = (
        uuid_df.loc[:, ["Modul", "Szenariobeschreibung"]]
                .assign(
                    Modul=lambda d: d["Modul"].astype(str),
                    Szenariobeschreibung=lambda d: d["Szenariobeschreibung"].astype(str).str.strip(),
                )
                .groupby("Modul", dropna=False)["Szenariobeschreibung"]
                .agg(lambda s: sorted({x for x in s if x != ""}))
                .reset_index()
    )
    tmp: Dict[str, List[str]] = {}
    for _, r in scen.iterrows():
        stage = r["Modul"]
        lst = r["Szenariobeschreibung"]
        if isinstance(lst, list) and len(lst) > 1:
            tmp[stage] = lst
    if tmp:
        scenarios_map = {stage: descs for stage, descs in tmp.items()}  # type: ignore[assignment]

    # Narrow frame and numeric parse
    work = uuid_df.loc[:, ["Modul"] + present_cols].copy()
    for c in present_cols:
        work[c] = work[c].map(parse_num)

    # Average across scenarios (group only by Modul)
    agg_spec = {c: (lambda s: None if s.dropna().empty else float(s.dropna().mean()))
                for c in present_cols}
    grp = work.groupby("Modul", dropna=False, as_index=False).agg(agg_spec)

    # Build per-indicator stage dicts
    indicator_buckets: Dict[str, Dict[str, Optional[float]]] = {}
    for _, row in grp.iterrows():
        stage_key = row["Modul"]
        for csv_col in present_cols:
            obd_name = COLUMN_MAP[csv_col]  # canonical OBD indicator name
            val = row[csv_col]
            indicator_buckets.setdefault(obd_name, {})[stage_key] = None if val is None else float(val)

    # Convert to Indicators
    indicators: List[Indicator] = []
    for ind_name, stages_dict in indicator_buckets.items():
        # Skip if everything is None
        if all(v is None for v in stages_dict.values()):
            continue

        # Cast keys to EN15978_STAGES
        typed_stages: Dict[EN15978_STAGES, Optional[float]] = {  # type: ignore[assignment]
            stage: v for stage, v in stages_dict.items()
        }
        indicators.append(Indicator(name=ind_name, stages=typed_stages))  # type: ignore[arg-type]

    return Indicators(
        indicators=indicators,
        scenarios=scenarios_map if scenarios_map else None # Only include scenarios if any were aggregated
    )

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

    source = "OEKOBAUDAT 2024-I" # hardcoded; update as needed

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
        compliance = [
            part.strip().strip("'").strip('"')
            for part in raw_compliance.split("/")
            if part.strip()
        ] or None
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

# ==================================================================
# Extract and build an InventoryItem object from an Oekobaudat entry
# ==================================================================

def extract_inventory_item_obd(
    uuid_df: pd.DataFrame,
    uuid_series: pd.Series,
    *,
    write_json: bool = False,
    output_dir: Optional[Path | str] = None,
) -> InventoryItem:
    """
    Orchestrate extraction and assembly of an InventoryItem from a raw EPD payload.

    If write_json=True, serialize the InventoryItem to output_dir/{item.id}.json
    (placeholder filename). Change the naming scheme later as needed.
    """
    # Extract
    core = extract_matching_core_obd(uuid_series, output_dir)
    indicators = extract_indicators_obd(uuid_df)
    reference = extract_reference_obd(uuid_series)
    metadata = extract_metadata_obd(uuid_series)

    # Assemble
    item = InventoryItem(
        item_core=core,
        indicators=indicators,
        reference=reference,
        metadata=metadata,
    )

    # --- Optional write ---
    if write_json:
        if output_dir is None:
            raise ValueError("If write_json=True, you must provide an output_dir.")

        # Determine bucket from entry_type (handles Enum or str)
        entry = getattr(item.item_core, "entry_type", None)
        entry_str = (
            getattr(entry, "value", None)
            if hasattr(entry, "value")
            else (entry.name if hasattr(entry, "name") else str(entry))
        )
        entry_str = (entry_str or "").lower()
        if entry_str == "component":
            bucket = "component"
        elif entry_str == "material":
            bucket = "material"
        else:
            bucket = "other"

        out_dir = Path(output_dir) / bucket
        out_dir.mkdir(parents=True, exist_ok=True)

        uuid = uuid_series.get("UUID")
        out_path = out_dir / f"{uuid}.json"
        out_path.write_text(
            json.dumps(item.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return item

# ==========================================================
# Extract and build an Inventory object from Oekobaudat CSV
# ==========================================================


def extract_inventory_obd(
    csv_path: Union[str, Path],
    *,
    write_json: bool = False,                   # write one JSON per InventoryItem
    output_dir: Optional[Path | str] = None,    # where to write those JSON files
) -> Inventory:
    """
    Build an Inventory from an OBD CSV.

    - Reads the CSV
    - Iterates all UUIDs
    - Extracts an InventoryItem per UUID (and optionally writes each item as JSON)
    - Returns an Inventory containing all items
    """
    # Early validation
    if write_json and output_dir is None:
        raise ValueError("If write_json=True, you must provide an output_dir.")

    # Read csv -> DataFrame
    obd: pd.DataFrame = read_csv(csv_path)

    # Collect UUIDs in processing order
    uuids: List[str] = uuids_in_csv(obd)
    total = len(uuids)
    print(f"\nFound {total} UUID(s) in {csv_path}")

    # Extract items
    items: List[InventoryItem] = []
    written = 0
    for i, uuid in enumerate(uuids, start=1):
        print(f"\n[{i}/{total}] UUID={uuid} → building InventoryItem…")
        # subset per UUID
        try:
            uuid_df: pd.DataFrame = subset_for_uuid(obd, uuid)
            uuid_series: pd.Series = first_row_for_uuid(uuid_df, uuid)

            # extract one InventoryItem (this will also write its JSON if requested)
            item = extract_inventory_item_obd(
                uuid_df=uuid_df,
                uuid_series=uuid_series,
                write_json=write_json,
                output_dir=output_dir,
            )
            items.append(item)
            print(f"[OK] Wrote InventoryItem object for OBD-entry with uuid: {uuid}")
            written += 1

        except Exception as e:
            print(f"[FAIL] Couldn't write InventoryItem object for OBD-entry with uuid: {uuid}")
            traceback.print_exc()

    # Return Inventory wrapper
    return Inventory(items)