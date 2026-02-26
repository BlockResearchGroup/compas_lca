
import json

from pathlib import Path
from typing import Dict
from typing import Any
from typing import Optional
from typing import Iterable
from typing import List
from typing import Union

import pandas as pd

from compas_lca.workflows.raw_extraction.url.url_extraction import extract_url

from compas_lca.workflows.raw_extraction.oekobaudat.obd_readers import read_csv
from compas_lca.workflows.raw_extraction.oekobaudat.obd_readers import uuids_in_csv
from compas_lca.workflows.raw_extraction.oekobaudat.obd_readers import subset_for_uuid
from compas_lca.workflows.raw_extraction.oekobaudat.obd_readers import first_row_for_uuid

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed


# Defaults you can override at call time
DEFAULT_KEEP_COLUMNS = [
    "UUID",
    "URL",
    "Name (de)",
    "Name (en)",
    "Kategorie (original)",
    "Kategorie (en)",
    "Typ",
    "Referenzfluss-Name",
    "Schuettdichte (kg/m3)",
    "Flaechengewicht (kg/m2)",
    "Rohdichte (kg/m3)",
    "Schichtdicke (m)",
]

DEFAULT_KEEP_KEYS = {
    "Description",
    "Technical purpose of product or process",
    "Use advice for data set",
    "Classification number",
    "General comment on data set",
    "Technology description including background system",
}


def obd_series_to_json(
    s: pd.Series,
    *,
    columns: list[str] | None = None,
) -> str:
    """Serialize selected columns of a Series to a pretty JSON string."""
    if columns is not None:
        s = s.loc[[c for c in columns if c in s.index]]

    s_clean = s.where(~s.isna(), None)
    data = {str(k): v for k, v in s_clean.to_dict().items()}

    return json.dumps(data, ensure_ascii=False, indent=2) # pretty


def ingest_obd_item(
    series_uuid: pd.Series,
    *,
    # series → json options
    keep_columns: Optional[list[str]] = None,
    # url → json options
    select_keys: bool = True,
    keep_keys: Optional[Iterable[str]] = None,
    # output (optional)
    out_path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """
    Combine JSON from the Series (via `obd_series_to_json`) and the URL (via `extract_url`)
    into one flat JSON. Writes to `out_path` if provided, else returns the JSON string.
    """

    # set defaults
    keep_columns = keep_columns or DEFAULT_KEEP_COLUMNS
    keep_keys = keep_keys or DEFAULT_KEEP_KEYS

    # 1) Series → dict
    series_json_str = obd_series_to_json(
        series_uuid,
        columns=keep_columns or DEFAULT_KEEP_COLUMNS,
    )
    try:
        series_dict: Dict[str, Any] = json.loads(series_json_str) if series_json_str else {}
    except json.JSONDecodeError:
        series_dict = {}

    # 2) URL → dict (force JSON mode)
    url_value = str(series_uuid.get("URL", "")).strip()
    url_dict: Dict[str, Any] = {}
    if url_value:
        url_json_str = extract_url(
            url_value,
            return_json=True,          # force JSON so we can merge
            select_keys=select_keys,
            keep_keys=(keep_keys or DEFAULT_KEEP_KEYS),
        )
        try:
            url_dict = json.loads(url_json_str) if url_json_str else {}
        except json.JSONDecodeError:
            url_dict = {}

    # 3) Merge (URL fields take precedence if keys collide)
    combined: Dict[str, Any] = {**series_dict, **url_dict}

    # 4) Serialize once
    combined_json = json.dumps(combined, ensure_ascii=False, indent=2)

    # 5) Optional write
    if out_path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(combined_json, encoding="utf-8")
    return combined


def write_obd_payload(
    payload: Dict[str, Any],
    payload_dir: Path,
    uuid: str,
) -> Path:
    payload_dir.mkdir(parents=True, exist_ok=True)
    path = payload_dir / f"{uuid}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return path

def build_obd_payload_for_uuid(uuid_series: pd.Series) -> Dict[str, Any]:
    # Exactly what you do today in extract_matching_core_obd
    return ingest_obd_item(uuid_series)

def extract_obd_payloads(
    csv_path: Union[str, Path],
    *,
    payload_dir: Union[str, Path],
    max_workers: int = 1,
    resume: bool = True,
    uuid_filter: Optional[List[str]] = None,
) -> Path:
    payload_dir = Path(payload_dir)
    payload_dir.mkdir(parents=True, exist_ok=True)

    obd: pd.DataFrame = read_csv(csv_path)
    uuids: List[str] = uuids_in_csv(obd)

    if uuid_filter is not None:
        s = set(uuid_filter)
        uuids = [u for u in uuids if u in s]

    if resume:
        existing = {p.stem for p in payload_dir.glob("*.json") if p.name != "llm_metadata.json"}
        uuids = [u for u in uuids if u not in existing]

    total = len(uuids)
    print(f"Writing {total} OBD payload JSON(s) to: {payload_dir}")

    def _one(uuid: str, idx: int):
        uuid_df = subset_for_uuid(obd, uuid)
        uuid_series = first_row_for_uuid(uuid_df, uuid)
        payload = build_obd_payload_for_uuid(uuid_series)
        path = write_obd_payload(payload, payload_dir, uuid)
        print(f"[{idx}/{total}] payload → {path.name}")
        return path

    if max_workers > 1:
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = [ex.submit(_one, u, i) for i, u in enumerate(uuids, start=1)]
            for f in as_completed(futures):
                f.result()
    else:
        for i, u in enumerate(uuids, start=1):
            _one(u, i)

    return payload_dir