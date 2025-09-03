from compas_model.models import Model

class LcaModel(Model):
    def __init__(self, name, elements):
        self.name = name
        self.elements = elements
        self.global_context = {}

    def from_ifc(self, filepath: str):
        pass