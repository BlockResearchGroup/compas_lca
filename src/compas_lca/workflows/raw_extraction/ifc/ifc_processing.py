"""
Functions to ensure a standardized BaseModel format (JSON-serializable) for
each IfcBuildingElement within an IFC model. It serves as the pre-processing
of each element into a format which is then used for the agent-based procession
workflow, generating a reliable quantity take-off for downstream LCA calculation,
etc. Right now, it focuses almost exclusively on IFC2x3 and has not yet been
trialed for later IFC versions.
"""

from pathlib import Path

from typing import Optional

import logging

from .ifc_element import IfcElementMetadata
from .ifc_element import IfcMaterial
from .ifc_element import IfcMaterialList
from .ifc_element import IfcMaterialLayer
from .ifc_element import IfcMaterialLayerSet
from .ifc_element import IfcMaterialLayerSetUsage
from .ifc_element import MaterialAssociation
from .ifc_element import IfcElementProperties
from .ifc_element import IfcElementQuantities
from .ifc_element import IfcElementData

from .ifc_caches import IfcCaches

from .ifc_readers import load_ifc_file
from .ifc_readers import load_ifc_units
from .ifc_readers import load_ifc_metadata

from .ifc_helpers import get_single_ifc
from .ifc_helpers import clean_value
from .ifc_helpers import write_bytes
from .ifc_helpers import norm_objtype
from .ifc_helpers import get_hierarchy
from .ifc_helpers import get_material_props
from .ifc_helpers import has_valid_geometry
from .ifc_helpers import get_classification
from .ifc_helpers import tesselated_brep_obb
from .ifc_helpers import tesselated_brep_volume
from .ifc_helpers import classify_material_bucket
from .ifc_helpers import update_rep_index
from .ifc_helpers import init_rep_index
from .ifc_helpers import init_ml_index
from .ifc_helpers import init_mm_index
from .ifc_helpers import write_rep_index
from .ifc_helpers import write_ml_index
from .ifc_helpers import write_mm_index
from .ifc_helpers import write_comp_index
from .ifc_helpers import write_meta_ifc
from .ifc_helpers import write_multilayer_pkg
from .ifc_helpers import write_multimaterial_pkg
from .ifc_helpers import NO_OBJTYPE

# ------------------------
# Metadata
# ------------------------
def process_metadata(element, caches) -> IfcElementMetadata:
    """process IFC element metadata and return a validated IfcElementMetadata instance."""
    name = getattr(element, "Name", None)
    global_id = getattr(element, "GlobalId", None)
    entity= type(element).__name__
    object_type = getattr(element, "ObjectType", None)
    description = getattr(element, "Description", None)
    classification = get_classification(element, caches.classification_rels)
    decomposes, is_decomposed_by = get_hierarchy(element, caches.aggregates_rels)

    return IfcElementMetadata(
        name=name,
        global_id=global_id,
        entity=entity,
        object_type=object_type,
        description=description,
        classification=classification,
        decomposes=decomposes,
        is_decomposed_by=is_decomposed_by,
    )

# ------------------------
# Material associations
# ------------------------
def process_material(relating_material, caches) -> IfcMaterial:
    """process material and return a validated IfcMaterial instance."""
    return IfcMaterial(
        entity="IfcMaterial",
        material_name=getattr(relating_material, "Name", None),
        material_description=getattr(relating_material, "Description", None),
        material_category=getattr(relating_material, "Category", None),
        material_properties=get_material_props(relating_material, caches),
    )

def process_material_list(relating_material, caches) -> IfcMaterialList:
    mats = getattr(relating_material, "Materials", None) or []
    return IfcMaterialList(
        entity="IfcMaterialList",
        materials=[process_material(m, caches) for m in mats if m is not None],
    )

def process_layer(relating_material, caches, units) -> IfcMaterialLayer:
    mat = getattr(relating_material, "Material", None)
    return IfcMaterialLayer(
        material_name=getattr(mat, "Name", None) if mat else None,
        material_description=getattr(mat, "Description", None) if mat else None,
        thickness=getattr(relating_material, "LayerThickness", None),
        thickness_unit=units.get("LENGTHUNIT"),
        is_ventilated=getattr(relating_material, "IsVentilated", None),
        material_properties=get_material_props(mat, caches) if mat else None,
    )

def process_layerset(relating_material, caches, units) -> IfcMaterialLayerSet:
    layers = getattr(relating_material, "MaterialLayers", None) or []
    return IfcMaterialLayerSet(
        entity="IfcMaterialLayerSet",
        layer_set_name=getattr(relating_material, "LayerSetName", None),
        layer_set_description=getattr(relating_material, "Description", None),
        material_layers=[process_layer(l, caches, units) for l in layers],
    )

