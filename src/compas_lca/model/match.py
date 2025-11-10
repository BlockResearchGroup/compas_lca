from typing import Optional
from typing import Dict
from typing import Any
from typing import List

from pydantic import BaseModel
from pydantic import Field

class Match(BaseModel):
    item_id: str    # InventoryItem id
    item_name: Optional[str]  # InventoryItem name
    # If obtainable, score the Match
    score: Optional[float]
    # a short explanation list is useful; shows the matching criteria/procedure (how score was retreived)
    explain: Optional[List[Dict[str, Any]]] = None
    # to ensure trace
    dataset_source: Optional[str] = None # e.g., "OEKOBAUDAT 2024-I"
    # store a selection of InventoryItem (ref unit, subset of indicators), retreived with InventoryItem.snapshot() 
    snapshot: Optional[Dict[str, Any]] = None

class Matches(BaseModel):
    core_id: str        # stable id per element's MatchingCore
    matches: List[Match] = Field(default_factory=list)