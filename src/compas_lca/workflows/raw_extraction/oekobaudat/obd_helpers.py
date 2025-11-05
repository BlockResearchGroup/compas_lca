import pandas as pd

from typing import Dict
from typing import Optional





def safe_str(val: any) -> Optional[str]:
    """Convert to stripped string, return None if empty or invalid."""
    if pd.isna(val):
        return None
    s = str(val).strip()
    return s if s and s.lower() not in {"nan", "none"} else None

def safe_int(val: any) -> Optional[int]:
    """Convert to int, return None if empty or invalid."""
    if pd.isna(val):
        return None
    s = str(val).strip()
    if not s or s.lower() in {"nan", "none"}:
        return None
    try:
        return int(float(s))
    except ValueError:
        return None
    
    
# Standard column names (dont require mapping)
STD_TO_OBD: Dict[str, str] = {
    "PERE": "PERE",
    "PERM": "PERM",
    "PERT": "PERT",
    "PENRE": "PENRE",
    "PENRM": "PENRM",
    "PENRT": "PENRT",
    "SM": "SM",
    "RSF": "RSF",
    "NRSF": "NRSF",
    "FW": "FW",
    "HWD": "HWD",
    "NHWD": "NHWD",
    "RWD": "RWD",
    "CRU": "CRU",
    "MFR": "MFR",
    "MER": "MER",
    "EEE": "EEE",
    "EET": "EET",
}

# EN15978/+A2 label (map to normal)
A2_TO_OBD: Dict[str, str] = {
    "AP (A2)": "AP",
    "GWPtotal (A2)": "GWPtotal",
    "GWPbiogenic (A2)": "GWPbiogenic",
    "GWPfossil (A2)": "GWPfossil",
    "GWPluluc (A2)": "GWPluluc",
    "ETPfw (A2)": "ETPfw",
    "PM (A2)": "PM",
    "EPmarine (A2)": "EPmarine",
    "EPfreshwater (A2)": "EPfreshwater",
    "EPterrestrial (A2)": "EPterrestrial",
    "HTPc (A2)": "HTPc",
    "HTPnc (A2)": "HTPnc",
    "IRP (A2)": "IRP",
    "SOP (A2)": "SOP",
    "ODP (A2)": "ODP",
    "POCP (A2)": "POCP",
    "ADPF (A2)": "ADPF",
    "ADPE (A2)": "ADPE",
    "WDP (A2)": "WDP",
}

COLUMN_MAP: Dict[str, str] = {**STD_TO_OBD, **A2_TO_OBD}

def parse_num(x):
    """Empty: None, else float using decimal dot (silently ignore non-numeric)."""
    if x is None:
        return None
    s = str(x).strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None