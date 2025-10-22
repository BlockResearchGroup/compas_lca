import os
import json

from .helpers import


from . import helpers_units as unit
from . import helpers_io as inout
from . import helpers_metadata as meta
from . import helpers_material as mat
from . import helpers_geometry as geo
from . import helpers_psets as prop
from . import helpers_file_metadata as file_meta


def extractor(ifc_input_file, model, out_directory_elements, out_directory_compositions, out_directory_boq):

    # Initialize counters for single and composition elements & bill of quantities rows
    count_single_elements = 0
    count_composition_elements = 0

    # Check IFC schema version to specify the correct entity type
    schema_version = model.schema_name
    entity_type = "IfcBuiltElement" if schema_version.startswith("IFC4.3") else "IfcBuildingElement"

    # Load all IfcBuildingElements from IFC model
    elements = model.get_entities_by_type(entity_type)

    # Extract global model values before looping element
    formatted_units, lc_factor = unit.model_units(model)
    classification_relationships = model.get_entities_by_type("IfcRelAssociatesClassification")
    property_relationships = model.get_entities_by_type("IfcRelDefinesByProperties")
    type_relationships = model.get_entities_by_type("IfcRelDefinesByType")
    material_relationships = model.get_entities_by_type("IfcRelAssociatesMaterial")
    aggregates_relationships = model.get_entities_by_type("IfcRelAggregates")

    # Get File Metadata for overview sheet
    file_metadata = file_meta.get_file_metadata(ifc_input_file, model, formatted_units)

    # Some IFC files have identical names for elements. Keep track of used names
    used_names = {}

    # Iterate over all IfcBuildingElements
    for element in elements:

        try:
            # === CREATE DATA SHEETS FOR EACH ELEMENT ===

            # Initialize the data dictionary for each element
            element_data = {}

            # --- ELEMENT METADATA ---
            metadata = {}
            metadata["Name"] = element.Name
            metadata["GlobalId"] = element.GlobalId
            metadata["Type"] = type(element).__name__
            metadata["ObjectType"] = element.ObjectType
            metadata["Classification"] = meta.extract_classification_info(element, classification_relationships)
            decomposes, is_decomposed_by = meta.extract_hierarchy(element, aggregates_relationships)
            metadata["Decomposes"] = decomposes
            metadata["Is Decomposed By"] = is_decomposed_by
            metadata["Description"] = meta.description(element)
            element_data["Element Metadata"] = metadata
            

            # --- MATERIAL DATA ---
            material_data = mat.extract_material_associations(element, material_relationships, type_relationships, lc_factor)
            element_data["Element Material Data"] = material_data

            # --- PROPERTY SETS ---
            psets_data = {}
            psets_data["Psets Element"] = prop.extract_element_psets(element, property_relationships)
            psets_data["Psets Object Type"] = prop.extract_type_psets(element, type_relationships)
            element_data["Element Property Sets"] = psets_data

            # --- QUANTITIES ---
            geometry_data = {}
            geometry_data["Quantities (IFC)"] = geo.quantities_ifc(element, property_relationships, lc_factor)

            # --- EXPORT ---
            base_name = meta.name(element) or "Unnamed"

            if base_name not in used_names:
                used_names[base_name] = 0
                final_name = base_name
            else:
                used_names[base_name] += 1
                final_name = f"{base_name}_{used_names[base_name]}"


            # Choose directory based on is_decompsed_by
            if is_decomposed_by:
                inout.save_individual_json(element_data, out_directory_compositions, final_name)
                count_composition_elements += 1
            else:     
                inout.save_individual_json(element_data, out_directory_elements, final_name)
                count_single_elements += 1

        except Exception as e:
            name = meta.name(element) or "Unnamed"
            globalid = meta.globalid(element) or "No GlobalId"
            print(f"Error processing element: Name='{name}', GlobalId='{globalid}'")
            print(f"Exception: {e}")
            continue
    
    # Add composition and skipped element counters to metadata
    file_metadata["Module 01: Data Extraction"] = {
        "Module 01a: Extract All Elements": {
            "Building Elements with Childern (Disregarded for inference)": count_composition_elements,
            "Building Elements without Childern": count_single_elements
        }
    }

    # Export the Metadata JSON file
    file_metadata_output_path = os.path.join(out_directory_boq, "metadata_step_01a.json")
    with open(file_metadata_output_path, "w", encoding="utf-8") as jsonfile:
        json.dump(file_metadata, jsonfile, indent=4)