from pathlib import Path

import json

from typing import Optional
from typing import Any

from .helpers import get_classification
from .helpers import get_hierarchy
from .helpers import get_material_props
from .helpers import clean_value

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

from .ifc_readers import load_ifc_file
from .ifc_readers import load_ifc_units

from .ifc_caches import IfcCaches

import logging
logger = logging.getLogger(__name__)

# ------------------------
# Metadata
# ------------------------
def extract_metadata(element, caches) -> IfcElementMetadata:
    """Extract IFC element metadata and return a validated IfcElementMetadata instance."""
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
def extract_material(relating_material, caches) -> IfcMaterial:
    """Extract material and return a validated IfcMaterial instance."""
    return IfcMaterial(
        entity="IfcMaterial",
        material_name=getattr(relating_material, "Name", None),
        material_description=getattr(relating_material, "Description", None),
        material_category=getattr(relating_material, "Category", None),
        material_properties=get_material_props(relating_material, caches),
    )

def extract_material_list(relating_material, caches) -> IfcMaterialList:
    mats = getattr(relating_material, "Materials", None) or []
    return IfcMaterialList(
        entity="IfcMaterialList",
        materials=[extract_material(m, caches) for m in mats if m is not None],
    )

def extract_layer(relating_material, caches, units) -> IfcMaterialLayer:
    mat = getattr(relating_material, "Material", None)
    return IfcMaterialLayer(
        material_name=getattr(mat, "Name", None) if mat else None,
        material_description=getattr(mat, "Description", None) if mat else None,
        thickness=getattr(relating_material, "LayerThickness", None),
        thickness_unit=units.get("LENGTHUNIT"),
        is_ventilated=getattr(relating_material, "IsVentilated", None),
        material_properties=get_material_props(mat, caches) if mat else None,
    )

def extract_layerset(relating_material, caches) -> IfcMaterialLayerSet:
    layers = getattr(relating_material, "MaterialLayers", None) or []
    return IfcMaterialLayerSet(
        entity="IfcMaterialLayerSet",
        layer_set_name=getattr(relating_material, "LayerSetName", None),
        layer_set_description=getattr(relating_material, "Description", None),
        material_layers=[extract_layer(l, caches) for l in layers],
    )

def extract_layerset_usage(relating_material, caches) -> IfcMaterialLayerSetUsage:
    layer_set = getattr(relating_material, "ForLayerSet", None)
    layers = getattr(layer_set, "MaterialLayers", None) or []
    return IfcMaterialLayerSetUsage(
        entity="IfcMaterialLayerSetUsage",
        layer_set_name=getattr(layer_set, "LayerSetName", None) if layer_set else None,
        layer_set_description=getattr(layer_set, "Description", None) if layer_set else None,
        material_layers=[extract_layer(l, caches) for l in layers],
        layer_set_direction=str(getattr(relating_material, "LayerSetDirection", None)),
        direction_sense=str(getattr(relating_material, "DirectionSense", None)),
    )

def extract_material_data(element, caches) -> Optional[MaterialAssociation]:
    """
    Return the *best* material association for an element.
    Preference: IfcMaterialLayerSetUsage > IfcMaterialLayerSet > IfcMaterialList > IfcMaterial.
    Falls back to the element's type if the occurrence has none.
    """

    def _kind(x):
        return x.is_a() if hasattr(x, "is_a") else type(x).__name__

    # 1) Gather all material rels attached to the *element*
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

    # 2) If nothing on the element, try the *type*
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
        return extract_layerset_usage(rel_mat, caches)
    elif kind == "IfcMaterialLayerSet":
        return extract_layerset(rel_mat, caches)
    elif kind == "IfcMaterialList":
        return extract_material_list(rel_mat, caches)
    elif kind == "IfcMaterial":
        return extract_material(rel_mat, caches)
    # Unknown kinds are ignored gracefully
    return None


# ------------------------
# Property Sets
# ------------------------
def extract_psets(element, caches) -> Optional[IfcElementProperties]:
    """Extract property sets for element and its type."""
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

