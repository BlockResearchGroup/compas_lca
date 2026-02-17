from typing import List
from typing import Optional
from typing import Dict
from typing import Union

from uuid import UUID
from uuid import uuid4

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.matching_core.core import MatchingCore

from compas_lca.model.metadata import ModelMetadata
from compas_lca.model.quantity import Quantities
from compas_lca.model.descriptor import ElementDescriptor
from compas_lca.model.match import Matches
from compas_lca.model.match import Match

Number = Union[int, float]

# ==========================================================
# ----------------------- LcaElement -----------------------
# ==========================================================
class LcaElement(BaseModel):
    """
    LCA element record (one building-model element mapped to LCA inputs).

    Attributes
    ----------
    id : UUID
        Stable unique identifier for this element. Auto-generated if not provided ('uid').
    descriptor : ElementDescriptor
        Descriptive data about the source element (name, types, labels,
        manufacturer hints, notes). Flags if it is a multilayer, and includes
        layer count (if multiple layered materials are included in this element).
    element_core : List[MatchingCore]
        The list of all MatchingCores for each material of this element.
        Multiple MatchingCore objects if the LcaElement represents a multilayer element
        Only one MatchingCore if the element is made out of one material.
    quantities : Quantities
        Numeric take-offs used for LCA (length, area, volume, piece count, etc.).
    metadata : Optional[ModelMetadata]
        Provenance of the building element (e.g., filename, source software, version, author).
    matched_items : Optional[List[Matches]]
        A list of Match objects for each MatchingCore (Matches), representing an
        abbreviated InventoryItem (attached to the LcaElement after matching and merging).
        If an LcaElement has multiple MatchingCore objects, each MatchingCore receives
        the top k matches, and is indexed by the core_id of each MatchingCore.
        This field is optional, since the same LcaElement object needs to be created
        before the matching procedure, after which the top_k scored InventoryItems are 
        appended to the matched_items list -> compas_lca/workflows/matching.py
    """

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    descriptor: ElementDescriptor
    element_core: List[MatchingCore]            
    quantities: Quantities
    metadata: Optional[ModelMetadata]
    matched_items: Optional[List[Matches]] = None # add source
    """
    indicator_stats: Optional[IndicatorStatistics] = None

    ### Idea: after calculation, can add indicator statistics (i.e., min, max, mean) for LcaElement.
    Not implemented yet, noted here for future reference.
    """


    # ----------------------------
    # Public convenience API
    # ----------------------------

    def matching_core_ids(self) -> List[str]:
        """
        Return the element's MatchingCore core_id values, 
        in the same order as element.element_core has listed them
        """
        ids: List[str] = []
        for core in self.element_core:
            # MatchingCore.core_id is UUID; store as str in Matches
            ids.append(str(core.core_id))
        return ids

    def item_ids(self) -> Dict[str, List[str]]:
        """
        Return a mapping from each core_id to a list of item_ids
        found in this element's matched_items.
        """
        mapping: Dict[str, List[str]] = {}
        for core_matches in self.matched_items:
            core_id = str(core_matches.core_id)
            item_ids = [match.item_id for match in core_matches.matches]
            mapping[core_id] = item_ids
        return mapping

    def item_names(self) -> Dict[str, List[str]]:
        """
        Return a mapping from each core_id to a list of item_names
        found in this element's matched_items.
        """
        mapping: Dict[str, List[str]] = {}
        for core_matches in self.matched_items:
            core_id = str(core_matches.core_id)
            item_names = [match.item_name for match in core_matches.matches]
            mapping[core_id] = item_names
        return mapping

    # ----------------------------
    # Matching logic (best score)
    # ----------------------------

    def best_score(self) -> Dict[str, Optional["Match"]]:
        """
        Return the best (max score) Match per core_id.
        Output: { "<core_id_str>": Match | None }
        """
        result: Dict[str, Optional["Match"]] = {
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

    # ----------------------------
    # Quantity / unit logic
    # ----------------------------

    def layer_ratio_map(self) -> Dict[str, float]:
        """
        Returns {core_id -> thickness_ratio}.

        If all (>=2) cores have positive thickness values, ratio = thickness_i / sum(thickness_j).
        Otherwise (e.g., single-layer or missing thickness), every core gets ratio = 1.0.
        """
        # Extract thicknesses from element_core (works if entries are Pydantic models or dicts)
        thickness_by_core: Dict[str, float] = {}
        for core in (self.element_core or []):
            core_id = str(getattr(core, "core_id", None) or getattr(core, "id", None))
            if not core_id:
                continue
            thickness = getattr(core, "thickness", None)
            if thickness is None and isinstance(core, dict):
                thickness = core.get("thickness")
            if isinstance(thickness, (int, float)) and thickness > 0:
                thickness_by_core[core_id] = float(thickness)

        if len(thickness_by_core) >= 2:
            total_thickness = sum(thickness_by_core.values())
            if total_thickness > 0:
                return {cid: t / total_thickness for cid, t in thickness_by_core.items()}

        # Fallback: no ratioing (single layer or insufficient data)
        return {str(core.core_id): 1.0 for core in (self.element_core or [])}


    def get_quantity_value(self, name: str) -> Optional[float]:
        """
        Returns the numeric value of a named quantity from `self.quantities`.
        """
        qsrc = getattr(self, "quantities", None)
        if qsrc is None or not hasattr(qsrc, "quantities"):
            return None
        qblock = qsrc.quantities
        if not isinstance(qblock, list):
            return None
        target = (name or "").strip().lower()
        for q in qblock:
            # Each q is a Pydantic Quantity model
            q_name = (getattr(q, "name", "") or "").strip().lower()
            if q_name != target:
                continue
            v = getattr(q, "value", None)
            if v is None:
                return None
            try:
                return float(v)
            except (TypeError, ValueError):
                return None
        return None