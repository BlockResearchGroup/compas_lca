from typing import Dict
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field
from pydantic import field_validator

from compas_lca.validators import ParsedNumber

# TO DO:
# add KBOB stage names, indicators, and units
# make generalizable workflow (database-agnostic)
# only need to load the constants from a specific databse
from .constants import EN15978_STAGES
from .constants import OBD_INDICATOR_NAME
from .constants import OBD_INDICATOR_UNITS
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
    stages: Dict[EN15978_STAGES, ParsedNumber] = Field(default_factory=dict)

    # Derive unit from the canonical map, not user-settable.
    @computed_field(return_type=str)
    @property
    def unit(self) -> str:
        return OBD_INDICATOR_UNITS[self.name]

    # Validators & normalizers
    @field_validator("stages")
    @classmethod
    def validate_stage_values(cls, v: Dict[EN15978_STAGES, ParsedNumber]) -> Dict[EN15978_STAGES, ParsedNumber]:
        # Keys are type-checked by Pydantic via STAGE_NAME; you can normalize values here if needed.
        return dict(v)

    # Convenience accessors
    def get(self, stage: EN15978_STAGES, default: Optional[ParsedNumber] = None) -> Optional[ParsedNumber]:
        """Return the value for one stage (or default if missing)."""
        return self.stages.get(stage, default)

    def has_stage(self, stage: EN15978_STAGES) -> bool:
        """True if a value is present for the given stage."""
        return stage in self.stages

    def total(self, include: Optional[List[EN15978_STAGES]] = None) -> ParsedNumber:
        """
        Sum across stages. If `include` is provided, only those stages are summed.
        """
        if include is None:
            return sum(self.stages.values())
        return sum(self.stages.get(s, 0) for s in include)

    def stage_items(self) -> List[tuple[EN15978_STAGES, ParsedNumber]]:
        """Return (stage, value) pairs for serialization."""
        return list(self.stages.items())

    def __repr__(self) -> str:
        inner = ", ".join(f"{k}={v}" for k, v in self.stages.items())
        return f'Indicator(name="{self.name}", unit="{self.unit}", stages={{ {inner} }})'


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
    # stages that had multiple scenarios which were averaged.
    # Keys are stage names (A1, A2, …, D); values are the list of scenario codes found (e.g. ["S1","S2"]).
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
        key = name.strip()  # `INDICATOR_NAME` is str-backed; strip for robustness
        return [ind for ind in self.indicators if ind.name == key]  # type: ignore[comparison-overlap]

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
        include_stages: Optional[List[EN15978_STAGES]] = None
    ) -> Dict[OBD_INDICATOR_NAME, ParsedNumber]:
        """
        Aggregate totals per indicator name across stages (first occurrence per name).
        If you allow duplicates and want them summed together, adapt this accordingly.
        """
        totals: Dict[OBD_INDICATOR_NAME, ParsedNumber] = {}
        for ind in self.indicators:
            if ind.name not in totals:
                totals[ind.name] = ind.total(include=include_stages)
        return totals

    def add(self, indicator: Indicator) -> None:
        """Append an Indicator to the collection."""
        self.indicators.append(indicator)

    def __iter__(self):
        return iter(self.indicators)

    def __len__(self):
        return len(self.indicators)

    def __repr__(self) -> str:
        inner = ", ".join(repr(ind) for ind in self.indicators)
        return f"Indicators([{inner}])"