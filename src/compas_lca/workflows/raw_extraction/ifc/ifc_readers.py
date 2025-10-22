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



def load_ifc_units(model: Model):
    """
    Extracts relevant unit information from an IFC model and computes a length conversion factor.

    Parameters
    ----------
    model : compas_ifc.model.Model
        The loaded COMPAS IFC model instance from which unit assignments are extracted.

    Returns
    -------
    tuple[dict, float]
        A tuple containing:
        - **formatted_units** (`dict`):  
          A mapping of unit types to their normalized names
        - **lc_factor** (`float`):  
          Length conversion factor used to convert model dimensions to meters
    """

    unit_assignments = model.get_entities_by_type("IfcUnitAssignment")
    formatted_units = {}
    lc_factor = 1.0  # length conversion factor (Default to METRE)
    relevant_units = {
        "LENGTHUNIT", "AREAUNIT", "VOLUMEUNIT",
        "PLANEANGLEUNIT", "MASSUNIT", "MASSDENSITYUNIT"
    }

    for assignment in unit_assignments:
        for unit in getattr(assignment, "Units", []):
            unit_type = getattr(unit, "UnitType", "Unknown")

            if unit_type in relevant_units:
                unit_name = getattr(unit, "Name", "Unknown").upper()
                unit_prefix = getattr(unit, "Prefix", None)
                unit_prefix = unit_prefix.upper() if isinstance(unit_prefix, str) else ""
                formatted_units[unit_type] = unit_name

                if unit_type == "LENGTHUNIT":
                    if unit_prefix == "MILLI":
                        lc_factor = 0.001
                        formatted_units["LENGTHUNIT"] = "MILLIMETRE"
                    elif unit_prefix == "CENTI":
                        lc_factor = 0.01
                        formatted_units["LENGTHUNIT"] = "CENTIMETRE"
                    else:
                        formatted_units["LENGTHUNIT"] = "METRE"

    return formatted_units, lc_factor



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
