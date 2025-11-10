from typing import List
from typing import Optional
from typing import Dict

from uuid import UUID
from uuid import uuid4

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.matching_core.core import MatchingCore


from compas_lca.model.quantity import Quantities
from compas_lca.model.descriptor import ElementDescriptor
from compas_lca.model.match import Matches
from compas_lca.model.match import Match
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
    element_core : List[MatchingCore]
        The list of all MatchingCores for each material of this element.
        Multiple MatchingCore objects if the LcaElement represents a multilayer element
        Only one MatchingCore if the element is made out of one material.
    quantities : Quantities
        Numeric take-offs used for LCA (length, area, volume, piece count, etc.).
        If not provided but 'geometry' is present, compas may compute them downstream.
    matched_items : Optional[List[CoreMatches]]
        A list of Match objects for each MatchingCore (CoreMatches), representing an
        abbreviated InventoryItem (attached to the LcaElement after matching and merging).
        If an LcaElement has multiple MatchingCore objects, each MatchingCore receives
        the top k matches, and is indexed by the core_id of each MatchingCore.
    """

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    descriptor: ElementDescriptor           # describes if multilayer or no, describes if comp level abstraction or specific material(s)
    element_core: List[MatchingCore]            
    quantities: Quantities
    matched_items: List[Matches] = [] # matched InventoryItem objects for each MatchingCore of the element_core (multiple if multilayer element)

    def best_match(self) -> Dict[str, Optional[Match]]:
        """
        Return the best (max score) Match per core_id.
        Output: { "<core_id_str>": Match | None }
        """
        result: Dict[str, Optional[Match]] = {
            str(core.core_id): None for core in self.element_core
        }
        if not self.matched_items:
            return result
        for cm in self.matched_items:
            if cm.matches:
                result[cm.core_id] = max(cm.matches, key=lambda m: m.score)
            else:
                result.setdefault(cm.core_id, None)
        return result

    def calculate_lca(self):
        """
        Will only work if matched_items != None
        """
        pass

    def dissect_layers():
        pass


