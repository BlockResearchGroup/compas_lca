from pathlib import Path

import json

from typing import Optional
from typing import Dict
from typing import Any

from compas_ifc.model import Model

from .helpers import get_classification
from .helpers import get_hierarchy
from .helpers import get_material_props
from .helpers import clean_value

from .ifc_element import IfcElementMetadata
from .ifc_element import IfcMaterial
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
    type= type(element).__name__
    object_type = getattr(element, "ObjectType", None)
    description = getattr(element, "Description", None)
    classification = get_classification(element, caches.classification_rels)
    decomposes, is_decomposed_by = get_hierarchy(element, caches.aggregates_rels)

    return IfcElementMetadata(
        name=name,
        global_id=global_id,
        type=type,
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

def extract_layer(relating_material, caches) -> IfcMaterialLayer:
    mat = getattr(relating_material, "Material", None)
    return IfcMaterialLayer(
        material_name=getattr(mat, "Name", None) if mat else None,
        material_description=getattr(mat, "Description", None) if mat else None,
        thickness=getattr(relating_material, "LayerThickness", None),
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
    Build a MaterialAssociation (IfcMaterialLayerSetUsage | IfcMaterialLayerSet | IfcMaterial)
    for a single IFC element from IfcRelAssociatesMaterial relationships.
    """
    rel = next(
        (r for r in caches.material_rel if element in (getattr(r, "RelatedObjects", None) or [])),
        None,
    )
    if not rel:
        return None
    rel_mat = getattr(rel, "RelatingMaterial", None)
    if rel_mat is None:
        return None
    kind = rel_mat.is_a() if hasattr(rel_mat, "is_a") else type(rel_mat).__name__
    if kind == "IfcMaterialLayerSetUsage":
        return extract_layerset_usage(rel_mat, caches)
    elif kind == "IfcMaterialLayerSet":
        return extract_layerset(rel_mat, caches)
    elif kind == "IfcMaterial":
        return extract_material(rel_mat, caches)
    else:
        raise ValueError(f"Unsupported RelatingMaterial type: {kind}")

# ------------------------
# Property Sets
# ------------------------
def extract_psets(element, caches) -> Optional[IfcElementProperties]:
    """Extract property sets for element and its type."""
    psets_element = {}
    psets_type = {}

    # Element property sets
    for rel in caches.property_rels:
        if element in rel.RelatedObjects:
            prop_set = getattr(rel, "RelatingPropertyDefinition", None)
            if prop_set and prop_set.is_a("IfcPropertySet"):
                for prop in getattr(prop_set, "HasProperties", []) or []:
                    if hasattr(prop, "Name") and hasattr(prop, "NominalValue"):
                        raw_value = prop.NominalValue
                        psets_element[prop.Name] = clean_value(str(raw_value))

    # Type property sets
    for rel in caches.type_rels:
        if element in rel.RelatedObjects:
            object_type = rel.RelatingType
            if object_type and hasattr(object_type, "HasPropertySets"):
                for pset in object_type.HasPropertySets:
                    if pset.is_a("IfcPropertySet"):
                        for prop in getattr(pset, "HasProperties", []) or []:
                            if hasattr(prop, "Name") and hasattr(prop, "NominalValue"):
                                raw_value = prop.NominalValue
                                psets_type[f"{pset.Name}.{prop.Name}"] = clean_value(str(raw_value))

    if not psets_element and not psets_type:
        return None

    return IfcElementProperties(
        psets_element=psets_element if psets_element else None,
        psets_type=psets_type if psets_type else None,
    )

# ------------------------
# Quantities
# ------------------------

def _norm(name: str) -> str:
    # lower + remove spaces/underscores for robust matching
    return (name or "").lower().replace(" ", "").replace("_", "")

def extract_quantities(element, caches, lc_factor) -> Optional[IfcElementQuantities]:
    # Initialize all outputs (None by default)
    width = length = height = depth = None
    gross_area = net_area = None
    gross_side_area = net_side_area = None
    gross_footprint_area = net_footprint_area = None
    cross_section_area = None
    gross_volume = net_volume = None
    area_factor = lc_factor ** 2
    volume_factor = lc_factor ** 3

    for rel in getattr(caches, "property_rel", []):
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
                v = round(volume_factor * q.VolumeValue, 4)
                if "gross" in qname:
                    gross_volume = v
                elif "net" in qname:
                    net_volume = v

            # Areas (m²)
            if q.is_a("IfcQuantityArea") and hasattr(q, "AreaValue") and q.AreaValue is not None:
                a = round(area_factor * q.AreaValue, 4)

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
                L = round(lc_factor * q.LengthValue, 4)
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
        units="meter, square_meter, cubic_meter",
        width=width,
        length=length,
        height=height,
        depth=depth,
        gross_area=gross_area,
        net_area=net_area,
        gross_side_area=gross_side_area,
        net_side_area=net_side_area,
        gross_footprint_area=gross_footprint_area,
        net_footprint_area=net_footprint_area,
        cross_section_area=cross_section_area,
        gross_volume=gross_volume,
        net_volume=net_volume,
    )


# ------------------------
# Element data (compiled)
# ------------------------
def extract_ifc_element(element, caches, lc_factor) -> IfcElementData:
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
        quantities = extract_quantities(element, caches, lc_factor)

        return IfcElementData(
            metadata=metadata,
            material_data=material_data,
            properties=psets,
            quantities=quantities,
        )

    except Exception as e:
        element_id = getattr(element, "GlobalId", None)
        logger.warning(
            f"Failed to extract element {element_id or element}: {type(e).__name__} - {e}"
        )
        return None


# ------------------------
# IFC Model extraction
# ------------------------


def extract_ifc_model(ifc_file: Path, output_dir: Path, exclude_none: bool = False):
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
    units, lc_factor = load_ifc_units(model)

    # Build caches once
    caches = IfcCaches(model)

    # All elements of interest
    elements = model.get_entities_by_type(entity_type)

    for element in elements:
        try:
            # Extract full element data
            data = extract_ifc_element(
                element,
                caches,
                lc_factor
            )
            if not data:
                continue

            # Serialize to JSON
            payload: Any = data.model_dump(exclude_none=exclude_none, by_alias=True)
            gid = getattr(element, "GlobalId", None)
            out_path = elements_dir / f"{gid}.json"
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

        except Exception:
            # Keep going on individual element failures
            continue




















