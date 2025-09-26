
from .lca_element import LcaElement


class LcaLayer(LcaElement): 
    """Base class for an LCA layer, if the referenced LcaElement has more than one material layer.
    
    Attributes 
    ---------- 
    layer : 
        The subsequent material layer
        This is a class that shows layer name, layer material, thickness, and other relevant attributes.
    element_context : 
        All LCA relevant context of the LcaElement this layer belongs to.
        This might be important, as some layers might have different context depending on the element they belong to.

    """
    pass