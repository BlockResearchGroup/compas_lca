import json

import re

from collections import OrderedDict

from pathlib import Path

from typing import Any
from typing import Literal
from typing import List
from typing import Iterator
from typing import Iterable
from typing import Optional
from typing import Dict
from typing import Tuple

from pydantic import BaseModel
from pydantic import ConfigDict

from compas_lca.model.lca_element import LcaElement
from compas_lca.model.metadata import ModelMetadata
from compas_lca.model.descriptor import ElementDescriptor
from compas_lca.matching_core.core import MatchingCore

from compas_lca.helpers import load_json

# ===============
# GENERIC HELPERS
# ===============

def get_single_ifc(directory: Path) -> Path:
    """
    Find exactly one IFC file in `directory` (non-recursive).
    - Accepts case-insensitive `.ifc` extension.
    Raises helpful errors if zero or multiple are found.
    """
    if not directory.exists() or not directory.is_dir():
        raise NotADirectoryError(f"Directory does not exist: {directory}")

    # Only scan files directly in this folder
    candidates = [
        p for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() == ".ifc"
    ]

    if not candidates:
        raise FileNotFoundError(f"No .ifc files found in {directory}")

    if len(candidates) > 1:
        details = "\n  - " + "\n  - ".join(str(p) for p in candidates)
        raise ValueError(
            f"Expected exactly one .ifc file but found {len(candidates)} in {directory}:{details}"
        )

    return candidates[0]

def get_classification(element, classification_rels):
    """
    Extracts classification information associated with an IFC element using IfcRelAssociatesClassification relationships.

    Parameters
    ----------
    element : compas_ifc.entities.element.IfcBuildingElement
        The IFC element whose classification information should be extracted.
    rel_classifications : compas_ifc.model.get_entities_by_type("IfcRelAssociatesClassification")
        A list of `IfcRelAssociatesClassification` relationship instances to search through.

    Returns
    -------
    list[dict] or str
        A list of dictionaries containing classification information for the element, where each dictionary includes:
        - IfcEntity: The IFC entity type of the classification reference.
        - Identification: The classification code or identifier.
        - System Name: The name of the classification system or source.
        - Name: The classification name or title.
    """
    classifications = []
    for rel in classification_rels:
        if element in rel.RelatedObjects:
            classification_ref = rel.RelatingClassification
            classification_data = {
                "IfcEntity": type(classification_ref).__name__,
                "Identification": getattr(classification_ref, "Identification", "Unknown"),
                "System Name": getattr(getattr(classification_ref, "ReferencedSource", None), "Name", "Unknown"),
                "Name": getattr(classification_ref, "Name", "Unknown")
            }
            classifications.append(classification_data)
    if not classifications:
        return None
    return classifications


def get_hierarchy(element, aggregates_rels):
    """
    Extracts hierarchical decomposition information for a given IFC element.

    Parameters
    ----------
    element : compas_ifc.entities.element.IfcBuildingElement
        The IFC element whose hierarchical relationships are being analyzed.
    aggregates : compas_ifc.model.get_entities_by_type("IfcRelAggregates")
        A list of `IfcRelAggregates` relationship instances to search through.

    Returns
    -------
    tuple[dict, list[dict]]
        A tuple containing:
        - **decomposes** (`dict`): Information about the parent element that this element decomposes into.
        - **is_decomposed_by** (`list[dict]`): A list of child elements that this element decomposes into.
    """

    decomposes = {}
    is_decomposed_by = []
    for rel in aggregates_rels:
        if element in rel.RelatedObjects:
            decomposes = {
                "Name": rel.RelatingObject.Name if hasattr(rel.RelatingObject, "Name") and rel.RelatingObject.Name else None,
                "IfcEntity": type(rel.RelatingObject).__name__,
                "GlobalId": rel.RelatingObject.GlobalId if hasattr(rel.RelatingObject, "GlobalId") else None
            }
        if element == rel.RelatingObject:
            is_decomposed_by.extend([
                {
                    "Name": obj.Name if hasattr(obj, "Name") and obj.Name else None,
                    "IfcEntity": type(obj).__name__,
                    "GlobalId": obj.GlobalId if hasattr(obj, "GlobalId") else None
                }
                for obj in rel.RelatedObjects
            ])
    return decomposes, is_decomposed_by


