from __future__ import annotations
from typing import Any

class IfcCaches:
    """Cache commonly used IFC relationship collections for fast lookups"""
    def __init__(self, model: Any):
        self.property_relationships = model.get_entities_by_type("IfcRelDefinesByProperties")
        self.type_relationships = model.get_entities_by_type("IfcRelDefinesByType")
        self.material_relationships = model.get_entities_by_type("IfcRelAssociatesMaterial")
        self.classification_relationships = model.get_entities_by_type("IfcRelAssociatesClassification")
        self.spatial_relationships = model.get_entities_by_type("IfcRelContainedInSpatialStructure")
        self.aggregates_relationships = model.get_entities_by_type("IfcRelAggregates")
        self.nesting_relationships = model.get_entities_by_type("IfcRelNests")
        self.covering_relationships = model.get_entities_by_type("IfcRelCoversBldgElements")
        self.void_relationships = model.get_entities_by_type("IfcRelVoidsElement")
        self.group_relationships = model.get_entities_by_type("IfcRelAssignsToGroup")