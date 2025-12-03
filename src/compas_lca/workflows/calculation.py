"""
Compute LCA indicator values for one LcaElement.

Workflow
--------
1. LcaElement has, per MatchingCore, a list of lightweight Match objects (Matches).
   Each Match references an InventoryItem by `item_id`.

2. InventoryItem objects are stored as serialized JSON files in a directory.
   This module provides FileInventoryRepository to load them on demand.

3. Each InventoryItem has:
   - reference: ReferenceInfo (size, unit)
   - indicators: Indicators

   From this a *specific* indicator value per declared unit can be obtained,
   summed over desired life-cycle stages.

4. LcaElementCalculator then:
   - Retrieves the specific indicator value for each Match (per InventoryItem).
   - Scales it from "per declared unit" to "per element" using LcaElement.quantities,
     the InventoryItem reference unit, and (optionally) layer thickness ratios.
   - Aggregates over all matches to produce min, max, median, and sums.
"""

from dataclasses import dataclass

import json

from pathlib import Path

from statistics import median

from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Protocol
from typing import Union

from compas_lca.inventory.item import InventoryItem
from compas_lca.inventory.constants import EN15978_STAGES
from compas_lca.inventory.constants import OBD_INDICATOR_NAME
from compas_lca.model.lca_element import LcaElement
from compas_lca.model.match import Match

Number = Union[int, float]


# =============================================================================
# Inventory access abstraction
# =============================================================================

class InventoryRepository(Protocol):
    """
    Abstract interface for retrieving InventoryItem objects by id.

    This allows plugging in different backends (filesystem, SQL database, API, etc.)
    without changing the LcaElementCalculator logic.
    """

    def get(self, item_id: str) -> InventoryItem:
        """
        Retrieve one InventoryItem by its id (UUID string).

        Raises
        ------
        FileNotFoundError or custom exception if the item cannot be found.
        """
        ...


class FileInventoryRepository:
    """
    File-based implementation of InventoryRepository.

    Uses a filename convention for efficiency, but verifies that the JSON
    content actually matches the requested id.

    Assumptions
    -----------
    - Each InventoryItem is serialized as JSON in `root` directory.
    - Filenames follow the convention `<item_id>.json`, where `item_id`
      is the UUID stored in Match.item_id and InventoryItem.id.
    - The top-level JSON object has an "id" field.

    Example
    -------
    repo = FileInventoryRepository("/path/to/inventory_dir")
    item = repo.get("9a39a7e8-cade-4228-8a81-bd459ce012a3")
    """

    def __init__(self, root: Union[str, Path]) -> None:
        self.root = Path(root)

    def get(self, item_id: str) -> InventoryItem:
        """
        Retrieve one InventoryItem by its id.
        """
        path = self.root / f"{item_id}.json"
        if not path.is_file():
            raise FileNotFoundError(
                f"InventoryItem file not found for id={item_id}: {path}"
            )

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        json_id = str(data.get("id") or "")
        if json_id != item_id:
            raise ValueError(
                f"ID mismatch for InventoryItem in file {path}: "
                f"requested id={item_id!r}, JSON id={json_id!r}"
            )

        return InventoryItem.model_validate(data)


# =============================================================================
# Result dataclasses
# =============================================================================

@dataclass
class ElementIndicatorStats:
    """
    Statistics for one LcaElement and one indicator.

    Attributes
    ----------
    samples : List[float]
        Element-level emission values for each Match (one value per matched InventoryItem).
    min : Optional[float]
        Minimum sample, or None if no samples.
    max : Optional[float]
        Maximum sample, or None if no samples.
    median : Optional[float]
        Median of samples, or None if no samples.
    sum : Optional[float]
        Sum of samples, or None if no samples.
    """
    samples: List[float]
    min: Optional[float]
    max: Optional[float]
    median: Optional[float]
    sum: Optional[float]


@dataclass
class ElementIndicatorTotalRange:
    """
    Per-core min/max totals for a multi-layer element.

    Attributes
    ----------
    min_total : Optional[float]
        Sum across cores of each core's *minimum* sample, or None if no data.
    max_total : Optional[float]
        Sum across cores of each core's *maximum* sample, or None if no data.
    """
    min_total: Optional[float]
    max_total: Optional[float]


# =============================================================================
# LcaElement calculator
# =============================================================================