def get_material_props(material_definition, caches):
    """Always try to get IfcMaterialProperties from cache; returns None if not found."""
    mprops = caches.material_props_by_def.get(material_definition)
    if not mprops:
        return None
    return [
        {
            "name": getattr(p, "Name", None),
            "description": getattr(p, "Description", None),
            "properties": [
                {
                    "name": getattr(prop, "Name", None),
                    "value": getattr(getattr(prop, "NominalValue", None), "value", None),
                }
                for prop in getattr(p, "Properties", []) or []
            ],
        }
        for p in mprops
    ]

def clean_value(value):
    if isinstance(value, str):
        # Remove "<IfcType" wrappers if present
        if value.startswith("<Ifc") and " " in value:
            return value.split(" ", 1)[1].rstrip(">")
        return value  # Return as-is if it's already clean
    return value  # Return numbers/booleans as-is

Bucket = Literal["elements", "multilayers", "multimaterials"]

def classify_material_bucket(material_data) -> Optional[Bucket]:
    """
    Return which bucket the element should go to based on its material structure:
      - "multilayers"     → IfcMaterialLayerSet/IfcMaterialLayerSetUsage with >1 layers
      - "multimaterials"  → IfcMaterialList with >1 materials
      - None              → single material/layer or unknown structure
    """
    if not material_data:
        return None

    entity = getattr(material_data, "entity", None)
    layers = getattr(material_data, "material_layers", None) or []
    mats   = getattr(material_data, "materials", None) or []

    if entity in {"IfcMaterialLayerSetUsage", "IfcMaterialLayerSet"} and len(layers) > 1:
        return "multilayers"
    if entity == "IfcMaterialList" and len(mats) > 1:
        return "multimaterials"

    return None

def write_bytes(path: Path, blob: bytes) -> None:
    with path.open("wb") as f:
        f.write(blob)


# =======================
# COMPAS GEOMETRY HELPERS
# =======================


def tesselated_brep_obb(geom, units, ndigits=2):
    """Return largest OBB face area in project units (typically m²)."""
    # Get the Box from compas_ifc TessellatedBrep.obb
    try:
        box = getattr(geom, "obb", None)
    except Exception:
        box = None
    if not box:
        return None

    # Box sizes are in model length units
    x, y, z = box.xsize, box.ysize, box.zsize
    if x is None or y is None or z is None:
        return None

    max_area_model = max(x * y, y * z, x * z)

    # Convert to project units (e.g. m²)
    scale = units.get("lc_factor")
    max_area_si = max_area_model * (scale ** 2)

    return round(x,ndigits), round(y,ndigits), round(z,ndigits), round(max_area_si, ndigits)

def tesselated_brep_volume(geom, units, ndigits=4):
    """Return the COMPAS geometry volume converted to project units (e.g. m³)."""
    # Get raw volume (in model units)
    try:
        volume_model = getattr(geom, "volume", None)
    except Exception:
        return None

    if volume_model is None:
        return None

    # Convert to SI (project) units
    scale = units.get("lc_factor")
    volume_si = volume_model * (scale ** 3)

    return round(volume_si, ndigits)

def has_valid_geometry(element):
    """Return True if element has a geometry with vertices or solid data."""
    geom = getattr(element, "geometry", None)
    if geom is None:
        return False

    # COMPAS TessellatedBrep usually has a .vertices attribute (numpy array)
    if hasattr(geom, "vertices"):
        try:
            return len(geom.vertices) > 0
        except Exception:
            return False

    # Fallback for other geometry types
    return True


