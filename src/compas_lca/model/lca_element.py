from compas_model.elements import Element

class LcaElement(Element):

    def __init__(self, name, geometry, material, quantity, metadata):
        self.name = name
        self.geometry = geometry
        self.material = material
        self.quantity = quantity
        self.metadata = metadata

    def match(self, inventory_item):
        """Match the element to an inventory item. Returns True/False, or granularity too high/low."""
        pass

    def extract(self, inventory_summary):
        """Extract relevant information from the element, according to the LCA inventory summary."""
        pass