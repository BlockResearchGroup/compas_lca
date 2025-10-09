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
