from uuid import uuid4
from uuid import UUID

from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.matching_core.core import MatchingCore

from compas_lca.inventory.indicator import Indicators

class InventoryItem(BaseModel):
    """
    Represents a single Life Cycle Assessment (LCA) inventory entry.

    Each inventory item encapsulates one material or component record,
    its associated impact indicators, and its metadata (such as source and reference unit).
    This model provides a unique identifier and enforces strict validation rules
    for consistent data handling across the LCA matching core.

    Attributes
    ----------
    id : UUID
        Unique identifier for the inventory item (auto-generated).
    item_core : MatchingCore
        Core data describing the LCA inventory entry, including material or component attributes.
    indicators : Indicators, optional
        Environmental impact indicators associated with the inventory entry.
    reference_unit : str, optional
        Reference unit of measurement for the inventory (e.g., "kg", "m²", "m³").
    source : str, optional
        Source of the environmental product declaration (EPD), such as "Ökobau.dat" or "KBOB".
    """
    model_config = ConfigDict(extra = "forbid")
    id: UUID = Field(default_factory=uuid4)
    item_core: MatchingCore         # data describing the LCA Inventory entry (material or component)
    indicators: Indicators          # associated indicators of the LCA Inventory entry
    reference_unit: str             # perhaps Enum of most common reference units?
    source: Optional[str] = None    # source of the EPD (e.g., Oekobaudat, KBOB)

    @classmethod
    def from_parts(
        cls,
        matching_core: MatchingCore,
        indicators: Indicators,
        reference_unit: str,
        source: Optional[str] = None,
    ) -> "InventoryItem":
        """Factory for consistent construction and future normalization hooks."""
        return cls(
            item_core=matching_core,
            indicators=indicators,
            reference_unit=reference_unit,
            source=source,
        )