from typing import List

from uuid import UUID
from uuid import uuid4

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.matching_core.core import MatchingCore

from compas_lca.model.quantity import Quantities
from compas_lca.model.descriptor import ElementDescriptor
from compas_lca.model.materialspec import MaterialSpec

class LcaElement(BaseModel):
    """
    LCA element record (one building-model element mapped to LCA inputs).

    Attributes
    ----------
    uuid : UUID
        Stable unique identifier for this element. Auto-generated if not provided ('uid').
    metadata : ElementMetadata
        Descriptive data about the source element (name, types, labels,
        manufacturer hints, notes). Not authoritative for quantities.
    element_core : MatchingCore
        Component-level descriptor (assembly). Use when the source element represents a
        manufactured/constructed unit or system without a layer/composition breakdown
        (e.g., window unit, curtain-wall module, packaged HVAC, predefined wall/roof assembly).
        Mutually exclusive with 'material_data'.
    quantities : Quantities
        Numeric take-offs used for LCA (length, area, volume, piece count, etc.).
        If not provided but 'geometry' is present, compas may compute them downstream.
    """

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    descriptor: ElementDescriptor           # describes if multilayer or no, describes if comp level abstraction or specific material(s)
    element_core: List[MatchingCore]            
    quantities: Quantities
