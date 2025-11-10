from typing import List
from typing import Optional
from typing import Dict
from typing import Iterable
from typing import Union

from statistics import median

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

from compas_lca.inventory.constants import EN15978_STAGES

Number = Union[int, float]

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

    # ----------------------------
    # Public convenience API
    # ----------------------------

    def best_match(self) -> Dict[str, Optional["Match"]]:
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

    def min_gwp(
        self,
        *,
        core_id: Optional[str] = None,
        include_stage_D: bool = True,
        stages_filter: Optional[List[EN15978_STAGES]] = None,
    ) -> Optional[float]:
        """
        lowest GWP in kg CO₂-eqv of any match across the entire element. 
        Use if element only has 1 match, or specify core_id
        if you want to have the minimum gwp of one material
        (i.e., layered element)
        """
        vals = self._element_gwp_samples(core_id=core_id, include_stage_D=include_stage_D, stages_filter=stages_filter)
        return min(vals) if vals else None

    def max_gwp(
        self,
        *,
        core_id: Optional[str] = None,
        include_stage_D: bool = True,
        stages_filter: Optional[List[EN15978_STAGES]] = None,
    ) -> Optional[float]:
        """
        Highest GWP in kg CO₂-eqv of any match across the entire element. 
        Use if element only has 1 match, or specify core_id if 
        if you want to have the maximum gwp of one material
        (i.e., layered element)
        """
        vals = self._element_gwp_samples(core_id=core_id, include_stage_D=include_stage_D, stages_filter=stages_filter)
        return max(vals) if vals else None
    
    def median_gwp(
        self,
        *,
        core_id: Optional[str] = None,
        include_stage_D: bool = True,
        stages_filter: Optional[List[EN15978_STAGES]] = None,
    ) -> Optional[float]:
        """
        Median GWP in kg CO₂-eqv of any match across the entire element. 
        Use if element only has 1 match, or specify core_id if 
        if you want to have the median gwp of one material
        (i.e., layered element)
        """
        vals = self._element_gwp_samples(core_id=core_id, include_stage_D=include_stage_D, stages_filter=stages_filter)
        return median(vals) if vals else None

    def min_total_gwp(
            self, 
            *, 
            include_stage_D: bool = False,
            stages_filter: Optional[List[EN15978_STAGES]] = None
        ) -> Optional[float]:
        """
        Sum of lowest GWP in kg CO₂-eqv per core (element-level minimum).
        Use this to quickly calculate the the sum of the minimum gwp from
        multiple materials/layers within the LcaElement object.
        """
        total = 0.0
        for core_matches in self.matched_items or []:
            vals = self._element_gwp_samples(
                core_id=core_matches.core_id,
                include_stage_D=include_stage_D,
                stages_filter=stages_filter,  # e.g. ["A1-A3"]
            )
            if vals:
                total += min(vals)
        return total if total > 0 else None

    def max_total_gwp(
            self, 
            *, 
            include_stage_D: bool = False,
            stages_filter: Optional[List[EN15978_STAGES]] = None
        ) -> Optional[float]:
        """
        Sum of highest GWP in kg CO₂-eqv per core (element-level minimum).
        Use this to quickly calculate the the sum of the minimum gwp from
        multiple materials/layers within the LcaElement object.
        """
        total = 0.0
        found_any = False
        for core_matches in self.matched_items or []:
            vals = self._element_gwp_samples(
                core_id=core_matches.core_id,
                include_stage_D=include_stage_D,
                stages_filter=stages_filter,
            )
            if vals:
                total += max(vals)
                found_any = True
        return total if found_any else None

    # ----------------------------
    # Core logic
    # ----------------------------
    def _element_gwp_samples(
        self,
        *,
        core_id: Optional[str],
        include_stage_D: bool,
        stages_filter: Optional[Iterable[str]],
    ) -> List[float]:
        """
        Collects a list of element-level net-GWP realizations, one per Match.
        If core_id is None, pools matches from all cores. If core_id is provided,
        restricts to that core's matches only.

        Applies per-core thickness ratio when multiple cores with thickness are present.
        """
        if not self.matched_items:
            return []

        target_core_ids = {core_id} if core_id else {m.core_id for m in self.matched_items}
        ratio_map = self._layer_ratio_map()
        samples: List[float] = []

        for core_matches in self.matched_items:
            if core_matches.core_id not in target_core_ids:
                continue
            layer_ratio = ratio_map.get(core_matches.core_id, 1.0)
            for match in (core_matches.matches or []):
                val = self._match_net_gwp_for_element(
                    match,
                    include_stage_D=include_stage_D,
                    stages_filter=stages_filter,
                    layer_ratio=layer_ratio,
                )
                if val is not None:
                    samples.append(val)

        return samples


    def _match_net_gwp_for_element(
        self,
        match: "Match",
        *,
        include_stage_D: bool,
        stages_filter: Optional[Iterable[str]],
        layer_ratio: float = 1.0,   # keep this plumbed in
    ) -> Optional[float]:
        snap = (match.snapshot or {})
        ref = (snap.get("reference") or {})
        ref_size = ref.get("size")
        ref_unit = (ref.get("unit") or "").strip().lower()

        if not ref_size or not ref_unit:
            return None

        specific = self._sum_gwp_stages(
            snap.get("GWP") or {},
            include_stage_D=include_stage_D,
            stages_filter=stages_filter,
        )
        if specific is None:
            return None

        # density may be needed for mass refs
        density = snap.get("density")  # kg/m3 if present

        # note: ratio is only applied to volume (and mass when mass = volume * density)
        qty_val = self._functional_quantity_for_reference(
            ref_unit,
            density=density,
            layer_ratio=layer_ratio,   # only takes effect for volume paths
        )
        if qty_val is None:
            return None

        try:
            scale = float(qty_val) / float(ref_size)
        except Exception:
            return None

        return specific * scale  # kg CO2e

        
    def _layer_ratio_map(self) -> Dict[str, float]:
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


    # ----------------------------
    # Stage handling
    # ----------------------------
    def _sum_gwp_stages(
        self,
        gwp_block: Dict[str, object],
        *,
        include_stage_D: bool,
        stages_filter: Optional[Iterable[str]],
    ) -> Optional[float]:
        """
        Sums specific GWP (kg CO2e per reference) over chosen stages.

        Handles:
          - Combined keys like "A1-A3"
          - Individual keys like "A1", "A2", "A3"
          - Presence of "D" (included/excluded by flag)
        If stages_filter is provided, only those stage keys (case-insensitive) are considered.
        """
        if not gwp_block:
            return None

        stages: Dict[str, Number] = (gwp_block.get("stages") or {})  # dict of {stage:str -> value:number}
        if not isinstance(stages, dict) or not stages:
            return None

        # Normalize filter
        wanted = {s.upper() for s in stages_filter} if stages_filter else None

        total = 0.0
        for key, val in stages.items():
            if not isinstance(val, (int, float)):
                continue

            k = key.upper().strip()
            if k == "D" and not include_stage_D:
                continue

            if wanted is not None:
                # Allow filters like "A1", "A2", "A3", "A1-A3", "C1", etc.
                # If combined key like "A1-A3", include only if the combined key is explicitly in wanted.
                if k not in wanted:
                    continue

            total += float(val)

        return total

    # ----------------------------
    # Quantity / unit logic
    # ----------------------------
    def _functional_quantity_for_reference(
        self,
        ref_unit: str,
        *,
        density: Optional[Number],
        layer_ratio: float = 1.0,   # used only for volume-derived quantities
    ) -> Optional[float]:
        """
        Returns the element's functional quantity in the same unit as `ref_unit`.

        Ratio rules (per requirement):
        - For m³ references: use (volume * layer_ratio).
        - For kg references:
            * If mass = volume * density, apply ratio to volume ONLY ( (volume * layer_ratio) * density ).
            * If mass = area * thickness * density, DO NOT apply ratio.
        - For m² or piece/unit references: DO NOT apply ratio.
        """
        u = ref_unit.replace(" ", "")

        # Mass references
        if u in {"kg", "kilogram", "kilograms"} or u in {"t", "ton", "tonne", "tonnes"}:
            mass_kg = self._element_mass_kg(density=density, layer_ratio_for_volume=layer_ratio)
            if mass_kg is None:
                return None
            if u in {"t", "ton", "tonne", "tonnes"}:
                return mass_kg / 1000.0
            return mass_kg  # kg

        # Volume reference → apply ratio
        if u in {"m3", "m^3", "m³"}:
            vol = self._get_quantity_value("volume")
            if vol is not None:
                try:
                    return float(vol) * float(layer_ratio)
                except Exception:
                    return None

        # Area reference → no ratio
        if u in {"m2", "m^2", "m²"}:
            area = self._get_quantity_value("area")
            if area is not None:
                return float(area)

        # Piece / unit reference → no ratio
        if u in {"piece", "unit", "p", "pcs", "pieces", "units"}:
            pcs = (self._get_quantity_value("piece")
                or self._get_quantity_value("count")
                or self._get_quantity_value("quantity"))
            if pcs is not None:
                return float(pcs)

        return None


    def _element_mass_kg(
        self,
        *,
        density: Optional[Number],
        layer_ratio_for_volume: float = 1.0,  # NEW: used only for volume * density path
    ) -> Optional[float]:
        """
        Computes element mass in kg. Prefers:
        1) (volume * layer_ratio_for_volume) * density    <-- ratio applied here ONLY
        2) (area * thickness) * density                   <-- ratio NOT applied
        Returns None if insufficient data or no density.
        """
        if density is None:
            return None
        try:
            d = float(density)  # kg/m3
        except Exception:
            return None

        vol = self._get_quantity_value("volume")
        if vol is not None:
            try:
                return float(vol) * float(layer_ratio_for_volume) * d
            except Exception:
                return None

        area = self._get_quantity_value("area")
        thick = self._get_quantity_value("thickness")
        if area is not None and thick is not None:
            try:
                return float(area) * float(thick) * d
            except Exception:
                return None

        return None


    def _get_quantity_value(self, name: str) -> Optional[float]:
        """
        Fetch a quantity by 'name' from self.quantities, accepting both
        Pydantic models and plain dicts.

        Expected structures:
        - self.quantities.quantities -> List[Quantity(BaseModel)]
        - or self.quantities["quantities"] -> List[dict]
        """
        # 1) Get the list (works for Pydantic model or raw dict)
        qsrc = getattr(self, "quantities", None)
        if qsrc is None:
            return None

        qblock = None
        # Pydantic model path
        if hasattr(qsrc, "quantities"):
            qblock = getattr(qsrc, "quantities")
        # Dict fallback
        elif isinstance(qsrc, dict):
            qblock = qsrc.get("quantities")

        if not isinstance(qblock, list):
            return None

        target = (name or "").strip().lower()

        # 2) Iterate items that may be BaseModel or dict
        for q in qblock:
            # read name
            if hasattr(q, "name"):  # BaseModel
                q_name = (getattr(q, "name") or "").strip().lower()
            elif isinstance(q, dict):  # dict
                q_name = (q.get("name") or "").strip().lower()
            else:
                continue

            if q_name != target:
                continue

            # read value
            if hasattr(q, "value"):  # BaseModel
                v = getattr(q, "value")
            elif isinstance(q, dict):
                v = q.get("value")
            else:
                v = None

            if v is None:
                return None
            try:
                return float(v)
            except (TypeError, ValueError):
                return None

        return None


    # ----------------------------
    # placeholders
    # ----------------------------


    def calculate_lca(self):
        """
        Will only work if matched_items != None
        """
        pass

    def dissect_layers():
        pass