# ======================================
# QUANTITY HELPERS (PRIORITIZATION)
# ======================================

def _get_in(d: Dict[str, Any], path: Iterable[str]) -> Any:
    """Safe nested getter; returns None if any step is missing."""
    cur = d
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
        if cur is None:
            return None
    return cur

def _coerce_number(x: Any) -> Optional[float | int]:
    """Parse ints/floats from typical JSON strings; None if not parseable."""
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return x
    if isinstance(x, str):
        s = x.strip().replace(",", ".")
        try:
            f = float(s)
            return int(f) if f.is_integer() else f
        except ValueError:
            return None
    return None

def _first_numeric(input_json: Dict[str, Any], paths: List[List[str]]) -> Optional[float | int]:
    """Return the first parseable numeric across candidate paths."""
    for p in paths:
        val = _get_in(input_json, p)
        num = _coerce_number(val)
        if num is not None:
            return num
    return None

def _obb_dimension_range(input_json: dict) -> Optional[Tuple[float, float]]:
    """
    Return (smallest, largest) of compas_obb_{x,y,z}dim values found in input_json["quantities"].
    Returns None if none are numeric.
    """
    q = input_json.get("quantities", {})
    if not isinstance(q, dict):
        return None

    dims = []
    for key in ("compas_obb_xdim", "compas_obb_ydim", "compas_obb_zdim"):
        val = q.get(key)
        num = _coerce_number(val)
        if num is not None:
            dims.append(num)

    if not dims:
        return None

    return min(dims), max(dims)

# ======================================
# CREATE PACKAGE (FOLDER) FOR MULTILAYER
# ======================================

def _to_plain_dict(obj: Any) -> Dict[str, Any]:
    """
    Convert an arbitrary layer object into a plain dict.
    Tries pydantic .model_dump(), then .dict(), then assumes it's already a dict.
    """
    if hasattr(obj, "model_dump"):  # Pydantic v2
        return obj.model_dump(exclude_none=True, by_alias=True)
    if hasattr(obj, "dict"):        # Pydantic v1 or similar
        return obj.dict(exclude_none=True, by_alias=True)
    if isinstance(obj, dict):
        return obj
    # last resort: JSON round-trip if it's something serializable
    try:
        return json.loads(json.dumps(obj))
    except Exception as e:
        raise TypeError(f"Cannot convert layer object of type {type(obj)} to dict") from e

class IfcTargetLayer(BaseModel):
    """Specialized container that highlights layer (from IfcMaterialLayerSet) and minimal
    element metadata (for precision of inference, i.e., for application area, etc.)"""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    target_layer: Optional[Dict] = None
    parent_element_context: Optional[Dict] = None

def write_multilayer_pkg(
    root: Path,
    gid: str,
    element_blob: bytes,
    layers: List[Any],
    metadata: dict,
    psets: Optional[dict] = None
) -> None:
    """
    Writes a multilayer element as a folder:
      root/{gid}/
        {gid}.json
        {gid}_L1.json, {gid}_L2.json, ...

    Each L{i}.json adheres to IfcTargetLayer schema:
      {
        "target_layer": { ...layer dict... },
        "parent_element_context": { ...metadata... }
      }
    """
    pkg_dir = root / gid
    pkg_dir.mkdir(parents=True, exist_ok=True)
    # main element JSON
    write_bytes(pkg_dir / f"{gid}.json", element_blob)
    meta_dict = _to_plain_dict(metadata) if metadata is not None else {}
    psets_dict = _to_plain_dict(psets) if psets is not None else {}

    # base parent context (shared fields only)
    base_parent_context: dict = {}
    if "name" in meta_dict:
        base_parent_context["parent_element_name"] = meta_dict["name"]
    if "entity" in meta_dict:
        base_parent_context["entity"] = meta_dict["entity"]
    if psets_dict:
        base_parent_context["parent_element_properties"] = psets_dict

    # Precompute normalized layer dicts once
    layer_dicts: list[dict] = []
    for layer in layers:
        d = _to_plain_dict(layer) or {}
        layer_dicts.append(dict(d))  # shallow copy to detach from source

    for i, layer_dict in enumerate(layer_dicts, start=1):
        # Build "other_layers" = all except current index
        other_layers = [
            d for j, d in enumerate(layer_dicts)
            if j != (i - 1)
        ]

        # Per-file context (do not mutate shared base_parent_context)
        parent_context_for_file = dict(base_parent_context)
        parent_context_for_file["other_layers"] = other_layers

        wrapped = IfcTargetLayer(
            target_layer=layer_dict,  # optional but safest
            parent_element_context=parent_context_for_file,
        )

        layer_blob = wrapped.model_dump_json(
            exclude_none=True, by_alias=True, indent=2
        ).encode("utf-8")

        write_bytes(pkg_dir / f"{gid}_L{i}.json", layer_blob)