def process_layerset_usage(relating_material, caches, units) -> IfcMaterialLayerSetUsage:
    layer_set = getattr(relating_material, "ForLayerSet", None)
    layers = getattr(layer_set, "MaterialLayers", None) or []
    return IfcMaterialLayerSetUsage(
        entity="IfcMaterialLayerSetUsage",
        layer_set_name=getattr(layer_set, "LayerSetName", None) if layer_set else None,
        layer_set_description=getattr(layer_set, "Description", None) if layer_set else None,
        material_layers=[process_layer(l, caches, units) for l in layers],
        layer_set_direction=str(getattr(relating_material, "LayerSetDirection", None)),
        direction_sense=str(getattr(relating_material, "DirectionSense", None)),
    )

def process_material_data(element, caches, units) -> Optional[MaterialAssociation]:
    """
    Return the *best* material association for an element.
    Preference: IfcMaterialLayerSetUsage > IfcMaterialLayerSet > IfcMaterialList > IfcMaterial.
    Falls back to the element's type if the occurrence has none.
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
        # Find the element's type via IfcRelDefinesByType
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
def process_psets(element, caches) -> Optional[IfcElementProperties]:
    """process property sets for element and its type."""
    psets_element = {}
    psets_type = {}

    # Element property sets
    for rel in getattr(caches, "property_rels", []) or []:
        related = getattr(rel, "RelatedObjects", None) or []
        if element in related:
            prop_set = getattr(rel, "RelatingPropertyDefinition", None)
            if prop_set and prop_set.is_a("IfcPropertySet"):
                for prop in getattr(prop_set, "HasProperties", None) or []:
                    if hasattr(prop, "Name") and hasattr(prop, "NominalValue"):
                        raw_value = getattr(prop, "NominalValue", None)
                        if raw_value is not None:
                            psets_element[prop.Name] = clean_value(str(raw_value))

    # Type property sets
    for rel in getattr(caches, "type_rels", []) or []:
        related = getattr(rel, "RelatedObjects", None) or []
        if element in related:
            object_type = getattr(rel, "RelatingType", None)
            if object_type and hasattr(object_type, "HasPropertySets"):
                for pset in getattr(object_type, "HasPropertySets", None) or []:
                    if pset.is_a("IfcPropertySet"):
                        for prop in getattr(pset, "HasProperties", None) or []:
                            if hasattr(prop, "Name") and hasattr(prop, "NominalValue"):
                                raw_value = getattr(prop, "NominalValue", None)
                                if raw_value is not None:
                                    key = f"{pset.Name}.{prop.Name}"
                                    psets_type[key] = clean_value(str(raw_value))

    if not psets_element and not psets_type:
        return None

    return IfcElementProperties(
        psets_element=psets_element or None,
        psets_type=psets_type or None,
    )

# ------------------------
# Quantities
# ------------------------

def _norm(name: str) -> str:
    # lower + remove spaces/underscores for robust matching
    return (name or "").lower().replace(" ", "").replace("_", "")

def process_quantities(element, caches, units) -> Optional[IfcElementQuantities]:
    # Initialize all outputs (None by default)
    width = length = height = depth = None
    net_area = None
    net_side_area = None
    net_footprint_area = None
    cross_section_area = None
    net_surface_area = None
    net_volume = None

    # Always attempt geometry-based fallbacks (independent of property sets)
    compas_brep_volume = compas_obb_largest_area = compas_obb_xdim = compas_obb_ydim = compas_obb_zdim = None
    if has_valid_geometry(element):
        compas_obb_xdim, compas_obb_ydim, compas_obb_zdim, compas_obb_largest_area = tesselated_brep_obb(element.geometry, units)
        compas_brep_volume = tesselated_brep_volume(element.geometry, units)

    # IFC quantities (these may or may not exist)
    for rel in getattr(caches, "property_rels", []):
        if element not in getattr(rel, "RelatedObjects", []):
            continue

        qset = getattr(rel, "RelatingPropertyDefinition", None)
        if not (qset and qset.is_a("IfcElementQuantity") and hasattr(qset, "Quantities")):
            continue

        for q in qset.Quantities:
            qname_raw = getattr(q, "Name", "") or ""
            qname = _norm(qname_raw)

            # --- Volume ---
            if q.is_a("IfcQuantityVolume") and getattr(q, "VolumeValue", None) is not None:
                v = round(q.VolumeValue, 4)
                if "net" in qname:
                    net_volume = v

            # --- Area ---
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

            # --- Length ---
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

    # If absolutely nothing (including geometry fallbacks) was found, return None
    if all(v is None for v in (
        width, length, height, depth,
        net_area, net_side_area, net_footprint_area, net_surface_area,
        cross_section_area, net_volume,
        compas_obb_xdim, compas_obb_ydim, compas_obb_zdim,
        compas_obb_largest_area, compas_brep_volume,
    )):
        return None

    return IfcElementQuantities(
        LENGTHUNIT=units.get("LENGTHUNIT"),
        AREAUNIT=units.get("AREAUNIT"),
        VOLUMEUNIT=units.get("VOLUMEUNIT"),
        width=width, length=length, height=height, depth=depth,
        net_area=net_area,
        net_side_area=net_side_area,
        net_footprint_area=net_footprint_area,
        net_surface_area=net_surface_area,
        cross_section_area=cross_section_area,
        net_volume=net_volume,
        compas_obb_xdim=compas_obb_xdim,
        compas_obb_ydim=compas_obb_ydim,
        compas_obb_zdim=compas_obb_zdim,
        compas_obb_largest_area=compas_obb_largest_area,
        compas_brep_volume=compas_brep_volume
    )



# ------------------------
# Element data (compiled)
# ------------------------

logger = logging.getLogger(__name__)

def process_ifc_element(element, caches, units) -> IfcElementData:
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
    IfcElementData: A compiled Pydantic model containing:
        - `metadata`: Basic element identification and classification info.
        - `material_data`: Any linked material or material layer set usage.
        - `properties`: Property sets and type property sets (if any).
        - `quantities`: Geometric and derived quantities (e.g., length, area, volume).
    """
    try:
        metadata = process_metadata(element, caches)
        material_data = process_material_data(element, caches, units)
        psets = process_psets(element, caches)
        quantities = process_quantities(element, caches, units)

        return IfcElementData(
            metadata=metadata,
            material_data=material_data,
            properties=psets,
            quantities=quantities,
        )

    except Exception as e:
        element_name = getattr(element, "Name", None)
        logger.warning(
            f"Failed to process element {element_name or element}: {type(e).__name__} - {e}"
        )
        return None


