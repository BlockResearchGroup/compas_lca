from pathlib import Path

import os

from typing import Dict
from typing import Any

from collections import defaultdict
from collections import OrderedDict

from compas_ifc.bim import BuildingInformationModel

from compas_lca.workflows.raw_extraction.ifc.ifc_caches import IfcCaches
from compas_lca.workflows.raw_extraction.ifc.ifc_helpers import _to_decimal
from compas_lca.workflows.raw_extraction.ifc.ifc_helpers import _best_material_rel


class IfcModel:
    """Thin adapter over compas_ifc 2.0's ``BuildingInformationModel``.

    compas_ifc 2.0 renamed the model class and moved ``get_entities_by_type``
    onto the underlying ``IFCFile`` (``model._file``). This wrapper preserves the
    minimal, entity-level surface COMPAS LCA relies on, so that every downstream
    ``model.get_entities_by_type(...)`` / ``model.schema_name`` call keeps working
    unchanged. Entities are returned as ``compas_ifc`` ``Base`` wrappers (raw
    ifcopenshell attribute access, inverse psets, materials, ``is_a()``, ``id()``
    and identity-based membership all preserved).
    """

    def __init__(self, bim: BuildingInformationModel):
        self._bim = bim

    def get_entities_by_type(self, ifc_type: str):
        return self._bim._file.get_entities_by_type(ifc_type)

    @property
    def schema_name(self) -> str:
        return self._bim.schema_name

    def __getattr__(self, name):
        # Delegate anything else to the underlying BuildingInformationModel.
        return getattr(self._bim, name)


def load_ifc_file(filepath, use_occ: bool = False):
    """
    Load an IFC file using the COMPAS-IFC front-end model (compas_ifc 2.0).

    Parameters
    ----------
    filepath : str | Path
        Path to the IFC file.
    use_occ : bool, optional
        Whether to use the OCC backend.

    Returns
    -------
    IfcModel
        Adapter over the loaded ``BuildingInformationModel``.
    """
    path = Path(filepath).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"'{path}' does not exist.")
    try:
        model = BuildingInformationModel(str(path), use_occ=use_occ)
        return IfcModel(model)
    except Exception as e:
        raise RuntimeError(f"Failed to load file: {e}")


def load_ifc_units(model) -> dict:
    """
    Returns IFC units exactly as defined (no conversions or remapping),
    but each unit is represented as a string like "MILLIMETRE" or "SQUARE_METRE".
    Adds a "lc_factor" that converts LENGTHUNIT values to meters (for compas_ifc geometry quants).
    """
    unit_assignments = model.get_entities_by_type("IfcUnitAssignment") or []
    relevant_units = {"LENGTHUNIT", "AREAUNIT", "VOLUMEUNIT", "MASSDENSITYUNIT"}
    units = {}

    for assignment in unit_assignments:
        for u in getattr(assignment, "Units", []) or []:
            utype = getattr(u, "UnitType", None)
            if utype not in relevant_units:
                continue

            name = (getattr(u, "Name", None) or "").upper()
            prefix = (getattr(u, "Prefix", None) or "").upper()

            # combine prefix + name → e.g. "MILLIMETRE"
            full_name = f"{prefix}{name}" if prefix else name
            units[utype] = full_name

    # Default conversion factor (meters)
    factor = 1.0
    length_unit = units.get("LENGTHUNIT", "")

    # Metric prefix map
    prefix_scale = {
        "MILLI": 1e-3,
        "CENTI": 1e-2,
        "DECI": 1e-1,
        "DECA": 1e1,
        "HECTO": 1e2,
        "KILO": 1e3,
    }
    # Common imperial units
    imperial_scale = {
        "INCH": 0.0254,
        "FOOT": 0.3048,
        "YARD": 0.9144,
        "MILE": 1609.34,
    }

    # Determine conversion factor to meters
    if length_unit:
        name = length_unit.upper()

        # Handle imperial
        if name in imperial_scale:
            factor = imperial_scale[name]
        # Handle pure metre or prefixed
        elif name.endswith("METRE") or name.endswith("METER"):
            # Extract prefix if any (e.g., "MILLIMETRE" → "MILLI")
            for prefix, scale in prefix_scale.items():
                if name.startswith(prefix):
                    factor = scale
                    break
            else:
                factor = 1.0
        else:
            factor = 1.0 

    units["lc_factor"] = factor
    return units






class PsetReader:
    """Small façade over your procedural helpers. Holds caches so calls are short."""
    def __init__(self, caches: IfcCaches):
        self.caches = caches

    def element_psets(self, element) -> Dict[str, str]:
        pass
        #return prop.extract_element_psets(element, self.caches.property_relationships)

    def type_psets(self, element) -> Dict[str, str]:
        pass
        #return prop.extract_type_psets(element, self.caches.type_relationships)

    def both(self, element) -> Dict[str, Dict[str, str]]:
        return {
            "Psets Element": self.element_psets(element),
            "Psets Object Type": self.type_psets(element),
        }
    
_MATERIAL_KEYS = [
    "IfcMaterialLayerSetUsage (n_layer=1)",
    "IfcMaterialLayerSetUsage (n_layer>1)",
    "IfcMaterialLayerSet (n_layer=1)",
    "IfcMaterialLayerSet (n_layer>1)",
    "IfcMaterialList (n_material=1)",
    "IfcMaterialList (n_material>1)",
    "IfcMaterial",
    "Other Entities",
    "No material data",
]

def _finalize_material_breakdown(breakdown_dict) -> OrderedDict:
    # ensure all keys exist and in the desired order
    return OrderedDict((k, breakdown_dict.get(k, 0)) for k in _MATERIAL_KEYS)

