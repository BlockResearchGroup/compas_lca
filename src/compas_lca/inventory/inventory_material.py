from typing import Optional

from uuid import UUID
from uuid import uuid4

from typing import Optional

from compas_lca.material.lca_material import LcaMaterial

from .indicator import Indicators

# Notes: This is a draft. Unclear if it should inherit from compas.data or be a BaseModel
# perhaps it could inherit from IntentoryItem, but i dont know if that makes any sense

class InventoryMaterial:
    """
    Base class for an inventory material (either pure or composite material, NO COMPONENT)
    Represents data points required for precise LCA inventory filtering (LcaMaterial) and LCA calculation (Indicators, RefUnit)
    For calculation -> Density and thickness are extracted within the LcaMaterial dataschema!
    -> uuid is automatically created

    Attributes 
    ---------- 
    uuid : UUID
        Unique identifier for this InventoryMaterial. Automatically generated.
    material : LcaMaterial
        A dense list of attributes and values related to the LcaMaterial in terms of a material/product/composite
        This serves as the "matching core" between data from inventory data and a building model element
        perhaps naming convention should be reconsidered
    indicators : 
        indicators store the indicator name (e.g. GWP), inidicator unit (e.g., kgCO2eqv), life cycle stage, and indicator value. 
    reference_unit : 
        This is crucial for downstream calculation (combining InventoryMaterial and LcaElement)
        Unclear how this can be received in a generalizable way (LLM extraction??)
    """
    def __init__(
        self,
        material: LcaMaterial = None, # data describing the LCA Inventory Material (from EPD or database)
        indicators: Indicators = None, # associated indicators of the LCA Inventory Material
        reference_unit: str = None,  # perhaps Enum of most common reference units?
        source: Optional[str] = None # source of the EPD
    ):
        self._uuid: UUID = uuid4() # maybe redundant to have LcaMaterial with an UUID and LcaElement?
        self.material = material
        self.indicators = indicators # This should also be extracted by LLM for consistency... But seems very hard. For now, extracted from CSV (Oekobaudat)
        self.reference_unit = reference_unit # This should also be extracted by LLM for consistency...
        self.source = source # probably user input, but unclear
