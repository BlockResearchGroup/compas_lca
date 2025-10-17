from typing import Optional

from uuid import UUID
from uuid import uuid4

from typing import Optional

from compas_lca.component.lca_component import LcaComponent

from .indicator import Indicators

# DRAFT
# Notes: Unclear if it should inherit from compas.data or be a BaseModel
# Also here it makes sense to distinguish between material and component. hard/awkward to do this for LcaElement

class InventoryComponent:
    """
    Base class for an inventory dataset representing an enitre component (e.g., window, door, etc)
    Represents data points required for precise LCA inventory filtering (LcaMaterial) and LCA calculation (Indicators, RefUnit)
    For calculation -> Density and thickness are extracted within the LcaMaterial dataschema!
    -> uuid is automatically created

    Attributes 
    ---------- 
    uuid : UUID
        Unique identifier for this InventoryMaterial. Automatically generated.
    component : LcaComponent
        A dense list of attributes and values related to the LcaComponent.
        This serves as the "matching core" between data from inventory data and a building model element on a component-level resolution
        For instance, a modeled IfcWindow would be matched with a respective window InventoryComponent
        perhaps naming convention should be reconsidered
    indicators : Indicators
        indicators store the indicator name (e.g. GWP), inidicator unit (e.g., kgCO2eqv), life cycle stage, and indicator value. 
    reference_unit : str
        This is crucial for downstream calculation (combining InventoryMaterial and LcaElement)
        Unclear how this can be received in a generalizable way (LLM extraction??)
    source : str
        Where the data comes from (EPD link, database reference, etc.)
    """
    def __init__(
        self,
        component: LcaComponent = None, # data describing the LCA Inventory Material (from EPD or database)
        indicators: Indicators = None, # associated indicators of the LCA Inventory Material
        reference_unit: str = None,  # perhaps Enum of most common reference units?
        source: Optional[str] = None # source of the EPD
    ):
        self._uuid: UUID = uuid4() # maybe redundant to have LcaMaterial with an UUID and LcaElement?
        self.component = component
        self.indicators = indicators # This should also be extracted by LLM for consistency... But seems very hard. For now, extracted from CSV (Oekobaudat)
        self.reference_unit = reference_unit # This should also be extracted by LLM for consistency...
        self.source = source # probably user input, but unclear
