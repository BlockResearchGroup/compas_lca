import logging

import csv

import re

import json

from pathlib import Path

from typing import Optional
from typing import Dict
from typing import Any

from .ifc_caches import IfcCaches

from .ifc_readers import load_ifc_file
from .ifc_readers import load_ifc_units
from .ifc_readers import load_ifc_metadata

from .ifc_helpers import get_single_ifc
from .ifc_helpers import clean_value
from .ifc_helpers import write_json
from .ifc_helpers import get_hierarchy
from .ifc_helpers import inverse_list
from .ifc_helpers import get_material_props
from .ifc_helpers import has_valid_geometry
from .ifc_helpers import get_classification
from .ifc_helpers import tesselated_brep_obb
from .ifc_helpers import tesselated_brep_volume
from .ifc_helpers import classify_material_bucket
from .ifc_helpers import init_ml_index
from .ifc_helpers import init_mm_index
from .ifc_helpers import write_ml_index
from .ifc_helpers import write_mm_index
from .ifc_helpers import write_comp_index
from .ifc_helpers import write_object_type_index
from .ifc_helpers import write_meta_ifc
from .ifc_helpers import write_multilayer_pkg
from .ifc_helpers import write_multimaterial_pkg

# ------------------------
# Metadata
# ------------------------
def process_metadata(element, caches) -> dict:
    """Process IFC element metadata and return a plain dict."""
    eid_int = element.id() if hasattr(element, "id") else None
    eid = str(eid_int) if eid_int is not None else None
    decomposes, is_decomposed_by = get_hierarchy(element, caches.aggregates_rels)
    return {
        "name": getattr(element, "Name", None),
        "eid": eid,  # STEP entity id (str)
        "global_id": getattr(element, "GlobalId", None),
        "entity": type(element).__name__,
        "object_type": getattr(element, "ObjectType", None),
        "description": getattr(element, "Description", None),
        "classification": get_classification(element, caches.classification_rels),
        "decomposes": decomposes,
        "is_decomposed_by": is_decomposed_by,
    }


# ------------------------
# Material associations
# ------------------------
def process_material(relating_material, caches) -> dict:
    return {
        "entity": "IfcMaterial",
        "material_name": getattr(relating_material, "Name", None),
        "material_description": getattr(relating_material, "Description", None),
        "material_category": getattr(relating_material, "Category", None),
        "material_properties": get_material_props(relating_material, caches),
    }

def process_material_list(relating_material, caches) -> dict:
    mats = getattr(relating_material, "Materials", None) or []
    return {
        "entity": "IfcMaterialList",
        "materials": [process_material(m, caches) for m in mats if m is not None],
    }

def process_layer(relating_material, caches, units) -> dict:
    mat = getattr(relating_material, "Material", None)
    return {
        "entity": "IfcMaterialLayer",
        "material_name": getattr(mat, "Name", None) if mat else None,
        "material_description": getattr(mat, "Description", None) if mat else None,
        "thickness": getattr(relating_material, "LayerThickness", None),
        "thickness_unit": units.get("LENGTHUNIT"),
        "is_ventilated": getattr(relating_material, "IsVentilated", None),
        "material_properties": get_material_props(mat, caches) if mat else None,
    }

def process_layerset(relating_material, caches, units) -> dict:
    layers = getattr(relating_material, "MaterialLayers", None) or []
    return {
        "entity": "IfcMaterialLayerSet",
        "layer_set_name": getattr(relating_material, "LayerSetName", None),
        "layer_set_description": getattr(relating_material, "Description", None),
        "material_layers": [process_layer(l, caches, units) for l in layers if l is not None],
    }

def process_layerset_usage(relating_material, caches, units) -> dict:
    layer_set = getattr(relating_material, "ForLayerSet", None)
    layers = getattr(layer_set, "MaterialLayers", None) or []
    return {
        "entity": "IfcMaterialLayerSetUsage",
        "layer_set_name": getattr(layer_set, "LayerSetName", None) if layer_set else None,
        "layer_set_description": getattr(layer_set, "Description", None) if layer_set else None,
        "material_layers": [process_layer(l, caches, units) for l in layers if l is not None],
        "layer_set_direction": str(getattr(relating_material, "LayerSetDirection", None)),
        "direction_sense": str(getattr(relating_material, "DirectionSense", None)),
    }

