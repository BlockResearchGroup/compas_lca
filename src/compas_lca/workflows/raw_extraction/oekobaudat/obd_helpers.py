import pandas as pd

from enum import Enum

from pathlib import Path

from typing import Dict
from typing import Tuple
from typing import Optional

from compas_lca.inventory.item import InventoryItem


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
    

def infer_bucket(item: "InventoryItem") -> Tuple[str, str]:
    """
    Decide the top-level bucket ('material' / 'component' / 'unknown')
    and the dynamic subdir ('material_type' / 'component_type' / 'unknown'),
    reading directly from BaseModel attributes.
    """
    core = item.item_core  # BaseModel

    # entry_type → 'material' | 'component' | 'unknown'
    entry = core.entry_type
    if isinstance(entry, Enum):
        entry = entry.name
    entry_type = (entry or "unknown").strip().lower()
    if entry_type not in ("material", "component"):
        return "unknown", "unknown"

    # facet is also a BaseModel (may be None)
    facet = getattr(core, "facet", None)

    if entry_type == "material":
        # prefer facet.material_type, then core.material_type
        sub = (getattr(facet, "material_type", None) if facet is not None else None) \
              or getattr(core, "material_type", None)
    else:  # component
        # prefer facet.component_type, then core.component_type
        sub = (getattr(facet, "component_type", None) if facet is not None else None) \
              or getattr(core, "component_type", None)

    if isinstance(sub, Enum):
        sub = sub.name
    subdir = (str(sub) if sub is not None else "unknown").strip().lower() or "unknown"

    return entry_type, subdir


def write_item(
    item: InventoryItem,
    base_dir: Path,
    entry_type: str,
    subdir: str,
) -> Path:
    bucket = (entry_type or "unknown").strip().lower()
    subdir  = (str(subdir) or "unknown").strip().lower()

    # one call that returns a JSON string with proper encoders
    json_str = item.model_dump_json(
        by_alias=True,
        indent=2,
    )

    # pull the id from a JSON-safe dump (or from the model if you prefer)
    payload = item.model_dump(by_alias=True, mode="json")
    item_id = payload.get("id")
    if not item_id:
        raise ValueError("InventoryItem missing 'id'.")

    target_dir = base_dir / bucket / subdir
    target_dir.mkdir(parents=True, exist_ok=True)

    fp = target_dir / f"{item_id}.json"
    fp.write_text(json_str)
    return fp
