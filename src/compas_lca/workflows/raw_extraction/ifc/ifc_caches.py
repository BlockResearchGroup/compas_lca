from typing import Any

from collections import defaultdict

class IfcCaches:
    """Cache commonly used IFC relationship collections for fast lookups"""
    def __init__(self, model: Any):
        self.property_rels = model.get_entities_by_type("IfcRelDefinesByProperties")
        self.type_rels = model.get_entities_by_type("IfcRelDefinesByType")
        self.material_rels = model.get_entities_by_type("IfcRelAssociatesMaterial")
        self.classification_rels = model.get_entities_by_type("IfcRelAssociatesClassification")
        self.spatial_rels = model.get_entities_by_type("IfcRelContainedInSpatialStructure")
        self.aggregates_rels = model.get_entities_by_type("IfcRelAggregates")
        self.nesting_rels = model.get_entities_by_type("IfcRelNests")
        self.covering_rels = model.get_entities_by_type("IfcRelCoversBldgElements")
        self.void_rels = model.get_entities_by_type("IfcRelVoidsElement")
        self.group_rels = model.get_entities_by_type("IfcRelAssignsToGroup")
        self.material_props = model.get_entities_by_type("IfcMaterialProperties")
        
        # TODO: Verify and decide on the necessity of this reverse index.
        #       Reverse index: IfcMaterialDefinition -> [IfcMaterialProperties, ...]
        #       Observation: IfcMaterialProperties are seldom exported (at least not from Revit).
        #       Question: Is this reverse index even needed in practice?
        #       Note: Requires enabling “Export Material Properties” in Revit’s IFC export dialog.
        
        self.material_props_by_def = defaultdict(list)
        for mprops in self.material_props:
            mat_def = getattr(mprops, "Material", None)  # IfcMaterial / IfcMaterialLayer / IfcMaterialLayerSet
            if mat_def is not None:
                self.material_props_by_def[mat_def].append(mprops)