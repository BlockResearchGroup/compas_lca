"""
OBD csv files are very convoluted, as each entry has multiple rows, with each row having
an indicator value for each life cycle stage (and even multiple scnearios for some stages)

These functions enable creating a "dataframe" which is used as a raw data representing an EPD
(EPDRaw)
"""

from typing import List

import pandas as pd

def read_csv(csv_path: str, *, encoding: str = "latin1") -> pd.DataFrame:
    """
    Load an ÖKOBAUDAT CSV (semicolon-separated) as strings.
    """
    df = pd.read_csv(
        csv_path,
        sep=",",
        dtype=str,
        keep_default_na=False,
        na_filter=False,
        encoding=encoding,
    )
    if "UUID" not in df.columns:
        raise ValueError("CSV missing required column 'UUID'.")
    return df

def uuids_in_csv(df: pd.DataFrame) -> List[str]:
    """
    List all unique UUIDs present in the CSV.
    """
    return sorted(u for u in df["UUID"].astype(str).unique() if u.strip())


def subset_for_uuid(df: pd.DataFrame, uuid: str) -> pd.DataFrame:
    """
    Return the slice of rows that belong to one OBD entry (same UUID).
    """
    uuid = str(uuid).strip()
    sub = df[df["UUID"].astype(str) == uuid].copy()
    if sub.empty:
        raise ValueError(f"UUID {uuid} not found in CSV.")
    return sub

def first_row_for_uuid(df: pd.DataFrame, uuid: str) -> pd.Series:
    sub = df[df["UUID"].astype(str) == str(uuid).strip()]
    if sub.empty:
        raise ValueError(f"UUID {uuid} not found.")
    return sub.iloc[0]