def load_ifc_metadata(input_file, model, units) -> Dict[str, Any]:
    """
    Build overall IFC file metadata, including:
      - project/app info
      - building element counts
      - breakdown by element type
      - breakdown by *material entity* category
    """

    # ---- Project name ---- 
    projects = model.get_entities_by_type("IfcProject")
    project_name = projects[0].Name if projects and hasattr(projects[0], "Name") else "Unnamed_Project"
    project_uuid = projects[0].GlobalId if projects and hasattr(projects[0], "GlobalId") else None

    # ---- Application details ---- 
    applications = model.get_entities_by_type("IfcApplication")
    if applications:
        application = applications[0]
        application_name = getattr(application, "ApplicationFullName", "Unknown Application")
        application_version = getattr(application, "Version", "Unknown Version")
        application_identifier = getattr(application, "ApplicationIdentifier", "Unknown ID")
        application_developer = getattr(application.ApplicationDeveloper, "Name", "Unknown Developer") \
            if hasattr(application, "ApplicationDeveloper") else "Unknown Developer"
    else:
        application_name = "Unknown Application"
        application_version = "Unknown Version"
        application_identifier = "Unknown ID"
        application_developer = "Unknown Developer"

    # ---- Building elements ----
    if model.schema_name.startswith("IFC4.3"):
        building_elements = model.get_entities_by_type("IfcBuiltElement")
    else:
        building_elements = model.get_entities_by_type("IfcBuildingElement")

    total_building_elements = len(building_elements)

    # ---- Breakdown by element type ----
    breakdown = {}
    for elem in building_elements:
        elem_type = elem.is_a()
        breakdown[elem_type] = breakdown.get(elem_type, 0) + 1

    # ---- Get Author / Owner of dataset ----
    owner = None
    creation_time = None
    docs = model.get_entities_by_type("IfcDocumentInformation")
    if docs:
        d = docs[0]
        owner = getattr(d, "DocumentOwner", None)
        creation_time = getattr(d, "CreationTime", None)

    # ---- Get Author Location Info ----
    site_data = []
    sites = model.get_entities_by_type("IfcSite")
    site = sites[0]  # get first site, should be close to others if multiple
    address = getattr(site, "SiteAddress", None)
    ltn = getattr(site, "LandTitleNumber", None)
    lat_attr = getattr(site, "RefLatitude", None)
    lon_attr = getattr(site, "RefLongitude", None)
    elev_attr = getattr(site, "RefElevation", None)
    lat = _to_decimal(lat_attr)
    lon = _to_decimal(lon_attr)
    elev = float(elev_attr) if elev_attr is not None else None
    site_data.append({
        "name": getattr(site, "Name", None),
        "address": address,
        "land_title_number": ltn,
        "latitude": lat,
        "longitude": lon,
        "elevation": elev,
    })
    

    # ---- Breakdown by material entity ----
    # Categories:
    # "IfcMaterialLayerSetUsage (n_layer=1)"
    # "IfcMaterialLayerSetUsage (n_layer>1)"
    # "IfcMaterialLayerSet (n_layer=1)"
    # "IfcMaterialLayerSet (n_layer>1)"
    # "IfcMaterialList (n_material=1)"
    # "IfcMaterialList (n_material>1)"
    # "IfcMaterial"
    # "Other Entities"
    # "No material data"
    material_breakdown = defaultdict(int)

    for elem in building_elements:
        best = _best_material_rel(elem) # choose material relationship based on predefined hierarchy
        if not best:
            material_breakdown["No material data"] += 1
            continue

        kind, rel_mat = best

        if kind == "IfcMaterialLayerSetUsage":
            # count layers from the underlying LayerSet
            layer_set = getattr(rel_mat, "ForLayerSet", None)
            layers = getattr(layer_set, "MaterialLayers", None) or []
            n = len(layers)
            key = "IfcMaterialLayerSetUsage (n_layer=1)" if n == 1 else "IfcMaterialLayerSetUsage (n_layer>1)"
            material_breakdown[key] += 1
        elif kind == "IfcMaterialLayerSet":
            layers = getattr(rel_mat, "MaterialLayers", None) or []
            n = len(layers)
            key = "IfcMaterialLayerSet (n_layer=1)" if n == 1 else "IfcMaterialLayerSet (n_layer>1)"
            material_breakdown[key] += 1
        elif kind == "IfcMaterialList":
            mats = getattr(rel_mat, "Materials", None) or []
            n = len(mats)
            key = "IfcMaterialList (n_material=1)" if n == 1 else "IfcMaterialList (n_material>1)"
            material_breakdown[key] += 1
        elif kind == "IfcMaterial":
            material_breakdown["IfcMaterial"] += 1
        else:
            material_breakdown["Other Entities"] += 1

    return {
        "IFC Project Name": project_name,
        "IFC Project UUID": project_uuid,
        "File Name": os.path.basename(input_file),
        "File Size (MB)": round(os.path.getsize(input_file) / (1024 * 1024), 2),
        "IFC Schema": model.schema_name,
        "IFC Project Units": units,
        "Document Owner": owner,
        "Document Creation Time": creation_time,
        "Site Data": site_data,
        "BIM Authoring Application": {
            "Application Name": application_name,
            "Version": application_version,
            "Application Identifier": application_identifier,
            "Developer": application_developer
        },
        "Building Elements Overview": {
            "Total Building Elements": total_building_elements,
            "Breakdown by Type": breakdown,
            "Breakdown by Material Entity": _finalize_material_breakdown(material_breakdown)
        }
    }
