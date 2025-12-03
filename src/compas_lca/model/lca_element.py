from typing import List
from typing import Literal
from typing import Optional
from typing import Dict
from typing import Union

from uuid import UUID
from uuid import uuid4
from uuid import uuid5

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.matching_core.core import MatchingCore

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
    is_aggregated: Literal[False]
        Discriminator between LcaElement and AggregatedLcaElement. Aggregation means that
        multiple building-model elements that share a common grouping key (e.g. "object_type",
        material signature, or classification) are represented as one element instance, and 
        their quantities are summed up.
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
    is_aggregated: Literal[False] = False
    descriptor: ElementDescriptor
    element_core: List[MatchingCore]            
    quantities: Quantities
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


# ==========================================================
# ------------------ AggregatedLcaElement ------------------
# ==========================================================


class AggregatedLcaElement(LcaElement):
    """
    Aggregated representation of multiple `LcaElement` objects that share a common 
    `object_type` grouping key.

    This subclass inherits all data fields and LCA computation methods from `LcaElement`,
    but adds metadata describing the aggregation context and provenance of the grouped elements.

    During aggregation (`from_group`):
        • All source elements must have the same non-empty `descriptor.object_type`.
        • The aggregated element's `descriptor.element_name` is redefined as:
              "<object_type> (aggregated xN)"
          where *N* is the number of elements combined.
        • The aggregated element's `descriptor.element_uuid` is set to `"AGGREGATED"`,
          since it no longer corresponds to a single building-model object.
        • Other descriptor fields (e.g. `is_multilayer`, `layer_count`, `classification`)
          are copied verbatim from the representative element.

    Typical use:
        - Combine multiple identical or equivalent building elements into a single record
          and sum their quantities for more efficient LCA computations and reporting.
        - Preserve traceability by listing all contributing `LcaElement` IDs.

    Attributes
    ----------
    is_aggregated : bool = True
        Discriminator between `LcaElement` and `AggregatedLcaElement`.
    source_ids : List[UUID]
        UUIDs of the original `LcaElement` instances included in this aggregate.
    group_key : str
        Grouping criterion used for aggregation (always equal to the shared `object_type`).
    count : int
        Number of individual elements represented by this aggregate.
    
    TODO: This is consistently doable for IFC models; for other formats 
    like 3dm or compas_model, this approach needs to be refactored.
    """
    model_config = ConfigDict(extra="forbid")

    is_aggregated: Literal[True] = True # discriminator for LcaModel
    source_ids: List[UUID]
    group_key: str
    count: int

    @classmethod
    def from_group(
        cls,
        elements: List[LcaElement],
        *,
        group_key: str,
        name_suffix: Optional[str] = None,   # kept for API compatibility; ignored now
        merge_matches: bool = True,
    ) -> "AggregatedLcaElement":
        if not elements:
            raise ValueError("Cannot aggregate empty list")

        rep = elements[0]

        # --- Compatibility checks ----------
        # object_type must be present (non-empty) on the representative
        ref_objtype = (rep.descriptor.object_type or "").strip()
        if not ref_objtype:
            raise ValueError(f"Aggregation requires non-empty object_type (ref {rep.id})")

        # All elements must share the same object_type and it must be non-empty
        for e in elements[1:]:
            objtype = (e.descriptor.object_type or "").strip()
            if not objtype:
                raise ValueError(f"Aggregation requires non-empty object_type (elem {e.id})")
            if objtype != ref_objtype:
                raise ValueError(
                    f"object_type mismatch: '{objtype}' (elem {e.id}) != '{ref_objtype}' (ref {rep.id})"
                )

        # Identical ordered list of core_id values
        ref_core_ids = [str(core.core_id) for core in (rep.element_core or [])]
        for e in elements[1:]:
            ids = [str(core.core_id) for core in (e.element_core or [])]
            if ids != ref_core_ids:
                raise ValueError(
                    "core_id sequence mismatch:\n"
                    f"  ref ({rep.id}): {ref_core_ids}\n"
                    f"  got ({e.id}): {ids}"
                )

        # Per-core thickness equality (exact; tolerance = 0.0)
        ref_thicknesses: List[float] = []
        for idx, core in enumerate(rep.element_core or [], start=1):
            t = getattr(core, "thickness", None)
            if t is None:
                raise ValueError(f"Missing thickness for core[{idx}] (ref {rep.id})")
            try:
                ref_thicknesses.append(float(t))
            except Exception:
                raise ValueError(f"Non-numeric thickness for core[{idx}] (ref {rep.id}): {t!r}")

        for e in elements[1:]:
            if len(e.element_core or []) != len(ref_thicknesses):
                raise ValueError(f"Thickness list length mismatch (elem {e.id})")
            for idx, core in enumerate(e.element_core or [], start=1):
                t = getattr(core, "thickness", None)
                if t is None:
                    raise ValueError(f"Missing thickness for core[{idx}] (elem {e.id})")
                try:
                    tv = float(t)
                except Exception:
                    raise ValueError(f"Non-numeric thickness for core[{idx}] (elem {e.id}): {t!r}")
                if tv != ref_thicknesses[idx - 1]:
                    raise ValueError(
                        f"core[{idx}] thickness mismatch (elem {e.id}): "
                        f"{ref_thicknesses[idx - 1]} mm vs {tv} mm (tol=0.0 mm)"
                    )

        # Enforce that the provided group_key matches the object_type
        if group_key.strip() != ref_objtype:
            raise ValueError(
                f"group_key must equal object_type for aggregation: "
                f"'{group_key}' != '{ref_objtype}'"
            )

        # Sum quantities (implement Quantities.sum to do field-wise sum safely)
        total_quant = Quantities.sum([e.quantities for e in elements])

        # Descriptor: copy representative, but force name to OBJECT_TYPE (aggregated xN)
        desc = rep.descriptor.model_copy(deep=True)
        desc.element_name = f"{ref_objtype} (aggregated x{len(elements)})"
        if hasattr(desc, "element_uuid"):
            desc.element_uuid = "AGGREGATED"

        # uuid5 for AggregateLcaElements
        agg_id = uuid5

        # Merge matches per core_id (optional)
        matched_items = None
        if merge_matches:
            by_core: Dict[str, List[Match]] = {}
            for e in elements:
                for cm in (e.matched_items or []):
                    key = str(cm.core_id)
                    by_core.setdefault(key, []).extend(cm.matches or [])
            matched_items = [Matches(core_id=k, matches=v) for k, v in by_core.items()]

        return cls(
            id=agg_id,
            descriptor=desc,
            element_core=rep.element_core,
            quantities=total_quant,
            matched_items=matched_items,
            source_ids=[e.id for e in elements],
            group_key=ref_objtype,  # store the canonical grouping key
            count=len(elements),
        )
