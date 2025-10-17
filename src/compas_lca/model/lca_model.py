from typing import Optional
from typing import List

from compas_model.models import Model

from .lca_element import LcaElement

class LcaModel(Model):
    def __init__(
            self, 
            name: str, 
            elements: Optional[List[LcaElement]] = []
            ):

        self.name = name
        self.elements = elements
        self.global_context = {}

    def from_ifc(self, filepath: str):
        pass
