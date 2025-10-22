from typing import List

from pydantic import BaseModel
from pydantic import Field

from compas_lca.enums import EntryKind

class DataKind(BaseModel):
    """
    Classifies the input dataset as a material, a component, or unknown.
    """
    kind: EntryKind = Field(
        ..., 
        description="One of: material, component, unknown.",
        examples=["material", "component", "unknown"]
    )
    rationale: str = Field(
        ...,
        description="One-sentence justification based on definitions/criteria; ≤ 280 chars."
    )
    evidence: List[str] = Field(
        default_factory=list,
        description="Exact phrases/fields from the dataset that support the decision."
    )