class LcaElementCalculator:
    """
    Performs indicator calculations for LcaElement using external InventoryItem records.

    This class is deliberately *stateless* with respect to elements: it only
    depends on an InventoryRepository for loading InventoryItem objects.

    Typical usage
    -------------
    repo = FileInventoryRepository("/path/to/inventory_dir")
    calc = LcaElementCalculator(repo)

    stats = calc.element_indicator_stats(
        element,
        indicator_name="GWPtotal",
        include_stages=["A1-A3", "C3"],
        include_stage_D=False,
    )
    """

    def __init__(self, inventory_repo: InventoryRepository) -> None:
        self.repo = inventory_repo

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def element_indicator_stats(
        self,
        element: LcaElement,
        *,
        indicator_name: OBD_INDICATOR_NAME,
        include_stages: Optional[Iterable[EN15978_STAGES]] = None,
        include_stage_D: bool = True,
        scenario_agg: str = "mean",  # "mean" | "sum" | "single"
    ) -> ElementIndicatorStats:
        """
        Compute basic statistics (min, max, median, sum) of element-level emissions
        for one indicator over all Matches across all cores.

        Each Match yields one sample:
        (specific indicator per reference unit) * (element functional quantity).

        Parameters
        ----------
        element : LcaElement
            The element whose matches and quantities will be used.
        indicator_name : OBD_INDICATOR_NAME
            Name of the indicator (e.g. "GWPtotal", "GWPfossil").
        include_stages : iterable of EN15978_STAGES, optional
            If provided, restrict indicator stages to this subset.
            If None, all available stages are included.
        include_stage_D : bool, default True
            Whether to include stage "D" in the indicator total.
        scenario_agg : {'mean', 'sum', 'single'}
            How to aggregate multiple scenarios per stage (see Indicator.stage_value).

        Returns
        -------
        ElementIndicatorStats
        """
        samples = self._element_indicator_samples(
            element,
            indicator_name=indicator_name,
            include_stages=include_stages,
            include_stage_D=include_stage_D,
            scenario_agg=scenario_agg,
        )

        if not samples:
            return ElementIndicatorStats(samples=[], min=None, max=None, median=None, sum=None)

        return ElementIndicatorStats(
            samples=samples,
            min=min(samples),
            max=max(samples),
            median=median(samples),
            sum=sum(samples),
        )

    def element_indicator_total_range(
        self,
        element: LcaElement,
        *,
        indicator_name: OBD_INDICATOR_NAME,
        include_stages: Optional[Iterable[EN15978_STAGES]] = None,
        include_stage_D: bool = True,
        scenario_agg: str = "mean",
    ) -> ElementIndicatorTotalRange:
        """
        Compute a "range" of possible totals for a multi-layer element by:

        - For each core_id:
            * Gather its samples (one per matched InventoryItem).
            * Take min(sample) and max(sample) for that core.
        - Sum per-core minima → min_total
        - Sum per-core maxima → max_total

        This is useful if each core represents a different material layer and
        you're exploring uncertainty/variance across database choices.

        Returns
        -------
        ElementIndicatorTotalRange
        """
        if not element.matched_items:
            return ElementIndicatorTotalRange(min_total=None, max_total=None)

        per_core_min: Dict[str, float] = {}
        per_core_max: Dict[str, float] = {}

        for core_matches in element.matched_items:
            cid = core_matches.core_id
            samples = self._core_indicator_samples(
                element,
                core_id=cid,
                indicator_name=indicator_name,
                include_stages=include_stages,
                include_stage_D=include_stage_D,
                scenario_agg=scenario_agg,
            )
            if samples:
                per_core_min[cid] = min(samples)
                per_core_max[cid] = max(samples)

        if not per_core_min:
            return ElementIndicatorTotalRange(min_total=None, max_total=None)

        min_total = sum(per_core_min.values())
        max_total = sum(per_core_max.values())
        return ElementIndicatorTotalRange(min_total=min_total, max_total=max_total)

    # -------------------------------------------------------------------------
    # Internals
    # -------------------------------------------------------------------------

    def _core_indicator_samples(
        self,
        element: LcaElement,
        *,
        core_id: str,
        indicator_name: OBD_INDICATOR_NAME,
        include_stages: Optional[Iterable[EN15978_STAGES]],
        include_stage_D: bool,
        scenario_agg: str,
    ) -> List[float]:
        """
        Collect samples for one core_id only (one sample per Match for that core).
        """
        if not element.matched_items:
            return []

        ratio_map = element.layer_ratio_map()
        target_id = core_id
        samples: List[float] = []

        for core_matches in element.matched_items:
            if core_matches.core_id != target_id:
                continue
            layer_ratio = ratio_map.get(core_matches.core_id, 1.0)
            for match in core_matches.matches:
                val = self._match_indicator_for_element(
                    element,
                    match,
                    indicator_name=indicator_name,
                    include_stages=include_stages,
                    include_stage_D=include_stage_D,
                    scenario_agg=scenario_agg,
                    layer_ratio=layer_ratio,
                )
                if val is not None:
                    samples.append(val)

        return samples

    def _element_indicator_samples(
        self,
        element: LcaElement,
        *,
        indicator_name: OBD_INDICATOR_NAME,
        include_stages: Optional[Iterable[EN15978_STAGES]],
        include_stage_D: bool,
        scenario_agg: str,
    ) -> List[float]:
        """
        Collect a list of element-level indicator values, one per Match,
        pooling over all cores.
        """
        if not element.matched_items:
            return []

        ratio_map = element.layer_ratio_map()
        samples: List[float] = []

        for core_matches in element.matched_items:
            layer_ratio = ratio_map.get(core_matches.core_id, 1.0)
            for match in core_matches.matches:
                val = self._match_indicator_for_element(
                    element,
                    match,
                    indicator_name=indicator_name,
                    include_stages=include_stages,
                    include_stage_D=include_stage_D,
                    scenario_agg=scenario_agg,
                    layer_ratio=layer_ratio,
                )
                if val is not None:
                    samples.append(val)

        return samples

    def _match_indicator_for_element(
        self,
        element: LcaElement,
        match: Match,
        *,
        indicator_name: OBD_INDICATOR_NAME,
        include_stages: Optional[Iterable[EN15978_STAGES]],
        include_stage_D: bool,
        scenario_agg: str,
        layer_ratio: float = 1.0,
    ) -> Optional[float]:
        """
        Compute element-level value for one Match (one InventoryItem).

        Steps
        -----
        1. Load InventoryItem by item_id.
        2. Get specific indicator value (per reference unit) using
           InventoryItem.indicators.indicator_value(...).
        3. Derive element functional quantity in the same unit as the InventoryItem
           reference.
        4. Scale: element_value = specific_value * (element_quantity / ref_size).
        """
        inv = self.repo.get(match.item_id)

        # 1) reference info
        ref_size = inv.reference.size
        ref_unit_obj = inv.reference.unit
        ref_unit = getattr(ref_unit_obj, "value", str(ref_unit_obj)).strip().lower()

        if not ref_size or not ref_unit:
            return None

        # 2) specific indicator value per reference unit
        specific = inv.indicators.indicator_value(
            indicator_name,
            include_stages=include_stages,
            include_stage_D=include_stage_D,
            agg=scenario_agg,  # "mean", "sum", or "single"
        )
        if specific is None:
            return None

        # 3) density (if available) – assumed to be stored on item_core (kg/m3)
        density = getattr(inv.item_core, "density", None)

        # element functional quantity in same unit as reference
        qty_val = _functional_quantity_for_reference(
            element,
            ref_unit,
            density=density,
            layer_ratio=layer_ratio,
        )
        if qty_val is None:
            return None

        try:
            scale = float(qty_val) / float(ref_size)
        except Exception:
            return None

        return specific * scale


