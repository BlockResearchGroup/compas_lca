import os
import re
import json


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

def sanitize_filename(name):
    if not name:
        return "UnnamedElement"
    cleaned = re.sub(r'[^\w\säöüÄÖÜß-]', '-', name, flags=re.UNICODE)
    return cleaned.replace(" ", "-")

def save_json(element_data, output_directory, element_name):
    """
    Saves the given element_data to a JSON file named after the element's name,
    with illegal characters replaced by "-". Allows UTF-8 characters like umlauts.
    """
    # Ensure output directory exists
    os.makedirs(output_directory, exist_ok=True)
    # Get element name and sanitize it for filesystem use
    sanitized_name = sanitize_filename(element_name)
    # Construct full file path
    filename = f"{sanitized_name}.json"
    filepath = os.path.join(output_directory, filename)
    # Write JSON file
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(element_data, f, indent=4, ensure_ascii=False)