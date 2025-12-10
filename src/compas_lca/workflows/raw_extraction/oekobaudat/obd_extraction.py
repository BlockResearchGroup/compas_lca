from pathlib import Path

import traceback

import pandas as pd

import json

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from compas_lca.helpers import merge_llm_meta

from compas_lca.matching_core.core import MatchingCore

from compas_lca.inventory.inventory import Inventory
from compas_lca.inventory.item import InventoryItem
from compas_lca.inventory.metadata import ItemMetadata
from compas_lca.inventory.reference import ReferenceInfo
from compas_lca.inventory.indicator import Indicator
from compas_lca.inventory.indicator import IndicatorScenario
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
from compas_lca.workflows.raw_extraction.oekobaudat.obd_helpers import infer_bucket
from compas_lca.workflows.raw_extraction.oekobaudat.obd_helpers import write_item
from compas_lca.workflows.raw_extraction.oekobaudat.obd_helpers import COLUMN_MAP


# =======================================================
# Extract the matching core from an Oekobaudat entry
# =======================================================

def extract_matching_core_obd(uuid_series: pd.Series) -> MatchingCore:
    """
    Parse the EPD payload and construct a MatchingCore.
    Implement source-specific logic here.
    """
    # Build the combined JSON (Series + URL parse) in-memory
    obd_item_payload = ingest_obd_item(uuid_series)

    # Get matching core from hybrid obd payolad (csv and URL based)
    core, meta = extract_matching_core(
        input_type = "inventory_item",
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
        df["Szenariobeschreibung"] = (
            df["Szenariobeschreibung"].astype(str).str.strip().replace({"": None})
        )
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

    return Indicators(
        indicators=indicators,
        scenarios=scenario_summary or None  # <-- match your model field name
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
) -> InventoryItem:
    """
    Orchestrate extraction and assembly of an InventoryItem from a raw EPD payload.

    If write_json=True, serialize the InventoryItem to output_dir/{item.id}.json
    (placeholder filename). Change the naming scheme later as needed.
    """
    # Extract
    core, meta = extract_matching_core_obd(uuid_series)
    indicators = extract_indicators_obd(uuid_df)
    metadata = extract_metadata_obd(uuid_series)
    reference = extract_reference_obd(uuid_series)

    # Assemble
    item = InventoryItem(
        item_core=core,
        reference=reference,
        metadata=metadata,
        indicators=indicators,
    )

    return item, meta

# ==========================================================
# Extract and build an Inventory object from Oekobaudat CSV
# ==========================================================


def extract_inventory_obd(
    csv_path: Union[str, Path],
    *,
    write_json: bool = True,                   # write one JSON per InventoryItem
    output_dir: Optional[Path | str] = None,    # where to write those JSON files
) -> Inventory:
    """
    Build an Inventory from an OBD CSV.

    - Reads the CSV
    - Iterates all UUIDs
    - Extracts an InventoryItem per UUID
    - Optionally writes each item to JSON under a dynamic folder structure:
        {output_dir}/{entry_type}/{material_type|component_type}/{id}.json
      with 'unknown' fallback buckets.
    - Returns an Inventory containing all items.
    """
    # Early validation
    if write_json and output_dir is None:
        raise ValueError("If write_json=True, you must provide an output_dir.")

    # initialize base directory
    base_dir: Optional[Path] = Path(output_dir) if output_dir is not None else None

    # initialize LLM metadata (cost, token usage)
    all_llm_meta: dict[str, Any] = {}

    # Read csv -> DataFrame
    obd: pd.DataFrame = read_csv(csv_path)

    # Collect UUIDs in processing order
    uuids: List[str] = uuids_in_csv(obd)
    total = len(uuids)
    print(f"\nFound {total} UUID(s) in {csv_path}")

    # Extract items
    items: List[InventoryItem] = []
    for i, uuid in enumerate(uuids, start=1):
        print(f"\n[{i}/{total}] UUID={uuid} → building InventoryItem…")
        try:
            # subset per UUID
            uuid_df: pd.DataFrame = subset_for_uuid(obd, uuid)
            uuid_series: pd.Series = first_row_for_uuid(uuid_df, uuid)

            # extract one InventoryItem (this will also write its JSON if requested)
            item, llm_meta = extract_inventory_item_obd(
                uuid_df=uuid_df,
                uuid_series=uuid_series
            )
            items.append(item)
            all_llm_meta = merge_llm_meta(all_llm_meta, llm_meta)

            if write_json and base_dir is not None:
                # Get info from item, dynamically create folder taxonomy
                entry_type, subdir = infer_bucket(item)
                # Serialize the InventoryItem as JSON
                path = write_item(item, base_dir, entry_type, subdir)
                print(f"[OK] Wrote JSON → {path.as_posix()}")
            else:
                print(f"[OK] Built InventoryItem object for uuid: {uuid}")

        except Exception:
            print(f"[FAIL] Couldn't process InventoryItem for uuid: {uuid}")
            traceback.print_exc()

    # write LLM metadata
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        meta_path = output_dir / "llm_metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(all_llm_meta, f, indent=2)
        print(f"Aggregated LLM metadata saved to: {meta_path}")

    # Return Inventory wrapper
    return Inventory(items)