class IfcTargetMaterial(BaseModel):
    """Specialized container that highlights material (from IfcMaterialList) and minimal
    element metadata (for precision of inference, i.e., for application area, etc.)"""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    target_material: Optional[Dict] = None
    parent_element_context: Optional[Dict] = None

def write_multimaterial_pkg(
    root: Path,
    gid: str,
    element_blob: bytes,
    materials: List[Any],
    metadata: dict
) -> None:
    """
    Writes an element with material list as a folder:
      root/{gid}/
        {gid}.json
        M1.json, M2.json, ...

    Each M{i}.json adheres to the IfcTargetMaterial schema:
      {
        "target_material": { ...material dict... },
        "parent_element_context": { ...metadata... }
      }

    Args:
        root: Base directory where the multimaterial folder will be created.
        gid: GlobalId of the element (used as folder name and file name).
        element_blob: JSON bytes of the full element.
        materials: List of IfcMaterial models (or dict-like objects).
        metadata: Metadata to include as 'parent_element_context'.
    """
    pkg_dir = root / gid
    pkg_dir.mkdir(parents=True, exist_ok=True)

    # Write the main element JSON
    write_bytes(pkg_dir / f"{gid}.json", element_blob)
    meta_dict = _to_plain_dict(metadata) if metadata is not None else {}
    meta_filtered = {"entity": meta_dict.get("entity")} if "entity" in meta_dict else {}

    # Wrap and write each material
    for i, mat in enumerate(materials, start=1):
        mat_dict = _to_plain_dict(mat)

        wrapped = IfcTargetMaterial(
            target_material=mat_dict,
            parent_element_context=meta_filtered,
        )

        mat_blob = wrapped.model_dump_json(exclude_none=True, by_alias=True, indent=2).encode("utf-8")
        write_bytes(pkg_dir / f"M{i}.json", mat_blob)



# =================================
# PIPELINE + MODEL METADATA HELPERS
# =================================


NO_OBJTYPE = "UNSPECIFIED_OBJECTTYPE"

def norm_objtype(obj_type: Optional[str]) -> str:
    return (obj_type or NO_OBJTYPE).strip() or NO_OBJTYPE

def init_rep_index() -> Dict[str, Dict[str, Any]]:
    # "<ObjectType>": {"representative": {...} | None, "members": [ {...}, ... ]}
    return {}

def update_rep_index(index: Dict[str, Dict[str, Any]],
                      obj_type: Optional[str],
                      name: Optional[str],
                      gid: str) -> bool:
    """
    Update the index with this element.
    Returns True if this element became the representative for its object_type.
    """
    key = norm_objtype(obj_type)
    member = {"name": name, "global_id": gid}
    entry = index.setdefault(key, {"representative": None, "members": []})
    entry["members"].append(member)
    if entry["representative"] is None:
        entry["representative"] = member
        return True
    return False