# =============================================================================
# Quantity & layer helpers (pure functions)
# =============================================================================

def _functional_quantity_for_reference(
    element: LcaElement,
    ref_unit: str,
    *,
    density: Optional[Number],
    layer_ratio: float = 1.0,
) -> Optional[float]:
    """
    Returns the element's functional quantity in the same unit as `ref_unit`.

    Ratio rules (matching your earlier design)
    ------------------------------------------
    - For m³ references: use (volume * layer_ratio).
    - For kg references:
        * If mass = volume * density, apply ratio to volume ONLY:
              (volume * layer_ratio) * density
        * If mass = area * thickness * density, DO NOT apply ratio.
    - For m² or piece/unit references: DO NOT apply ratio.

    Parameters
    ----------
    element : LcaElement
        Element whose quantities are used.
    ref_unit : str
        Declared unit from InventoryItem.reference (normalized to lowercase).
    density : float | None
        Density in kg/m³ form InventoryItem.item_core.density (if available).
    layer_ratio : float
        Thickness ratio for the corresponding core when splitting volumes.
    """
    u = ref_unit.replace(" ", "").lower()

    # Mass references
    if u in {"kg", "kilogram", "kilograms"} or u in {"t", "ton", "tonne", "tonnes"}:
        mass_kg = _element_mass_kg(element, density=density, layer_ratio_for_volume=layer_ratio)
        if mass_kg is None:
            return None
        if u in {"t", "ton", "tonne", "tonnes"}:
            return mass_kg / 1000.0
        return mass_kg

    # Volume reference → apply ratio
    if u in {"m3", "m^3", "m³"}:
        vol = element.get_quantity_value("volume")
        if vol is not None:
            try:
                return float(vol) * float(layer_ratio)
            except Exception:
                return None

    # Area reference → no ratio
    if u in {"m2", "m^2", "m²"}:
        area = element.get_quantity_value("area")
        if area is not None:
            return float(area)

    # Piece / unit reference → no ratio
    if u in {"piece", "unit", "p", "pcs", "pieces", "units"}:
        pcs = (
            element.get_quantity_value("piece")
            or element.get_quantity_value("count")
            or element.get_quantity_value("quantity")
        )
        if pcs is not None:
            return float(pcs)

    return None


def _element_mass_kg(
    element: LcaElement,
    *,
    density: Optional[Number],
    layer_ratio_for_volume: float = 1.0,
) -> Optional[float]:
    """
    Computes element mass in kg, using either:

    1) (volume * layer_ratio_for_volume) * density    (volume-derived mass)
    2) (area * thickness) * density                   (layered surface; no ratio)

    Returns
    -------
    float | None
        Mass in kg if enough data is available, else None.
    """
    if density is None:
        return None
    try:
        d = float(density)  # kg/m3
    except Exception:
        return None

    vol = element.get_quantity_value("volume")
    if vol is not None:
        try:
            return float(vol) * float(layer_ratio_for_volume) * d
        except Exception:
            return None

    area = element.get_quantity_value("area")
    thick = element.get_quantity_value("thickness")
    if area is not None and thick is not None:
        try:
            return float(area) * float(thick) * d
        except Exception:
            return None

    return None