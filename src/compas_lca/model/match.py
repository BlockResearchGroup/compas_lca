from typing import Optional
from typing import Dict
from typing import Any
from typing import List

from pydantic import BaseModel
from pydantic import Field

class Match(BaseModel):
    item_id: str    # InventoryItem id
    item_name: Optional[str]  # InventoryItem name
    # to ensure traceability
    dataset_source: Optional[str] = None # e.g., "OEKOBAUDAT 2024-I" / Maybe Enum?
    # to ensure traceability and plug into frontend packages (e.g., openLCA, Brightway)
    registration_number: Optional[str] = None
    # If obtainable, score the Match
    match_score: Optional[float]
    # matching criteria/procedure (how score was retreived)
    match_criteria: Optional[List[Dict[str, Any]]] = None
class Matches(BaseModel):
    core_id: str        # stable id per element's MatchingCore
    matches: List[Match] = Field(default_factory=list)