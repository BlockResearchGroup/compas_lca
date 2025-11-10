from uuid import uuid4
from uuid import UUID

from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.matching_core.core import MatchingCore

from compas_lca.inventory.indicator import Indicators
from compas_lca.inventory.metadata import ItemMetadata
from compas_lca.inventory.reference import ReferenceInfo

class InventoryItem(BaseModel):
    """
    Single LCA inventory record combining product metadata and impact indicators.

    Attributes
    ----------
    id : UUID, default = uuid4()
        Auto-generated unique identifier for this inventory item.
    item_core : MatchingCore
        Core attributes that describe the material/component used for matching and classification.
    indicators : Indicators
        Environmental impact indicators (e.g., GWP, ADP, etc.) associated with this item.
    reference : ReferenceInfo
        Includes reference_size -> Numerical magnitude of the declared unit (e.g., 1, 1000).
        Must be positive. Typically left as 1 for standard EPD declared units.
        Includes reference_unit (RefUnitType) -> Declared/reference unit for the item 
        (e.g. "kg", "m", "m2", "m3", "pcs"). Flexible inputs are normalized to the `RefUnit` 
        enum by a validator.
    metadata : Optional[ItemMetadata]
        Provenance of the EPD or dataset (e.g., “Ökobau.dat”, “KBOB”), including any
        additional metadata defined in `ItemMetadata`.

    Notes
    -----
    - If `reference_unit` is already a `RefUnit`, it is accepted as-is; otherwise common
      spellings/aliases are normalized or an error is raised if ambiguous.
    """

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    item_core: MatchingCore
    reference: ReferenceInfo
    indicators: Indicators
    metadata: Optional[ItemMetadata] = None

    @classmethod
    def from_parts(
        cls,
        matching_core: MatchingCore,
        reference: ReferenceInfo,
        indicators: Indicators,
        metadata: Optional[ItemMetadata] = None,
    ) -> "InventoryItem":
        """Factory for consistent construction and future normalization hooks."""
        return cls(
            item_core=matching_core,
            reference=reference,
            indicators=indicators,
            metadata=metadata
        )



# Should ideally be a method within the class, but problem is if dictionary is passed?
# I assume mostly items will not be stored in memory but rather in disk as serialized files.
def snapshot(item: Any) -> dict:
    """
    Return a lightweight summary of an InventoryItem for embedding
    in LcaElements (to avoid large serializations). Customizable.
    """
    # Normalize
    if hasattr(item, "model_dump"):
        data = item.model_dump(exclude_none=True)
    elif isinstance(item, dict):
        data = item
    else:
        raise TypeError(f"Unsupported item type for snapshot: {type(item)}")

    reference = data.get("reference") or {}
    indicators = data.get("indicators") or {}
    core = data.get("item_core") or {}

    # --- density ---
    density = None
    facet = core.get("facet") or {}
    if isinstance(facet, dict):
        density = facet.get("density")

    # --- Reference ---
    ref = None
    if reference:
        ref = {
            "size": reference.get("size"),
            "unit": reference.get("unit"),
        }

    # --- GWP ---
    gwp = None
    inds = indicators.get("indicators")
    if isinstance(inds, list):
        for ind in inds:
            if ind.get("name") == "GWPtotal":
                gwp = {
                    "stages": dict(ind.get("stages", {})),
                    "unit": ind.get("unit"),
                }
                break

    # --- Build snapshot ---
    return {
        "reference": ref,
        "density": density,
        "GWP": gwp,
    }