def process_material_data(element, caches, units) -> Optional[Dict[str,Any]]:
    """
    Return the *best* material association for an element (because an element can have multiple IfcRelAssociatesMaterial).
    Preference: IfcMaterialLayerSetUsage > IfcMaterialLayerSet > IfcMaterialList > IfcMaterial.
    Falls back to the element's type if the occurrence has none.

    Not yet implemented: IfcMaterialConstituent(Set) and IfcMaterialProfile(Set) extraction.
    """

    def _kind(x):
        return x.is_a() if hasattr(x, "is_a") else type(x).__name__

    # pass 1: gather all material rels attached to the *element*
    elem_rels = [
        r for r in (getattr(caches, "material_rels", []) or [])
        if element in (getattr(r, "RelatedObjects", None) or [])
    ]
    def _best_candidate(rels):
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

    best = _best_candidate(elem_rels)

    # pass 2: if nothing on the element, try the *type*
    if not best:
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
            best = _best_candidate(type_mat_rels)

    if not best:
        return None

    kind, rel_mat = best
    if kind == "IfcMaterialLayerSetUsage":
        return process_layerset_usage(rel_mat, caches, units)
    elif kind == "IfcMaterialLayerSet":
        return process_layerset(rel_mat, caches, units)
    elif kind == "IfcMaterialList":
        return process_material_list(rel_mat, caches)
    elif kind == "IfcMaterial":
        return process_material(rel_mat, caches)
    return None


# ------------------------
# Property Sets
# ------------------------
def process_psets(element) -> Optional[Dict[str, Any]]:
    psets_element: Dict[str, Any] = {}
    psets_type: Dict[str, Any] = {}

    # ---- Element property sets (RelDefinesByProperties) ----
    for rel in inverse_list(element, "IsDefinedBy"):
        if not rel or not rel.is_a("IfcRelDefinesByProperties"):
            continue

        prop_def = getattr(rel, "RelatingPropertyDefinition", None)
        if not (prop_def and prop_def.is_a("IfcPropertySet")):
            continue

        for prop in getattr(prop_def, "HasProperties", None) or []:
            if not (hasattr(prop, "Name") and hasattr(prop, "NominalValue")):
                continue
            raw_value = getattr(prop, "NominalValue", None)
            if raw_value is not None:
                psets_element[prop.Name] = clean_value(str(raw_value))

    # ---- Type property sets (RelDefinesByType) ----
    # IFC4: element.IsTypedBy
    # IFC2x3: type rels often appear in element.IsDefinedBy as IfcRelDefinesByType
    type_rels = []

    for rel in inverse_list(element, "IsTypedBy"):
        if rel:
            type_rels.append(rel)

    for rel in inverse_list(element, "IsDefinedBy"):
        if rel:
            type_rels.append(rel)

    seen_rel_ids = set()
    for rel in type_rels:
        # De-dup in case a library exposes the same rel via multiple inverses
        rel_id = getattr(rel, "id", None)
        if callable(rel_id):
            rel_id = rel_id()
        if rel_id is not None:
            if rel_id in seen_rel_ids:
                continue
            seen_rel_ids.add(rel_id)

        if not rel.is_a("IfcRelDefinesByType"):
            continue

        object_type = getattr(rel, "RelatingType", None)
        if not object_type:
            continue

        for pset in getattr(object_type, "HasPropertySets", None) or []:
            if not (pset and pset.is_a("IfcPropertySet")):
                continue

            pset_name = getattr(pset, "Name", None) or "UnnamedPset"
            for prop in getattr(pset, "HasProperties", None) or []:
                if not (hasattr(prop, "Name") and hasattr(prop, "NominalValue")):
                    continue
                raw_value = getattr(prop, "NominalValue", None)
                if raw_value is not None:
                    key = f"{pset_name}.{prop.Name}"
                    psets_type[key] = clean_value(str(raw_value))

    if not psets_element and not psets_type:
        return None

    return {
        "psets_element": psets_element or None,
        "psets_type": psets_type or None,
    }

# ------------------------
# Quantities
# ------------------------

def _norm(name: str) -> str:
    return (name or "").lower().replace(" ", "").replace("_", "")

