from __future__ import annotations
from pathlib import Path
from typing import Any
from typing import Dict

from compas_ifc.model import Model

from .ifc_caches import IfcCaches


def load_ifc_file(filepath, use_occ: bool = False):
    """
    Load an IFC file using COMPAS-IFC Model class.

    Parameters
    ----------
    filepath : str | Path
        Path to the IFC file.
    use_occ : bool, optional
        Whether to use the OCC backend.

    Returns
    -------
    Model
        The loaded IFC model.
    """
    path = Path(filepath).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"'{path}' does not exist.")
    try:
        model = Model(str(path), use_occ=use_occ)
        return model
    except Exception as e:
        raise RuntimeError(f"Failed to load file: {e}")



def load_ifc_units(model: Model) -> dict:
    """
    Extracts unit information from an IFC model.

    Parameters
    ----------
    model : compas_ifc.model.Model
        The loaded COMPAS IFC model instance.

    Returns
    -------
    dict
        A mapping of IFC unit types to readable names, e.g.:
        {
            "LENGTHUNIT": "millimetre",
            "AREAUNIT": "square metre",
            "VOLUMEUNIT": "cubic metre",
            "PLANEANGLEUNIT": "radian",
            "MASSUNIT": "kilogram",
            "MASSDENSITYUNIT": "kilogram per cubic metre"
        }
    """
    unit_assignments = model.get_entities_by_type("IfcUnitAssignment") or []
    formatted_units = {}

    relevant_units = {
        "LENGTHUNIT",
        "AREAUNIT",
        "VOLUMEUNIT",
        "PLANEANGLEUNIT",
        "MASSUNIT",
        "MASSDENSITYUNIT",
    }

    # Helper: turn IFC enum + prefix into a human-readable name
    def _format_unit_name(unit):
        name = getattr(unit, "Name", None)
        prefix = getattr(unit, "Prefix", None)

        if not name:
            return "unknown"

        name = name.upper()
        prefix = prefix.upper() if isinstance(prefix, str) else None

        if prefix == "MILLI" and name == "METRE":
            return "millimetre"
        elif prefix == "CENTI" and name == "METRE":
            return "centimetre"
        elif prefix == "DECI" and name == "METRE":
            return "decimetre"
        elif prefix == "KILO" and name == "METRE":
            return "kilometre"

        mapping = {
            "METRE": "metre",
            "SQUARE_METRE": "square metre",
            "CUBIC_METRE": "cubic metre",
            "RADIAN": "radian",
            "GRAM": "gram",
            "KILOGRAM": "kilogram",
        }
        return mapping.get(name, name.replace("_", " ").lower())

    # Iterate through all IfcUnitAssignment entities
    for assignment in unit_assignments:
        for unit in getattr(assignment, "Units", []) or []:
            unit_type = getattr(unit, "UnitType", None)
            if unit_type in relevant_units:
                formatted_units[unit_type] = _format_unit_name(unit)

    # Fallback defaults for missing ones
    defaults = {
        "LENGTHUNIT": "metre",
        "AREAUNIT": "square metre",
        "VOLUMEUNIT": "cubic metre",
        "PLANEANGLEUNIT": "radian",
        "MASSUNIT": "kilogram",
        "MASSDENSITYUNIT": "kilogram per cubic metre",
    }
    for key, val in defaults.items():
        formatted_units.setdefault(key, val)

    return formatted_units




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