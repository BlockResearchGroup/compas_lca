from typing import Dict
from typing import List
from typing import Literal
from typing import Iterable
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field
from pydantic import field_serializer
from pydantic import field_validator

from .constants import EN15978_STAGES
from .constants import OBD_INDICATOR_NAME
from .constants import OBD_INDICATOR_UNITS

class IndicatorScenario(BaseModel):
    """One scenario value for a stage."""
    code: Optional[str] = Field(
        None, description="Scenario code if present (e.g., 'S1', 'S2'); None if not provided."
    )
    description: Optional[str] = Field(
        None, description="Free-text scenario description from the source."
    )
    value: Optional[float] = Field(
        None, description="Numeric indicator value for this scenario and stage."
    )

class Indicator(BaseModel):
    """
    One LCA indicator with values per life cycle stage.

    Example:
        Indicator(
            name="GWPtotal",
            stages={"A1-A3": 12.3, "A4": 0.6, "C3": 0.1}
        )
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    name: OBD_INDICATOR_NAME
    stages: Dict[EN15978_STAGES, List[IndicatorScenario]] = Field(
        default_factory=dict,
        description="Map of stage -> list of scenarios (one or many)."
    )

    # -------- inbound normalization --------

    @field_validator("stages", mode="before")
    @classmethod
    def _normalize_stages(
        cls,
        v: Dict[EN15978_STAGES, object],
    ) -> Dict[EN15978_STAGES, List[IndicatorScenario]]:
        """
        Accepts either:
          - scalar numbers: {"A1-A3": 12.3}
          - list of scenario dicts: {"C3": [{"code": "S1", "value": ...}, ...]}
        and converts them into Dict[stage, List[IndicatorScenario]].
        """
        if v is None:
            return {}

        out: Dict[EN15978_STAGES, List[IndicatorScenario]] = {}

        for stage, raw in v.items():

            # Allow: scalar → one scenario
            if isinstance(raw, (int, float)):
                out[stage] = [IndicatorScenario(value=float(raw))]

            # Allow: list of dicts or list of scalars
            elif isinstance(raw, list):
                scenarios: List[IndicatorScenario] = []
                for item in raw:
                    if isinstance(item, IndicatorScenario):
                        scenarios.append(item)
                    elif isinstance(item, dict):
                        scenarios.append(IndicatorScenario(**item))
                    elif isinstance(item, (int, float)):
                        scenarios.append(IndicatorScenario(value=float(item)))
                    else:
                        raise TypeError(
                            f"Unsupported scenario item type for stage {stage}: {type(item)!r}"
                        )
                out[stage] = scenarios

            # Allow: dict representing a single scenario
            elif isinstance(raw, dict):
                out[stage] = [IndicatorScenario(**raw)]
            else:
                raise TypeError(f"Unsupported stages value type for stage {stage}: {type(raw)!r}")

        return out

    # -------- outbound compact serialization --------

    @field_serializer("stages", when_used="json")
    def _serialize_stages_compact(
        self, stages: Dict[EN15978_STAGES, List[IndicatorScenario]], _info
    ):
        """
        Compact JSON:
        - If a stage has exactly one scenario AND (code is None) AND (description is None),
          serialize that stage as a scalar {stage: value}.
        - Otherwise, serialize as a list of scenario dicts, excluding None fields.
        """
        out: Dict[str, object] = {}
        for stage, scenarios in stages.items():
            present = [s for s in scenarios if s.value is not None]

            if (
                len(present) == 1
                and present[0].code is None
                and (present[0].description is None or present[0].description == "")
            ):
                out[stage] = present[0].value
            else:
                out[stage] = [s.model_dump(exclude_none=True) for s in present]
        return out

    # -------- metadata --------

    @computed_field(return_type=str)
    @property
    def unit(self) -> str:
        return OBD_INDICATOR_UNITS[self.name]

    # -------- helpers --------

    def stage_mean(self, stage: EN15978_STAGES) -> Optional[float]:
        vals = [s.value for s in self.stages.get(stage, []) if s.value is not None]
        return sum(vals)/len(vals) if vals else None

    def stage_single_value(self, stage: EN15978_STAGES) -> Optional[float]:
        """Returns the value only if exactly one scenario exists for the stage; else None."""
        items = [s for s in self.stages.get(stage, []) if s.value is not None]
        return items[0].value if len(items) == 1 else None

    # -------- scenario aggregation helpers --------

    def stage_value(
        self,
        stage: EN15978_STAGES,
        *,
        agg: Literal["mean", "single", "sum"] = "mean",
    ) -> Optional[float]:
        """
        Aggregate scenarios for one stage into a single numeric value.

        Parameters
        ----------
        stage : EN15978_STAGES
            The stage key (e.g. 'A1', 'A1-A3', 'C3', 'D', ...).
        agg : {'mean', 'single', 'sum'}
            - 'mean'   → arithmetic mean of all scenario values (default).
            - 'single' → only if exactly one scenario exists; otherwise None.
            - 'sum'    → sum of all scenario values.

        Returns
        -------
        float | None
        """
        scenarios = self.stages.get(stage, [])
        vals = [s.value for s in scenarios if s.value is not None]
        if not vals:
            return None

        if agg == "mean":
            return sum(vals) / len(vals)
        if agg == "sum":
            return sum(vals)
        if agg == "single":
            return vals[0] if len(vals) == 1 else None
        return None

    def stage_dict(
        self,
        *,
        include_stages: Optional[Iterable[EN15978_STAGES]] = None,
        include_stage_D: bool = True,
        agg: Literal["mean", "single", "sum"] = "mean",
    ) -> Dict[EN15978_STAGES, float]:
        """
        Return a dict of {stage -> aggregated_value} for this indicator.

        Examples
        --------
        gwp.stage_dict()                           # all stages, mean across scenarios
        gwp.stage_dict(include_stages=['A1-A3'])   # just A1-A3
        gwp.stage_dict(include_stage_D=False)      # exclude D
        """
        wanted = set(include_stages) if include_stages is not None else None
        out: Dict[EN15978_STAGES, float] = {}
        for stage, _scenarios in self.stages.items():
            s_upper = str(stage).upper().strip()
            if s_upper == "D" and not include_stage_D:
                continue
            if wanted is not None and stage not in wanted:
                continue
            val = self.stage_value(stage, agg=agg)
            if val is not None:
                out[stage] = float(val)
        return out

    def total(
        self,
        *,
        include_stages: Optional[Iterable[EN15978_STAGES]] = None,
        include_stage_D: bool = True,
        agg: Literal["mean", "single", "sum"] = "mean",
    ) -> Optional[float]:
        """
        Sum indicator over selected stages.

        This is your “specific value per declared unit” for *this indicator*.

        Parameters
        ----------
        include_stages : iterable of stages, optional
            If provided, only these stages are considered. If None, all are considered.
        include_stage_D : bool
            Whether to include stage 'D' in the sum.
        agg : {'mean', 'single', 'sum'}
            How to aggregate multiple scenarios for each stage.

        Returns
        -------
        float | None
        """
        stage_values = self.stage_dict(
            include_stages=include_stages,
            include_stage_D=include_stage_D,
            agg=agg,
        )
        if not stage_values:
            return None
        return sum(stage_values.values())


class Indicators(BaseModel):
    """
    Collection of Indicator items for one EPD or LCA database entry.
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    indicators: List[Indicator] = Field(default_factory=list)
    scenarios: Optional[Dict[EN15978_STAGES, List[str]]] = Field(
        default=None,
        description="For stages with >1 scenario, records the scenario codes that were averaged."
    )

    # Lookups & helpers
    def get(self, name: OBD_INDICATOR_NAME) -> List[Indicator]:
        """
        Find all indicators with the given name.
        (Multiple entries with the same name are allowed in case you want to distinguish by e.g. dataset source.)
        """
        key = name.strip()
        return [ind for ind in self.indicators if ind.name == key]

    def get_one(self, name: OBD_INDICATOR_NAME) -> Optional[Indicator]:
        """
        Return the first indicator with the given name, or None if not present.
        """
        matches = self.get(name)
        return matches[0] if matches else None

    def names(self) -> List[OBD_INDICATOR_NAME]:
        """List of indicator names present (with possible duplicates if duplicates exist)."""
        return [ind.name for ind in self.indicators]

    def total_by_name(
        self,
        include_stages: Optional[Iterable[EN15978_STAGES]] = None,
        include_stage_D: bool = True,
        agg: Literal["mean", "single", "sum"] = "mean",
    ) -> Dict[OBD_INDICATOR_NAME, float]:
        """
        Aggregate totals per indicator name across stages (first occurrence per name).
        """
        totals: Dict[OBD_INDICATOR_NAME, float] = {}
        for ind in self.indicators:
            if ind.name not in totals:
                val = ind.total(
                    include_stages=include_stages,
                    include_stage_D=include_stage_D,
                    agg=agg,
                )
                if val is not None:
                    totals[ind.name] = val
        return totals

    # -------- convenience wrappers around Indicator.total/stage_dict --------

    def indicator_value(
        self,
        name: OBD_INDICATOR_NAME,
        *,
        include_stages: Optional[Iterable[EN15978_STAGES]] = None,
        include_stage_D: bool = True,
        agg: Literal["mean", "single", "sum"] = "mean",
    ) -> Optional[float]:
        """
        Get the specific impact value (per reference unit) for one indicator name.
        """
        ind = self.get_one(name)
        if ind is None:
            return None
        return ind.total(
            include_stages=include_stages,
            include_stage_D=include_stage_D,
            agg=agg,
        )

    def stage_dict_for(
        self,
        name: OBD_INDICATOR_NAME,
        *,
        include_stages: Optional[Iterable[EN15978_STAGES]] = None,
        include_stage_D: bool = True,
        agg: Literal["mean", "single", "sum"] = "mean",
    ) -> Dict[EN15978_STAGES, float]:
        """
        Return {stage -> value} for one indicator name; empty dict if not present.
        """
        ind = self.get_one(name)
        if ind is None:
            return {}
        return ind.stage_dict(
            include_stages=include_stages,
            include_stage_D=include_stage_D,
            agg=agg,
        )

    def add(self, indicator: Indicator) -> None:
        self.indicators.append(indicator)

    def __iter__(self):
        return iter(self.indicators)

    def __len__(self):
        return len(self.indicators)

    def __repr__(self) -> str:
        inner = ", ".join(repr(ind) for ind in self.indicators)
        return f"Indicators([{inner}])"