def _finalize_rep_index(index: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    {
      "ObjectTypes": { ...sorted by members count desc, singles last... },
      "UnspecifiedObjectType": { "members": [...] }
    }
    """
    unspecified_members = index.get(NO_OBJTYPE, {}).get("members", [])

    # Split into multi-member and single-member buckets (exclude unspecified)
    items = [(k, v) for k, v in index.items() if k != NO_OBJTYPE]
    multi = [(k, v) for k, v in items if len(v.get("members", [])) > 1]
    singles = [(k, v) for k, v in items if len(v.get("members", [])) <= 1]

    # Sort multi-member by size DESC (tie-breaker: name ASC)
    multi_sorted = sorted(
        multi,
        key=lambda kv: (len(kv[1].get("members", [])), -ord(kv[0][0]) if kv[0] else 0),
        reverse=True,
    )
    # Simpler/clearer tie-breaker:
    multi_sorted = sorted(
        multi, key=lambda kv: (-len(kv[1].get("members", [])), kv[0].upper())
    )

    # Sort singles by name ASC (optional; keeps it deterministic)
    singles_sorted = sorted(singles, key=lambda kv: kv[0].upper())

    # Build an ordered mapping in the desired order
    ordered_object_types = OrderedDict()
    for k, v in multi_sorted + singles_sorted:
        ordered_object_types[k] = v

    return {
        "ObjectTypes": ordered_object_types,                 # ordered
        "UnspecifiedObjectType": {"members": unspecified_members},
    }

def write_rep_index(index: Dict[str, Dict[str, Any]], output_dir: Path) -> None:
    reps_path = output_dir / "metadata" / "representatives.json"
    reps_path.parent.mkdir(parents=True, exist_ok=True)
    final_payload = _finalize_rep_index(index)
    with reps_path.open("w", encoding="utf-8") as f:
        json.dump(final_payload, f, ensure_ascii=False, indent=2)

def write_comp_index(compositions_meta: List[Dict[str, Any]], output_dir: Path) -> None:
    if not compositions_meta:
        return  # nothing to write
    compositions_path = output_dir / "metadata" / "compositions.json"
    compositions_path.parent.mkdir(parents=True, exist_ok=True)
    with compositions_path.open("w", encoding="utf-8") as f:
        json.dump(compositions_meta, f, ensure_ascii=False, indent=2)

def init_ml_index() -> Dict[str, List[Dict[str, str]]]:
    """
    Initialize the multilayers metadata index.
    Structure:
    {
        "IfcMaterialLayerSet": [],
        "IfcMaterialLayerSetUsage": []
    }
    """
    return {
        "IfcMaterialLayerSet": [],
        "IfcMaterialLayerSetUsage": [],
    }

def init_mm_index() -> List[Dict[str, str]]:
    """
    Initialize the multimaterials metadata index.
    Structure:
    [
        {"name": str|None, "global_id": str},
        ...
    ]
    """
    return []


def write_ml_index(index: Dict[str, List[Dict[str, str]]], output_dir: Path) -> None:
    """
    index shape:
      {
        "IfcMaterialLayerSet":      [ {"name": str|None, "global_id": str}, ... ],
        "IfcMaterialLayerSetUsage": [ {"name": str|None, "global_id": str}, ... ],
      }
    """
    # Ensure keys exist even if empty (stable schema)
    payload = {
        "IfcMaterialLayerSet": index.get("IfcMaterialLayerSet", []),
        "IfcMaterialLayerSetUsage": index.get("IfcMaterialLayerSetUsage", []),
    }
    path = output_dir / "metadata" / "multilayers.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def write_mm_index(items: List[Dict[str, str]], output_dir: Path) -> None:
    """
    items shape:
      [ {"name": str|None, "global_id": str}, ... ]
    """
    if not items:
        return
    path = output_dir / "metadata" / "multimaterials.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def write_meta_ifc(ifcmeta: Dict[str, Any], output_dir: Path) -> None:
    model_path = output_dir / "metadata" / "model.json"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with model_path.open("w", encoding="utf-8") as f:
        json.dump(ifcmeta, f, ensure_ascii=False, indent=2)


def _to_decimal(angle):
    """Convert IFC RefLatitude/RefLongitude lists to decimal degrees."""
    if isinstance(angle, (list, tuple)) and len(angle) >= 1:
        deg = angle[0]
        min_ = angle[1] if len(angle) > 1 else 0
        sec = angle[2] if len(angle) > 2 else 0
        frac = angle[3] if len(angle) > 3 else 0
        return deg + (min_ / 60.0) + (sec / 3600.0) + (frac / 3600000.0)
    elif isinstance(angle, (int, float)):
        return float(angle)
    return None

# helpers that mirror your extract_material_data selection logic, lightweight for counting.
def _kind(x):
    return x.is_a() if hasattr(x, "is_a") else type(x).__name__

def _pick_best(rels) -> Optional[Tuple[str, Any]]:
    candidates = []
    for r in rels:
        rel_mat = getattr(r, "RelatingMaterial", None)
        if rel_mat is None:
            continue
        candidates.append((_kind(rel_mat), rel_mat))
    if not candidates:
        return None
    priority = {
        "IfcMaterialLayerSetUsage": 4,
        "IfcMaterialLayerSet": 3,
        "IfcMaterialList": 2,
        "IfcMaterial": 1,
    }
    kind, rel_mat = max(candidates, key=lambda kv: priority.get(kv[0], 0))
    return kind, rel_mat

def _best_material_rel(element, caches) -> Optional[Tuple[str, Any]]:
    elem_rels = [
        r for r in (getattr(caches, "material_rels", []) or [])
        if element in (getattr(r, "RelatedObjects", None) or [])
    ]
    best = _pick_best(elem_rels)
    if best:
        return best
    type_rels = (getattr(caches, "type_rels", []) or [])
    elem_type = next(
        (getattr(r, "RelatingType", None)
            for r in type_rels
            if element in (getattr(r, "RelatedObjects", None) or [])),
        None
    )
    if elem_type is not None:
        type_mat_rels = [
            r for r in (getattr(caches, "material_rels", []) or [])
            if elem_type in (getattr(r, "RelatedObjects", None) or [])
        ]
        return _pick_best(type_mat_rels)
    return None


# ===============================================
# HELPERS FOR PREPROCESSED IFC DATA -> LcaElement
# ===============================================

LAYER_RE = re.compile(r"^L(\d+)$")
MAT_RE   = re.compile(r"^M(\d+)$")

def _discover_multix_paths(
    directory: Path,
    kind: Literal["multilayer", "multimaterial"],
) -> Tuple[Path, List[Path]]:
    """
    Return (global_json_path, ordered_part_paths, part_count) for a multilayer/multimaterial directory.

    Rules:
      - The "global" JSON is any *.json whose stem does NOT match L\\d+ / M\\d+.
        Prefer a file whose stem == directory.name if present.
      - Part files are everything matching L\\d+.json (for multilayer) or M\\d+.json (for multimaterial),
        sorted by their numeric index (1, 2, 3, ...).
      - part_count is the number of part files found (i.e., len(ordered_part_paths)).
    """
    if not directory.exists() or not directory.is_dir():
        raise FileNotFoundError(f"Directory not found: {directory}")

    json_files = [p for p in directory.glob("*.json") if p.is_file()]
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in: {directory}")

    if kind == "multilayer":
        part_re = LAYER_RE
        part_prefix = "L"
    else:
        part_re = MAT_RE
        part_prefix = "M"

    part_paths: List[tuple[int, Path]] = []
    global_candidates: List[Path] = []

    for p in json_files:
        m = part_re.match(p.stem)
        if m:
            idx = int(m.group(1))
            part_paths.append((idx, p))
        else:
            global_candidates.append(p)

    if not global_candidates:
        raise ValueError(
            f"Expected a global JSON in {directory} (a file not named {part_prefix}N.json)."
        )

    # Prefer file matching directory name, else the first non-part json (deterministic by sort)
    preferred = directory.name + ".json"
    global_path = None
    for p in global_candidates:
        if p.name == preferred:
            global_path = p
            break
    if global_path is None:
        global_path = sorted(global_candidates)[0]

    # Sort parts by numeric index: L1, L2, ... or M1, M2, ...
    part_paths_sorted = [p for _, p in sorted(part_paths, key=lambda t: t[0])]

    return global_path, part_paths_sorted


# =============================================
# HELPERS FOR PREPROCESSED IFC DATA -> LcaModel
# =============================================

def _build_rep_guid_map(tree: dict) -> dict[str, dict]:
    """
    finds any {representative, members} dicts anywhere in the tree
    """
    out: dict[str, dict] = {}

    def visit(node):
        if isinstance(node, dict):
            # if this node looks like an entry, record it
            rep = node.get("representative")
            mem = node.get("members")
            if isinstance(rep, dict) and isinstance(mem, list):
                gid = rep.get("global_id")
                if gid:
                    out[gid] = node
            # recurse
            for v in node.values():
                visit(v)
        elif isinstance(node, list):
            for v in node:
                visit(v)

    visit(tree)
    return out

def _iter_subdirs(root: Path) -> Iterator[Path]:
    """Yield immediate subdirectories (skip files)."""
    if not root.exists():
        return
    for p in root.iterdir():
        if p.is_dir():
            yield p


def _build_guid_index(elements_dir: Path) -> dict[str, Path]:
    """
    Build a fast lookup from IFC global_id -> element JSON path
    for all files under `elements_dir` (non-recursive; switch to rglob if needed).
    """
    index: dict[str, Path] = {}
    for p in elements_dir.glob("*.json"):
        try:
            data = load_json(p)
            guid = data.get("metadata", {}).get("global_id")
            if guid:
                index[guid.lower()] = p
        except Exception:
            # Best-effort: skip corrupt/unexpected files
            continue
    return index

def _build_guid_dir_index(root: Path, kind: Literal["multilayer", "multimaterial"]) -> dict[str, Path]:
    """
    Build {global_id: subdir_path} for multi-* layouts.
    Each subdir contains a 'global' JSON plus L{n}.json / M{n}.json parts.
    """
    index: dict[str, Path] = {}
    for sub in _iter_subdirs(root):
        try:
            global_path, _ = _discover_multix_paths(sub, kind)
        except Exception:
            continue
        data = load_json(global_path)
        guid = data.get("metadata", {}).get("global_id")
        if guid:
            index[guid.lower()] = sub
    return index


def _save_lca_element(elem: LcaElement, out_dir: Optional[Path]) -> None:
    if out_dir is None:
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = str(elem.id)
    (out_dir / f"{stem}.json").write_text(elem.model_dump_json(indent=2), encoding="utf-8")

def _save_model_metadata(meta: ModelMetadata, out_dir: Optional[Path]) -> None:
    if out_dir is None:
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = str(meta.dataset_uuid)
    (out_dir / f"{stem}.json").write_text(meta.model_dump_json(indent=2), encoding="utf-8")

def update_descriptor_ifc(member: dict[str, Any], descriptor: ElementDescriptor) -> ElementDescriptor:
    metadata = member.get("metadata", {}) or {}
    name = metadata.get("name")
    global_id = metadata.get("global_id")
    if not isinstance(name, str) or not name.strip():
        name = getattr(descriptor, "element_name", None)
    if not isinstance(global_id, str) or not global_id.strip():
        global_id = getattr(descriptor, "element_uuid", None)
    try:
        return descriptor.model_copy(update={
            "element_name": name,
            "element_uuid": global_id,
        })
    except Exception as e:
        return descriptor

def update_matching_core_ifc(member: dict[str, Any], core: MatchingCore, entry_type: Optional[str]) -> MatchingCore:
    try:
        if entry_type == "component":
            metadata = member.get("metadata", {}) or {}
            new_name = metadata.get("name")
            if not isinstance(new_name, str) or not new_name.strip():
                new_name = getattr(core, "name", None)
            return core.model_copy(update={"name": new_name})
        return core
    except Exception as e:
        return core
    
def _normalize_entry_type(t):
    """Return 'component' | 'material' | 'unknown' | None from enum or str."""
    if t is None:
        return None
    return getattr(t, "value", str(t))


def _get_material_type(core):
    """
    Best-effort read of facet.material_type from either a Pydantic object or a dict.
    Returns a lowercase string or None.
    """
    facet = getattr(core, "facet", None) if not isinstance(core, dict) else core.get("facet")
    if facet is None:
        return None
    mt = getattr(facet, "material_type", None) if not isinstance(facet, dict) else facet.get("material_type")
    return None if mt is None else str(mt).lower().strip()


def _is_unknownish_core(core, t_norm):
    """
    'unknown-ish' means:
      - entry_type in {None, 'unknown'}, OR
      - entry_type == 'material' AND facet.material_type in {None, 'unknown', ''}
    """
    if t_norm in (None, "unknown"):
        return True
    if t_norm == "material":
        mt = _get_material_type(core)
        return (mt is None) or (mt == "") or (mt == "unknown")
    return False

def _pick_multilayer_bucket(
        rep_elem, 
        layered_list, layered_dir, 
        undef_list, undef_dir):
    cores = getattr(rep_elem, "element_core", None) or []
    if not cores:
        return undef_list, undef_dir, None

    types = [
        _normalize_entry_type(getattr(c, "entry_type", None) if not isinstance(c, dict) else c.get("entry_type"))
        for c in cores
    ]

    # 1) any component -> layered
    if any(t == "component" for t in types):
        return layered_list, layered_dir, "component"

    # 2) any material with known material_type -> layered (route as 'material')
    if any(
        t == "material" and (_get_material_type(c) not in (None, "", "unknown"))
        for c, t in zip(cores, types)
    ):
        return layered_list, layered_dir, "material"

    # 3) all cores unknown-ish -> undefined
    if all(_is_unknownish_core(core, t) for core, t in zip(cores, types)):
        return undef_list, undef_dir, None

    # 4) default
    return undef_list, undef_dir, None


def _pick_multimaterial_bucket(
    rep_elem,
    comp_list, comp_dir,        # components bucket
    layered_list, layered_dir,  # multilayer-by-material bucket
    undef_list, undef_dir       # undefined bucket
):
    """
    Multimaterial routing:
      1) if any core is component -> components bucket ('component')
      2) elif any core is material with known material_type -> multilayer bucket ('material')
      3) elif no cores OR all cores are unknown-ish -> undefined (None)
      4) else -> undefined (None)
    Returns: (target_list, target_dir, routing_entry_type)
    """
    cores = getattr(rep_elem, "element_core", None) or []
    if not cores:
        return undef_list, undef_dir, None

    # Normalize entry types once
    types = [
        _normalize_entry_type(getattr(c, "entry_type", None) if not isinstance(c, dict) else c.get("entry_type"))
        for c in cores
    ]

    # 1) any component -> components bucket
    if any(t == "component" for t in types):
        return comp_list, comp_dir, "component"

    # 2) any material with known material_type -> multilayer bucket
    any_known_material = any(
        (t == "material") and (_get_material_type(core) not in (None, "", "unknown"))
        for core, t in zip(cores, types)
    )
    if any_known_material:
        return layered_list, layered_dir, "material"

    # 3) all unknown-ish -> undefined
    if all(_is_unknownish_core(core, t) for core, t in zip(cores, types)):
        return undef_list, undef_dir, None

    # 4) default -> undefined
    return undef_list, undef_dir, None 
