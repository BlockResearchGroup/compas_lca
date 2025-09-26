from pathlib import Path

from compas_ifc.model import Model


def extract_ifc_model(ifc_input_file:Path):

    building_model_dir = Path("data/building_model")
    building_model_file = next(building_model_dir.iterdir())

    if building_model_file.is_file() and building_model_file.suffix.lower() == ".ifc":

        # Load the IFC model
        model = Model(str(building_model_file), use_occ=False)

        # Load all IfcBuildingElemements from IFC model
        schema_type = "IfcBuiltElement" if model.schema_name.startswith("IFC4.3") else "IfcBuildingElement"
        ifc_elements = model.get_entities_by_type(schema_type)
    


    else:
        pass






def extract_ifc_element_metadata(element):
    """Extract metadata from IFC elements."""
    pass

def extract_ifc_element_materials(model: Model):
    """Extract material information from IFC elements."""
    pass

def extract_ifc_element_quantities(model: Model):
    """Extract quantity information from IFC elements."""
    pass

def extract_ifc_elements(ifc_input_file):
    """Extract all IFC elements from the model."""
    pass





def aggregate_ifc_objecttype_data():
    pass

def dissect_multilayer_material():
    pass
    