def process_quantities(element, units) -> Optional[Dict[str,Any]]:
    width = length = height = depth = None
    net_area = net_side_area = net_footprint_area = None
    cross_section_area = net_surface_area = None
    net_volume = None

    # Geometry fallbacks (unchanged)
    compas_brep_volume = compas_obb_largest_area = None
    compas_obb_xdim = compas_obb_ydim = compas_obb_zdim = None
    if has_valid_geometry(element):
        compas_obb_xdim, compas_obb_ydim, compas_obb_zdim, compas_obb_largest_area = tesselated_brep_obb(element.geometry, units)
        compas_brep_volume = tesselated_brep_volume(element.geometry, units)

    # IFC quantities via inverse
    for rel in inverse_list(element, "IsDefinedBy"):
        if not rel or not rel.is_a("IfcRelDefinesByProperties"):
            continue

        qset = getattr(rel, "RelatingPropertyDefinition", None)
        if not (qset and qset.is_a("IfcElementQuantity") and hasattr(qset, "Quantities")):
            continue

        for q in qset.Quantities:
            qname = _norm(getattr(q, "Name", "") or "")

            if q.is_a("IfcQuantityVolume") and getattr(q, "VolumeValue", None) is not None:
                v = round(q.VolumeValue, 4)
                if "net" in qname:
                    net_volume = v

            if q.is_a("IfcQuantityArea") and getattr(q, "AreaValue", None) is not None:
                a = round(q.AreaValue, 4)
                if "netsidearea" in qname:
                    net_side_area = a
                elif "netfootprintarea" in qname:
                    net_footprint_area = a
                elif "crosssectionarea" in qname:
                    cross_section_area = a
                elif "netarea" in qname:
                    net_area = a
                elif "netsurfacearea" in qname:
                    net_surface_area = a

            if q.is_a("IfcQuantityLength") and getattr(q, "LengthValue", None) is not None:
                L = round(q.LengthValue, 4)
                if "length" in qname:
                    length = L
                elif "width" in qname:
                    width = L
                elif "height" in qname:
                    height = L
                elif "depth" in qname:
                    depth = L

    if all(v is None for v in (
        width, length, height, depth,
        net_area, net_side_area, net_footprint_area, net_surface_area,
        cross_section_area, net_volume,
        compas_obb_xdim, compas_obb_ydim, compas_obb_zdim,
        compas_obb_largest_area, compas_brep_volume,
    )):
        return None

    return {
        "LENGTHUNIT": units.get("LENGTHUNIT"),
        "AREAUNIT": units.get("AREAUNIT"),
        "VOLUMEUNIT": units.get("VOLUMEUNIT"),
        "width": width, "length": length, "height": height, "depth": depth,
        "net_area": net_area,
        "net_side_area": net_side_area,
        "net_footprint_area": net_footprint_area,
        "net_surface_area": net_surface_area,
        "cross_section_area": cross_section_area,
        "net_volume": net_volume,
        "compas_obb_xdim": compas_obb_xdim,
        "compas_obb_ydim": compas_obb_ydim,
        "compas_obb_zdim": compas_obb_zdim,
        "compas_obb_largest_area": compas_obb_largest_area,
        "compas_brep_volume": compas_brep_volume,
    }


# ------------------------
# Element data (compiled)
# ------------------------

logger = logging.getLogger(__name__)

def process_ifc_element(element, caches, units) -> Optional[Dict[str,Any]]:
    """
    process and compile all available IFC element data into a processd container.

    Parameters
    ----------
    element : compas_ifc.entities.element.IfcBuildingElement
        The IFC element to be processed.
    caches: IfcCaches
        Storage of pre-processed IFC relationship collections for fast lookups.
   units: dict
        dictionary of units as defined by IFC metadata & length conversion factor
        to standardize any computed geometric quantities with compas to m, m^2, m^3

    Returns
    -------
    Dict[str, Any]: A compiled dictionary containing:
        - `metadata`: Basic element identification and classification info.
        - `material_data`: Any linked material or material layer set usage.
        - `properties`: Property sets and type property sets (if any).
        - `quantities`: Geometric and derived quantities (e.g., length, area, volume).
    """
    try:
        metadata = process_metadata(element, caches)
        material_data = process_material_data(element, caches, units)
        psets = process_psets(element)
        quantities = process_quantities(element, units)

        return {
            "metadata": metadata,
            "material_data": material_data,
            "properties": psets,
            "quantities": quantities,
        }

    except Exception as e:
        element_name = getattr(element, "Name", None)
        logger.warning(
            f"Failed to process element {element_name or element}: {type(e).__name__} - {e}"
        )
        return None


