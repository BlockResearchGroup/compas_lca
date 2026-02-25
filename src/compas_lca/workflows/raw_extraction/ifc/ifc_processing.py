import logging

from pathlib import Path

from collections import defaultdict

from typing import Optional
from typing import DefaultDict
from typing import Dict
from typing import Any
from typing import Set
from typing import List

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


def process_ifc_model(
    ifc_dir: Path = Path("data/building_model"),
    output_dir: Path = Path("temp"),
    exclude_none: bool = False,
    config: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Process all IfcBuildingElements from the model and preprocess each as a JSON file in `output_dir`.
    This function will convert any IFC model into extraction-ready files for normalization,
    with subsequent directories and predefined dataschemas that are easy to parse and/or give to the LLM

    Not yet implemented: IfcMaterialConstituent(Set) and IfcMaterialProfile(Set) extraction.

    Args:
        ifc_dir: Path to the directory with exactly one IFC file.
        project_folder: Parent directory where the processed output will be stored.
        exclude_none: If True, remove all fields with None recursively from output.
        config: Optional dictionary to exclude certain IFC entity types from processing and output
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
                no_material/            -> (all IfcBuildingElements with no material associations)
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
        "elements/no_material",
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

    # Filter optional IFC entities based on config
    allowed_entities: Optional[Set[str]] = None
    excluded_entities: Set[str] = set()
    if config:
        excluded_entities = {k for k, v in config.items() if v is False}
        if excluded_entities:
            allowed_entities = {k for k, v in config.items() if v is True}

    # Get appropriate building element entity type based on schema version
    schema_version = model.schema_name
    entity_type = "IfcBuiltElement" if schema_version.upper().startswith("IFC4.3") else "IfcBuildingElement"
    elements = model.get_entities_by_type(entity_type)

    # Initialize & track metadata
    ml_index = init_ml_index()
    mm_index = init_mm_index()
    comp_index = []
    object_type_index = {}
    skipped: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)
    skipped_total = 0

    # print total count and message
    total = len(elements)
    print(f"{entity_type} count: {total}", flush=True)
    print("")
    print(f"Pre-processing all {entity_type} entities...", flush=True)
    processed = 0

    # process all building elements
    for element in elements:
        try:

            # Entity filtering
            if allowed_entities is not None:
                elem_type = element.is_a()
                if elem_type not in allowed_entities:
                    name = getattr(element, "Name", None)
                    gid = getattr(element, "GlobalId", None)

                    skipped[elem_type].append({
                        "name": name,
                        "global_id": gid,
                    })
                    skipped_total += 1
                    continue

            # Process IfcBuildingElement
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

            mat = data.get("material_data")  # can be None or dict
            mat_entity = (mat or {}).get("entity")

            # composition decision (True if it is decomposed by children)
            is_composition = bool(meta.get("is_decomposed_by"))

            # ONLY index non-composition elements
            if object_type and not is_composition:
                object_type_index.setdefault(object_type, []).append({
                    "name": name,
                    "eid": eid,
                    "global_id": gid,
                })

            if is_composition:
                bucket = "composition"
                children = meta.get("is_decomposed_by") or []
                comp_index.append({"name": name, "eid": eid, "global_id": gid, "children": children})
            else:
                bucket = classify_material_bucket(mat)  # should return single/multi/no buckets

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

    # Track skipped entities if any filtering was applied, and write metadata
    if allowed_entities is not None:
        skipped_breakdown = {t: len(items) for t, items in skipped.items()}

        # List names by type (and keep global_id if you want)
        skipped_elements_by_type = {
            t: [x["name"] for x in items if x.get("name")]
            for t, items in skipped.items()
        }

        ifcmeta["Skipped Elements Overview"] = {
            "Filter Active": True,
            "Excluded IFC Types": sorted(excluded_entities),
            "Total Skipped Elements": skipped_total,
            "Breakdown by Type": skipped_breakdown,
            "Skipped Element Names by Type": skipped_elements_by_type,
            # optionally keep the richer records instead of names-only:
            # "Skipped Elements (records)": dict(skipped),
        }
    else:
        ifcmeta["Skipped Elements Overview"] = {
            "Filter Active": False,
            "Total Skipped Elements": 0,
            "Breakdown by Type": {},
            "Skipped Element Names by Type": {},
        }

    # write metadata files once
    write_meta_ifc(ifcmeta, output_dir)
    write_comp_index(comp_index, output_dir)
    write_ml_index(ml_index, output_dir)
    write_mm_index(mm_index, output_dir)
    write_object_type_index(object_type_index, output_dir)

    print("")
    print("IFC model was successfully pre-processed ✔")
    print(f"Building Data stored in: {output_dir}")