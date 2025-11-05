"""
Function that ingests and formats OBD into a individual JSON files 
for each unique entry (EPD) that entails all relevant information for
determining the Fields inside of the MatchingCore

This step serves to minimize token usage, and to only provide relevant context
for the agent (context engineering)

Idiosyncratic workflow, works for only for the Oekobaudat CSV file, but
core prinicples apply for any ILCD+EPD, as it extracts this dataformat from
HTML.

Works for the following file:
"OBD_2024_I_2025-10-28T13_44_07.csv"
or
"OBD_2024_I_A2.csv" (after running obd_simplify.py)

Raw file can be found in:
https://www.oekobaudat.de/en/service/downloads.html

Last accessed: 29.10.2025
"""
import json

from pathlib import Path
from typing import Dict
from typing import Any
from typing import Optional
from typing import Iterable

import pandas as pd

from compas_lca.workflows.raw_extraction.url.url_extraction import extract_url


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
) -> str:
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