def extract_quantities(element, caches, units) -> Optional[IfcElementQuantities]:
    # Initialize all outputs (None by default)
    width = length = height = depth = None
    gross_area = net_area = None
    gross_side_area = net_side_area = None
    gross_footprint_area = net_footprint_area = None
    cross_section_area = None
    gross_volume = net_volume = None

    for rel in getattr(caches, "property_rels", []):
        if element not in getattr(rel, "RelatedObjects", []):
            continue

        qset = getattr(rel, "RelatingPropertyDefinition", None)
        if not (qset and qset.is_a("IfcElementQuantity") and hasattr(qset, "Quantities")):
            continue

        for q in qset.Quantities:
            qname_raw = getattr(q, "Name", "") or ""
            qname = _norm(qname_raw)  # e.g. "grossfootprintarea", "grosssidearea", etc.

            # Volumes (m³)
            if q.is_a("IfcQuantityVolume") and hasattr(q, "VolumeValue") and q.VolumeValue is not None:
                v = round(q.VolumeValue, 4)
                if "gross" in qname:
                    gross_volume = v
                elif "net" in qname:
                    net_volume = v

            # Areas (m²)
            if q.is_a("IfcQuantityArea") and hasattr(q, "AreaValue") and q.AreaValue is not None:
                a = round(q.AreaValue, 4)

                # names often used in Qto_* sets
                if "grosssidearea" in qname:
                    gross_side_area = a
                elif "netsidearea" in qname:
                    net_side_area = a
                elif "grossfootprintarea" in qname:
                    gross_footprint_area = a
                elif "netfootprintarea" in qname:
                    net_footprint_area = a
                elif "crosssectionarea" in qname:
                    cross_section_area = a
                elif "grossarea" in qname:
                    gross_area = a
                elif "netarea" in qname:
                    net_area = a

            # Lengths (m)
            if q.is_a("IfcQuantityLength") and hasattr(q, "LengthValue") and q.LengthValue is not None:
                L = round(q.LengthValue, 4)
                if "length" in qname:
                    length = L
                elif "width" in qname:
                    width = L
                elif "height" in qname:
                    height = L
                elif "depth" in qname:
                    depth = L

    # If nothing was found at all, return None (Optional[])
    if all(v is None for v in (
        width, length, height, depth,
        gross_area, net_area, gross_side_area, net_side_area,
        gross_footprint_area, net_footprint_area, cross_section_area,
        gross_volume, net_volume
    )):
        return None

    return IfcElementQuantities(
        length_unit=units.get("LENGTHUNIT"),
        area_unit=units.get("AREAUNIT"),
        volume_unit=units.get("VOLUMEUNIT"),
        width=width, length=length, height=height, depth=depth,
        gross_area=gross_area, net_area=net_area,
        gross_side_area=gross_side_area, net_side_area=net_side_area,
        gross_footprint_area=gross_footprint_area, net_footprint_area=net_footprint_area,
        cross_section_area=cross_section_area,
        gross_volume=gross_volume, net_volume=net_volume,
    )


# ------------------------
# Element data (compiled)
# ------------------------
def extract_ifc_element(element, caches, units) -> IfcElementData:
    """
    Extract and compile all available IFC element data into a structured container.

    Parameters
    ----------
    element : compas_ifc.entities.element.IfcBuildingElement
        The IFC element to be extracted.
    caches: IfcCaches
        Storage of pre-extracted IFC relationship collections for fast lookups.
    lc_factor: float
        length conversion factor to convert model dimensions to meters

    Returns
    -------
    IfcElementData: A compiled Pydantic model containing:
        - `metadata`: Basic element identification and classification info.
        - `material_data`: Any linked material or material layer set usage.
        - `properties`: Property sets and type property sets (if any).
        - `quantities`: Geometric and derived quantities (e.g., length, area, volume).
    """
    try:
        metadata = extract_metadata(element, caches)
        material_data = extract_material_data(element, caches)
        psets = extract_psets(element, caches)
        quantities = extract_quantities(element, caches, units)

        return IfcElementData(
            metadata=metadata,
            material_data=material_data,
            properties=psets,
            quantities=quantities,
        )

    except Exception as e:
        element_name = getattr(element, "Name", None)
        logger.warning(
            f"Failed to extract element {element_name or element}: {type(e).__name__} - {e}"
        )
        return None


# ------------------------
# IFC Model extraction
# ------------------------


def extract_ifc_model(ifc_file: Path, output_dir: Path, exclude_none: bool = False, max_elements: Optional[int]=None):
    """Extract all IFC elements from the model and write each as a JSON file in `output_dir`.

    Args:
        ifc_file: Path to the IFC file to load.
        output_dir: Directory where JSON files will be written (created if missing).
        exclude_none: If True, remove all fields with None recursively from output.

    Returns:
        - A directory with exported JSON files for each IfcBuildingElement in the output directory.
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    elements_dir = output_dir / "elements"
    elements_dir.mkdir(exist_ok=True)

    # Initialize counters for single and composition elements & bill of quantities rows
    count_single_elements = 0
    count_composition_elements = 0   

    # Load the IFC model
    model = load_ifc_file(ifc_file) 
    
    # Get appropriate entity type based on schema version
    schema_version = model.schema_name
    entity_type = "IfcBuiltElement" if schema_version.upper().startswith("IFC4.3") else "IfcBuildingElement"

    # Get units and length conversion factor
    units = load_ifc_units(model)

    # Build caches once
    caches = IfcCaches(model)

    # All elements of interest
    elements = model.get_entities_by_type(entity_type)


    #TEMP
    exported = 0

    for element in elements:

        # TEMP
        if max_elements is not None and exported >= max_elements:
            break


        try:
            # Extract full element data
            data = extract_ifc_element(
                element,
                caches,
                units
            )
            if not data:
                continue

            # Serialize to JSON
            payload: Any = data.model_dump(exclude_none=exclude_none, by_alias=True)

            elename = getattr(element, "Name", None)
            out_path = elements_dir / f"{elename}.json"

            """
            ### GLOBALID AS OUTPUT NAME
            gid = getattr(element, "GlobalId", None)
            out_path = elements_dir / f"{gid}.json"
            """

            with out_path.open("w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

        except Exception:
            # Keep going on individual element failures
            continue

        exported += 1