# ------------------------
# IFC Model procession
# ------------------------


def process_ifc_model(ifc_dir: Path = Path("data/input/ifc"), output_parent: Path = Path("temp"), exclude_none: bool = False):
    """process all IFC elements from the model and write each as a JSON file in `output_dir`.
    This function will convert any IFC model into processing-ready files for the compas_lca pipeline,
    with subsequent directories and predefined dataschemas that are easy to parse and/or give to the LLM

    TO-DO: Add IfcMaterialConstituent(Set) and IfcMaterialProfile(Set) to processing pipeline.

    Args:
        ifc_dir: Path to the directory with exactly one IFC file.
        output_parent: Parent directory where new directory with IFC file stem name will be created and JSON files will be written (created if missing).
        exclude_none: If True, remove all fields with None recursively from output.

    Returns:
        - A directory process with exported JSON files for the IfcBuildingElement entities of the IFC model.
        process:
        output_dir/
            all/
                compositions/       
                    (any element that has a none-empty "is_decomposed_by" dictionary)
                elements/           
                    (all IfcBuildingElements with one material or one material layer, and no composition)
                multilayers/        
                    (all IfcBuildingElements that have IfcMaterialLayerSet or IfcMaterialLayerSetUsage, 
                    and the number of material layers is > 1)
                    All elements stored as folders (with GlobalId), inside JSON files for element and for each layer.
                multimaterials/
                    (all IfcBuildingElements with IfcMaterialList, i.e., multiple materials but no quants,
                    and number of materials is >1)
            metadata/
                representatives.json    -> Stores overview of unique ObjectTypes and lists elements that belong to this (+ representative).
                compositions.json       -> Lists the composition elements, and all child elements that it is decomposed by.
                multilayers.json        -> Lists all multilayer elements
                multimaterials.json     -> Lists all elements with IfcMaterialList and how many materials are referenced.
                model.json              -> Metadata of the model.
            representatives/ ---->  Same process as all/ (without compositions), stores one representative
                                    element, multilayer, multimaterial for each unique ObjectType (or copy if
                                    no ObjectType). Reduced amount of inferences required downstream.
                elements/       (representative element for a unique object type)
                multilayers/    (representative multilayer element for a unique object type)
                multimaterials/ (representative material list element for a unique object type)
    """

    # Load file path
    ifc_file = get_single_ifc(ifc_dir)

    # Define desired output process
    subdirs = [
        "all",
        "all/compositions",
        "all/elements",
        "all/multilayers",
        "all/multimaterials",
        "metadata",
        "representatives",
        "representatives/elements",
        "representatives/multilayers",
        "representatives/multimaterials"
    ]

    # Create all dirs
    output_dir = Path(output_parent) / ifc_file.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    for rel in subdirs:
        p = output_dir / rel
        p.mkdir(parents=True, exist_ok=True)

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
    rep_index = init_rep_index()
    ml_index = init_ml_index()
    mm_index = init_mm_index()
    comp_index = []

    # print total count and start message
    total = len(elements)
    print(f"{entity_type} count: {total}", flush=True)
    print("")
    print("processing...", flush=True)
    processed = 0

    # process all building elements
    for element in elements:
        try:
            data = process_ifc_element(element, caches, units)
            if not data:
                continue

            # get relevant attributes for metadata & conditionals
            meta = data.metadata
            if not meta:
                continue
            name = meta.name
            gid = meta.global_id
            obj_type = meta.object_type
            mat = data.material_data
            mat_entity = getattr(mat, "entity", None) or []

            # composition decision (bool = True if it is decomposed by childern)
            is_composition = bool(getattr(meta, "is_decomposed_by", None))
            if is_composition:
                bucket = "compositions"
                children = getattr(meta, "is_decomposed_by", None) or []
                comp_index.append({"name": name, "global_id": gid, "children": children})
            else:
                mat_bucket = classify_material_bucket(getattr(data, "material_data", None))
                bucket = mat_bucket or "elements"

            # serialize once directly to JSON bytes
            json_str = data.model_dump_json(exclude_none=exclude_none, by_alias=True, indent=2)
            json_blob = json_str.encode("utf-8")

            # For "IfcMaterialLayerSet", "IfcMaterialLayerSetUsage"
            if bucket == "multilayers": 
                metadata = getattr(data, "metadata", None)
                layers = getattr(getattr(data, "material_data", None), "material_layers", None) or []
                write_multilayer_pkg(output_dir / "all" / bucket, gid, json_blob, layers, metadata) # Writes element + dissected layers in GlobalId folder
                if mat_entity in ("IfcMaterialLayerSet", "IfcMaterialLayerSetUsage"):
                    ml_index.setdefault(mat_entity, []).append({"name": name, "global_id": gid})
            
            # For "IfcMaterialList"
            elif bucket == "multimaterials": 
                mm_index.append({"name": name, "global_id": gid})
                metadata = getattr(data, "metadata", None)
                materials = getattr(getattr(data, "material_data", None), "materials", None) or []
                write_multimaterial_pkg(output_dir / "all" / bucket, gid, json_blob, materials, metadata) # Writes element + dissected materials in folder

            # For rest of the entities in material_data
            else: 
                write_bytes(output_dir / "all" / bucket / f"{gid}.json", json_blob) # Flat write for non-multilayer elements

            # representative on first-seen object_type (only non-compositions)
            if not is_composition:
                became_rep = update_rep_index(rep_index, obj_type, name, gid)
                norm_type = norm_objtype(obj_type)
                write_rep = (norm_type == NO_OBJTYPE) or became_rep

                # write representatives
                if write_rep:
                    if bucket == "multilayers":
                        metadata = getattr(data, "metadata", None)
                        layers = getattr(mat, "material_layers", None) or []
                        write_multilayer_pkg(output_dir / "representatives" / bucket, gid, json_blob, layers, metadata)
                    elif bucket == "multimaterials":
                        metadata = getattr(data, "metadata", None)
                        materials = getattr(mat, "materials", None) or []
                        write_multimaterial_pkg(output_dir / "representatives" / bucket, gid, json_blob, materials, metadata)
                    else:
                        write_bytes(output_dir / "representatives" / "elements" / f"{gid}.json", json_blob)


            # update progress and print
            processed += 1
            modulus = 100 if total > 200 else 10
            if processed % modulus == 0 or processed == total:
                print(f"processed elements: [{processed}/{total}]", flush=True)

        except Exception:
            continue

    # write metadata files once
    write_meta_ifc(ifcmeta, output_dir)
    write_rep_index(rep_index, output_dir)
    write_comp_index(comp_index, output_dir)
    write_ml_index(ml_index, output_dir)
    write_mm_index(mm_index, output_dir)

    print("")
    print(f"Done!")
    print(f"IFC file was successfully processed ✔")
    print(f"processed data stored in: {output_dir}")