# ------------------------
# IFC Model procession
# ------------------------


def process_ifc_model(ifc_dir: Path = Path("data/building_model"), output_dir: Path = Path("temp"), exclude_none: bool = False):
    """
    Process all IfcBuildingElements from the model and preprocess each as a JSON file in `output_dir`.
    This function will convert any IFC model into extraction-ready files for normalization,
    with subsequent directories and predefined dataschemas that are easy to parse and/or give to the LLM

    Not yet implemented: IfcMaterialConstituent(Set) and IfcMaterialProfile(Set) extraction.

    Args:
        ifc_dir: Path to the directory with exactly one IFC file.
        project_folder: Parent directory where the processed output will be stored.
        exclude_none: If True, remove all fields with None recursively from output.

    Returns:
        - A directory structure with exported JSON files for the IfcBuildingElement entities of the IFC model.
    
    Output structure:
        output_dir/
            elements/
                composition/            -> (any element that has a none-empty "is_decomposed_by" dictionary)       
                single_material/        -> (all IfcBuildingElements with one material or one material layer)
                multi_layer/            -> (all IfcBuildingElements with IfcMaterialLayerSet or IfcMaterialLayerSetUsage)
                    <EID>/
                        element.json (+ layer jsons)
                multi_material/         -> (all IfcBuildingElements with IfcMaterialList)
                    <EID>/
                        element.json (+ material jsons)
            metadata/
                compositions.json       -> Lists the composition elements, and all child elements that it is decomposed by.
                multilayers.json        -> Lists all multilayer elements
                multimaterials.json     -> Lists all elements with IfcMaterialList and how many materials are referenced.
                model.json              -> Metadata of the model.
    """

    # Load file path
    print("")
    print("Starting IFC model pre-processing...")
    print("")
    ifc_file = get_single_ifc(ifc_dir)

    # Define desired output process
    subdirs = [
        "elements",
        "elements/composition",
        "elements/single_material",
        "elements/multi_layer",
        "elements/multi_material",
        "metadata",
    ]

    # Create all dirs
    output_dir= Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for rel in subdirs:
        (output_dir/ rel).mkdir(parents=True, exist_ok=True)

    # Load the IFC model, units, caches
    model = load_ifc_file(ifc_file)
    units = load_ifc_units(model)
    caches = IfcCaches(model)
    ifcmeta = load_ifc_metadata(ifc_file, model, units, caches)
    
    # Get appropriate building element entity type based on schema version
    schema_version = model.schema_name
    entity_type = "IfcBuiltElement" if schema_version.upper().startswith("IFC4.3") else "IfcBuildingElement"
    elements = model.get_entities_by_type(entity_type)

    # Initialize & track metadata
    ml_index = init_ml_index()
    mm_index = init_mm_index()
    comp_index = []
    object_type_index = {}

    # print total count and message
    total = len(elements)
    print(f"{entity_type} count: {total}", flush=True)
    print("")
    print(f"Pre-processing all {entity_type} entities...", flush=True)
    processed = 0

    # process all building elements
    for element in elements:
        try:
            data = process_ifc_element(element, caches, units)
            if not data:
                continue

            # dict access
            meta = data.get("metadata") or {}
            eid = meta.get("eid")
            gid = meta.get("global_id")
            name = meta.get("name")
            object_type = meta.get("object_type")

            # if no GlobalId, skip (cannot name file)
            if not eid:
                continue

            if object_type:
                object_type_index.setdefault(object_type, []).append({
                    "name": name,
                    "eid": eid,
                    "global_id": gid,
                })

            mat = data.get("material_data")  # can be None or dict
            mat_entity = (mat or {}).get("entity")

            # composition decision (True if it is decomposed by children)
            is_composition = bool(meta.get("is_decomposed_by"))
            if is_composition:
                bucket = "composition"
                children = meta.get("is_decomposed_by") or []
                comp_index.append({"name": name, "eid": eid, "global_id": gid, "children": children})
            else:
                mat_bucket = classify_material_bucket(mat)  # make sure this accepts dict/None
                bucket = mat_bucket or "single_material"


            # For "IfcMaterialLayerSet", "IfcMaterialLayerSetUsage"
            if bucket == "multi_layer":
                psets = data.get("properties")
                layers = (mat or {}).get("material_layers") or []
                write_multilayer_pkg(
                    output_dir / "elements" / bucket,
                    eid,
                    data,
                    layers,
                    meta,
                    psets,
                )

                if mat_entity in ("IfcMaterialLayerSet", "IfcMaterialLayerSetUsage"):
                    ml_index.setdefault(mat_entity, []).append({"name": name, "eid": eid, "global_id": gid})

            # For "IfcMaterialList"
            elif bucket == "multi_material":
                psets = data.get("properties")
                materials = (mat or {}).get("materials") or []
                write_multimaterial_pkg(
                    output_dir / "elements" / bucket,
                    eid,
                    data,
                    materials,
                    meta,
                    psets
                )

                mm_index.append({"name": name, "eid": eid, "global_id": gid})

            # For rest of the entities in material_data
            else:
                write_json(output_dir / "elements" / bucket / f"{eid}.json", data, exclude_none=exclude_none)

            # update progress and print
            processed += 1
            modulus = 100 if total > 200 else 10
            if processed % modulus == 0 or processed == total:
                print(f"Processed elements: [{processed}/{total}]", flush=True)

        except Exception as e:
            # strongly recommend logging so you can see why elements fail
            logger.warning(
                "Failed to process element %s: %s - %s",
                getattr(element, "Name", None) or getattr(element, "eid", None) or str(element),
                type(e).__name__,
                e,
            )
            continue


    # write metadata files once
    write_meta_ifc(ifcmeta, output_dir)
    write_comp_index(comp_index, output_dir)
    write_ml_index(ml_index, output_dir)
    write_mm_index(mm_index, output_dir)
    write_object_type_index(object_type_index, output_dir)

    print("")
    print("IFC model was successfully pre-processed ✔")
    print(f"Building Data stored in: {output_dir}")



