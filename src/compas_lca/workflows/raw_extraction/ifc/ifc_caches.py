from typing import Any

from collections import defaultdict

class IfcCaches:
    """Cache the rarely-populated ``IfcMaterialProperties`` reverse index.

    All other IFC relationships (materials, classification, spatial decomposition,
    property/quantity sets) are read directly from each element's inverse
    attributes (see ``ifc_helpers`` / ``ifc_processing``), so no model-wide
    relationship caches or O(n) membership scans are needed.
    """
    def __init__(self, model: Any):
        self.material_props = model.get_entities_by_type("IfcMaterialProperties")

        # Reverse index: IfcMaterialDefinition -> [IfcMaterialProperties, ...].
        # IfcMaterialProperties are seldom exported (Revit only writes them when
        # "Export Material Properties" is enabled), so this is usually empty.
        self.material_props_by_def = defaultdict(list)
        for mprops in self.material_props:
            mat_def = getattr(mprops, "Material", None)  # IfcMaterial / IfcMaterialLayer / IfcMaterialLayerSet
            if mat_def is not None:
                self.material_props_by_def[mat_def].append(mprops)
