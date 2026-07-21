import json
import os
import shutil
from datetime import datetime
from datetime import timezone
from enum import Enum
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import pandas as pd
import yaml

from compas_lca.inventory.item import InventoryItem


def sync_trees(source_root: Path, dest_root: Path, log_output_dir: Path) -> None:
    """
    Copy all files from source_root into dest_root, preserving relative paths.
    Create missing directories in dest_root. Do not overwrite existing files.
    Ignore any file named 'llm_metadata.json'.
    Print actions taken.

    Additionally, write a LOG.txt into log_output_dir describing each copied JSON file:
      1) item_core/name
      2) metadata/dataset_uuid
      3) metadata/registration_number
      4) metadata/dataset_source
      5) exact destination path copied into
    """
    source_root = source_root.resolve()
    dest_root = dest_root.resolve()
    log_output_dir = log_output_dir.resolve()

    if not source_root.exists() or not source_root.is_dir():
        raise ValueError(f"Source directory does not exist or is not a directory: {source_root}")

    if not dest_root.exists():
        dest_root.mkdir(parents=True, exist_ok=True)
        print(f"[DIR CREATED] {dest_root}")

    if not dest_root.is_dir():
        raise ValueError(f"Destination is not a directory: {dest_root}")

    # Ensure log output directory exists
    log_output_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_output_dir / "LOG.txt"

    created_dirs: set[Path] = set()
    log_lines: list[str] = []

    # Log header
    started_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    log_lines.append(f"Sync log started: {started_at}")
    log_lines.append(f"Source: {source_root}")
    log_lines.append(f"Destination: {dest_root}")
    log_lines.append("")
    log_lines.append("Entries (copied files only):")
    log_lines.append("-" * 80)

    def _safe_get(dct: dict, path: tuple[str, ...]) -> str:
        cur = dct
        for key in path:
            if not isinstance(cur, dict) or key not in cur:
                return ""
            cur = cur[key]
        return "" if cur is None else str(cur)

    for current_dir, dirnames, filenames in os.walk(source_root):
        current_dir_path = Path(current_dir)

        rel_dir = current_dir_path.relative_to(source_root)
        target_dir = dest_root / rel_dir

        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
            if target_dir not in created_dirs:
                print(f"[DIR CREATED] {target_dir}")
                created_dirs.add(target_dir)

        # Ensure subdirectories exist
        for d in dirnames:
            src_sub = current_dir_path / d
            rel_sub = src_sub.relative_to(source_root)
            dst_sub = dest_root / rel_sub
            if not dst_sub.exists():
                dst_sub.mkdir(parents=True, exist_ok=True)
                if dst_sub not in created_dirs:
                    print(f"[DIR CREATED] {dst_sub}")
                    created_dirs.add(dst_sub)

        # Copy files (excluding llm_metadata.json)
        for fname in filenames:
            src_file = current_dir_path / fname
            rel_file = src_file.relative_to(source_root)

            if fname == "llm_metadata.json":
                continue

            dst_file = dest_root / rel_file

            if dst_file.exists():
                print(f"[SKIP EXISTS] {dst_file.name}  (at {rel_file})")
                continue

            dst_file.parent.mkdir(parents=True, exist_ok=True)

            # Read JSON for logging
            item_name = dataset_uuid = registration_number = dataset_source = ""
            if src_file.suffix.lower() == ".json":
                try:
                    with src_file.open("r", encoding="utf-8") as f:
                        payload = json.load(f)
                    item_name = _safe_get(payload, ("item_core", "name"))
                    dataset_uuid = _safe_get(payload, ("metadata", "dataset_uuid"))
                    registration_number = _safe_get(payload, ("metadata", "registration_number"))
                    dataset_source = _safe_get(payload, ("metadata", "dataset_source"))
                except Exception as e:
                    item_name = item_name or ""
                    dataset_uuid = dataset_uuid or ""
                    registration_number = registration_number or ""
                    dataset_source = dataset_source or ""
                    log_lines.append(f"FILE: {src_file}  (JSON READ ERROR: {type(e).__name__}: {e})")

            shutil.copy2(src_file, dst_file)
            print(f"[ADDED] {dst_file.name}  ->  {rel_file}")

            # log copied JSON files
            if src_file.suffix.lower() == ".json":
                log_lines.append(f"NAME: {item_name}")
                log_lines.append(f"DATASET_UUID: {dataset_uuid}")
                log_lines.append(f"REGISTRATION_NUMBER: {registration_number}")
                log_lines.append(f"DATASET_SOURCE: {dataset_source}")
                log_lines.append(f"COPIED_TO: {dst_file.resolve()}")
                log_lines.append("-" * 80)

    finished_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    log_lines.append("")
    log_lines.append(f"Sync log finished: {finished_at}")

    # Write log
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print(f"[LOG WRITTEN] {log_path}")


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


# Standard column names
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
        sub = (getattr(facet, "material_type", None) if facet is not None else None) or getattr(core, "material_type", None)
    else:  # component
        # prefer facet.component_type, then core.component_type
        sub = (getattr(facet, "component_type", None) if facet is not None else None) or getattr(core, "component_type", None)

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
    subdir = (str(subdir) or "unknown").strip().lower()

    json_str = item.model_dump_json(
        by_alias=True,
        indent=2,
    )

    payload = item.model_dump(by_alias=True, mode="json")
    meta = payload.get("metadata")
    item_id = meta.get("dataset_uuid")
    if not item_id:
        raise ValueError("InventoryItem missing 'id'.")

    target_dir = base_dir / bucket / subdir
    target_dir.mkdir(parents=True, exist_ok=True)

    fp = target_dir / f"{item_id}.json"
    fp.write_text(json_str)
    return fp


def uuids_in_payload_dir(payload_dir: Path) -> List[str]:
    return sorted([p.stem for p in payload_dir.glob("*.json") if p.name != "llm_metadata.json"])


def read_payload(payload_dir: Path, uuid: str) -> Dict[str, Any]:
    path = payload_dir / f"{uuid}.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_epd_parser_config(epd_parser_path: Path) -> dict:
    with epd_parser_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