# ------------------------
# PRELIMINARY BILL OF QUANITITIES
# ------------------------

_LAYER_RE = re.compile(r"_L(\d+)\.json$", re.IGNORECASE)
_MATERIAL_RE = re.compile(r"_M(\d+)\.json$", re.IGNORECASE)

def _layer_from_path(p: Path) -> int | None:
    m = _LAYER_RE.search(p.name)
    return int(m.group(1)) if m else None

def _material_from_path(p: Path) -> int | None:
    m = _MATERIAL_RE.search(p.name)
    return int(m.group(1)) if m else None

def process_ifc_model_boq(output_parent: Path | str) -> None:
    output_parent = Path(output_parent)
    processed_directory = output_parent

    if not processed_directory.exists() or not processed_directory.is_dir():
        raise FileNotFoundError(
            f"Required directory not found: {processed_directory.resolve()}\n"
            "Run the IFC preprocessing step first (process_ifc_model)."
        )

    # Directories (as Path objects)
    single_material_dir = processed_directory / "elements" / "single_material"
    multi_layer_dir = processed_directory / "elements" / "multi_layer"
    multi_material_dir = processed_directory / "elements" / "multi_material"

    boq_rows_all: list[dict] = []
    boq_rows_dissected: list[dict] = []

    # Iterate over single material source files
    if single_material_dir.exists() and single_material_dir.is_dir():
        for source_path in single_material_dir.glob("*.json"):
            try:
                with source_path.open("r", encoding="utf-8") as file:
                    data = json.load(file)

                metadata = data.get("metadata", {})
                material = data.get("material_data", {})
                quantities = data.get("quantities", {})

                # material conditionals
                if material.get("entity") in ("IfcMaterialLayerSetUsage", "IfcMaterialLayerSet"):
                    layers = material.get("material_layers") or []
                    material_d = layers[0] if layers else {}
                    material_name = material_d.get("material_name", None)
                    thickness = material_d.get("thickness", None)
                elif material.get("entity") == ("IfcMaterialList"):
                    materials = material.get("materials") or []
                    material_d = materials[0] if materials else {}
                    material_name = material_d.get("material_name", None)
                    thickness = None
                else:
                    material_name = material.get("material_name")
                    thickness = None

                boq_rows_all.append(
                    {
                        "EID": metadata.get("eid", None),
                        "GlobalId": metadata.get("global_id", None),
                        "Name": metadata.get("name", None),
                        "Entity": metadata.get("entity", None),
                        "Object Type": metadata.get("object_type", None),
                        "Material Type": "single_material",
                        "Material Entity": material.get("entity", None),
                        "Material Name(s)": material_name,
                        "Thickness": thickness,
                        "Length": quantities.get("length", None),
                        "Width": quantities.get("width", None),
                        "Height": quantities.get("height", None),
                        "Depth": quantities.get("depth", None),
                        "LENGTHUNIT": quantities.get("LENGTHUNIT"),
                        "Net Area": quantities.get("net_area", None),
                        "Net Side Area": quantities.get("net_side_area", None),
                        "Net Footprint Area": quantities.get("net_footprint_area", None),
                        "Net Surface Area": quantities.get("net_surface_area", None),
                        "Cross-sectional Area": quantities.get("cross_sectional_area", None),
                        "OBB Largest Area": quantities.get("compas_obb_largest_area", None),
                        "AREAUNIT": quantities.get("AREAUNIT"),
                        "Net Volume": quantities.get("net_volume", None),
                        "BRep Volume": quantities.get("compas_brep_volume", None),
                        "VOLUMEUNIT": quantities.get("VOLUMEUNIT"),
                    }
                )

                boq_rows_dissected.append(
                    {
                        "EID": metadata.get("eid", None),
                        "GlobalId": metadata.get("global_id", None),
                        "Name": metadata.get("name", None),
                        "Layer/Material Number": None,
                        "Entity": metadata.get("entity", None),
                        "Object Type": metadata.get("object_type", None),
                        "Material Type": "single_material",
                        "Material Entity": material.get("entity", None),
                        "Material Name": material_name,
                        "Thickness": thickness,
                        "Length": quantities.get("length", None),
                        "Width": quantities.get("width", None),
                        "Height": quantities.get("height", None),
                        "Depth": quantities.get("depth", None),
                        "LENGTHUNIT": quantities.get("LENGTHUNIT"),
                        "Net Area": quantities.get("net_area", None),
                        "Net Side Area": quantities.get("net_side_area", None),
                        "Net Footprint Area": quantities.get("net_footprint_area", None),
                        "Net Surface Area": quantities.get("net_surface_area", None),
                        "Cross-sectional Area": quantities.get("cross_sectional_area", None),
                        "OBB Largest Area": quantities.get("compas_obb_largest_area", None),
                        "AREAUNIT": quantities.get("AREAUNIT"),
                        "Net Volume": quantities.get("net_volume", None),
                        "BRep Volume": quantities.get("compas_brep_volume", None),
                        "VOLUMEUNIT": quantities.get("VOLUMEUNIT"),
                    }
                )

            except Exception as e:
                print(f"[WARN] Skipping {source_path.name}: {e}")

    if multi_layer_dir.exists() and multi_layer_dir.is_dir():
        for element_dir in multi_layer_dir.iterdir():
            if not element_dir.is_dir():
                continue

            eid = element_dir.name

            # --- aggregate file (same as you already do) ---
            source_path = element_dir / f"{eid}.json"
            if not source_path.exists():
                continue

            try:
                with source_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                metadata = data.get("metadata", {}) or {}
                material = data.get("material_data", {}) or {}
                quantities = data.get("quantities", {}) or {}
                layers = material.get("material_layers") or []

                material_names = [
                    layer.get("material_name")
                    for layer in layers
                    if isinstance(layer, dict) and layer.get("material_name")
                ]
                material_name = " | ".join(material_names) if material_names else None

                thickness = sum(
                    (layer.get("thickness") or 0.0)
                    for layer in layers
                    if isinstance(layer, dict)
                )

                boq_rows_all.append(
                    {
                        "EID": metadata.get("eid"),
                        "GlobalId": metadata.get("global_id"),
                        "Name": metadata.get("name"),
                        "Entity": metadata.get("entity"),
                        "Object Type": metadata.get("object_type"),
                        "Material Type": "multi_layer",
                        "Material Entity": material.get("entity"),
                        "Material Name(s)": material_name,
                        "Thickness": thickness,
                        "Length": quantities.get("length", None),
                        "Width": quantities.get("width", None),
                        "Height": quantities.get("height", None),
                        "Depth": quantities.get("depth", None),
                        "LENGTHUNIT": quantities.get("LENGTHUNIT"),
                        "Net Area": quantities.get("net_area", None),
                        "Net Side Area": quantities.get("net_side_area", None),
                        "Net Footprint Area": quantities.get("net_footprint_area", None),
                        "Net Surface Area": quantities.get("net_surface_area", None),
                        "Cross-sectional Area": quantities.get("cross_sectional_area", None),
                        "OBB Largest Area": quantities.get("compas_obb_largest_area", None),
                        "AREAUNIT": quantities.get("AREAUNIT"),
                        "Net Volume": quantities.get("net_volume", None),
                        "BRep Volume": quantities.get("compas_brep_volume", None),
                        "VOLUMEUNIT": quantities.get("VOLUMEUNIT"),
                    }
                )

                # --- nested loop over per-layer files ---
                layer_paths = list(element_dir.glob(f"{eid}_L*.json"))

                # sort by L-number so output is stable
                layer_paths.sort(key=lambda p: (_layer_from_path(p) is None, _layer_from_path(p) or 0))

                for lp in layer_paths:
                    try:
                        layer_no = _layer_from_path(lp)  # 1,2,3,...

                        with lp.open("r", encoding="utf-8") as f:
                            layer_data = json.load(f)

                        target_layer = layer_data.get("target_layer", {}) or {}

                        boq_rows_dissected.append(
                            {
                                "EID": metadata.get("eid"),
                                "GlobalId": metadata.get("global_id"),
                                "Name": metadata.get("name"),
                                "Layer/Material Number": layer_no,
                                "Entity": metadata.get("entity"),
                                "Object Type": metadata.get("object_type"),
                                "Material Type": "multi_layer",
                                "Material Entity": material.get("entity"),
                                "Material Name": target_layer.get("material_name"),
                                "Thickness": target_layer.get("thickness"),
                                "Length": None,
                                "Width": None,
                                "Height": None,
                                "Depth": None,
                                "LENGTHUNIT": quantities.get("LENGTHUNIT"),
                                "Net Area": None,
                                "Net Side Area": None,
                                "Net Footprint Area": None,
                                "Net Surface Area": None,
                                "Cross-sectional Area": None,
                                "OBB Largest Area": None,
                                "AREAUNIT": quantities.get("AREAUNIT"),
                                "Net Volume": None,
                                "BRep Volume": None,
                                "VOLUMEUNIT": quantities.get("VOLUMEUNIT"),
                            }
                        )

                    except Exception as e:
                        print(f"[WARN] Skipping layer file {lp}: {e}")

            except Exception as e:
                print(f"[WARN] Skipping {source_path}: {e}")


    if multi_material_dir.exists() and multi_material_dir.is_dir():
        for element_dir in multi_material_dir.iterdir():
            if not element_dir.is_dir():
                continue

            eid = element_dir.name

            # Only pick the JSON whose filename matches the directory name
            source_path = element_dir / f"{element_dir.name}.json"
            if not source_path.exists():
                continue

            try:
                with source_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                metadata = data.get("metadata", {})
                material = data.get("material_data", {})
                quantities = data.get("quantities", {})
                materials = material.get("materials") or []

                # Collect all material names
                material_names = [
                    m.get("material_name")
                    for m in materials
                    if isinstance(m, dict) and m.get("material_name")
                ]

                # Join into one CSV-safe string
                material_name = " | ".join(material_names) if material_names else None

                # IfcMaterialList has no thicknesses
                thickness = None

                boq_rows_all.append(
                    {
                        "EID": metadata.get("eid", None),
                        "GlobalId": metadata.get("global_id", None),
                        "Name": metadata.get("name", None),
                        "Entity": metadata.get("entity", None),
                        "Object Type": metadata.get("object_type", None),
                        "Material Type": "multi_material",
                        "Material Entity": material.get("entity", None),
                        "Material Name(s)": material_name,
                        "Length": quantities.get("length", None),
                        "Width": quantities.get("width", None),
                        "Height": quantities.get("height", None),
                        "Depth": quantities.get("depth", None),
                        "LENGTHUNIT": quantities.get("LENGTHUNIT"),
                        "Net Area": quantities.get("net_area", None),
                        "Net Side Area": quantities.get("net_side_area", None),
                        "Net Footprint Area": quantities.get("net_footprint_area", None),
                        "Net Surface Area": quantities.get("net_surface_area", None),
                        "Cross-sectional Area": quantities.get("cross_sectional_area", None),
                        "OBB Largest Area": quantities.get("compas_obb_largest_area", None),
                        "AREAUNIT": quantities.get("AREAUNIT"),
                        "Net Volume": quantities.get("net_volume", None),
                        "BRep Volume": quantities.get("compas_brep_volume", None),
                        "VOLUMEUNIT": quantities.get("VOLUMEUNIT"),
                    }
                )

                # --- nested loop over per-material files ---
                material_paths = list(element_dir.glob(f"{eid}_M*.json"))

                # sort by M-number so output is stable
                material_paths.sort(key=lambda p: (_material_from_path(p) is None, _material_from_path(p) or 0))

                for mp in material_paths:
                    try:
                        material_no = _material_from_path(mp)  # 1,2,3,...

                        with mp.open("r", encoding="utf-8") as f:
                            material_data = json.load(f)

                        target_material = material_data.get("target_material", {}) or {}

                        boq_rows_dissected.append(
                            {
                                "EID": metadata.get("eid"),
                                "GlobalId": metadata.get("global_id"),
                                "Name": metadata.get("name"),
                                "Layer/Material Number": material_no,
                                "Entity": metadata.get("entity"),
                                "Object Type": metadata.get("object_type"),
                                "Material Type": "multi_material",
                                "Material Entity": material.get("entity"),
                                "Material Name": target_material.get("material_name"),
                                "Thickness": None,
                                "Length": None,
                                "Width": None,
                                "Height": None,
                                "Depth": None,
                                "LENGTHUNIT": quantities.get("LENGTHUNIT"),
                                "Net Area": None,
                                "Net Side Area": None,
                                "Net Footprint Area": None,
                                "Net Surface Area": None,
                                "Cross-sectional Area": None,
                                "OBB Largest Area": None,
                                "AREAUNIT": quantities.get("AREAUNIT"),
                                "Net Volume": None,
                                "BRep Volume": None,
                                "VOLUMEUNIT": quantities.get("VOLUMEUNIT"),
                            }
                        )

                    except Exception as e:
                        print(f"[WARN] Skipping layer file {mp}: {e}")

            except Exception as e:
                print(f"[WARN] Skipping {source_path}: {e}")


    # Export the Bill of Quantities to a CSV file
    boq_all_output_path = processed_directory / "BoQ_01_all.csv"
    boq_all_fieldnames = [
        "EID",
        "GlobalId",
        "Name",
        "Entity",
        "Object Type",
        "Material Type",
        "Material Entity",
        "Material Name(s)",
        "Thickness",
        "Length",
        "Width",
        "Height",
        "Depth",
        "LENGTHUNIT",
        "Net Area",
        "Net Side Area",
        "Net Footprint Area",
        "Net Surface Area",
        "Cross-sectional Area",
        "OBB Largest Area",
        "AREAUNIT",
        "Net Volume",
        "BRep Volume",
        "VOLUMEUNIT",
    ]

    with boq_all_output_path.open("w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=boq_all_fieldnames)
        writer.writeheader()
        writer.writerows(boq_rows_all)

    boq_dissected_output_path = processed_directory / "BoQ_01_dissected.csv"
    boq_dissected_fieldnames = [
        "EID",
        "GlobalId",
        "Name",
        "Layer/Material Number",
        "Entity",
        "Object Type",
        "Material Type",
        "Material Entity",
        "Material Name",
        "Thickness",
        "Length",
        "Width",
        "Height",
        "Depth",
        "LENGTHUNIT",
        "Net Area",
        "Net Side Area",
        "Net Footprint Area",
        "Net Surface Area",
        "Cross-sectional Area",
        "OBB Largest Area",
        "AREAUNIT",
        "Net Volume",
        "BRep Volume",
        "VOLUMEUNIT",
    ]

    with boq_dissected_output_path.open("w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=boq_dissected_fieldnames)
        writer.writeheader()
        writer.writerows(boq_rows_dissected)

    print(f"Preliminary BoQ of entire elements stored in: {boq_all_output_path}. Rows written: {len(boq_rows_all)}")
    print(f"Preliminary BoQ of dissected elements stored in: {boq_dissected_output_path}. Rows written: {len(boq_rows_dissected)}")
    print("")
