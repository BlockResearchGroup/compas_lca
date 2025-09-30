from typing import List, Optional, Literal, Annotated
from pydantic import BaseModel, Field

FieldType = Literal["bool", "string", "float", "integer", "enum", "range", "ordinal_enum"]
Provenance = Literal["explicit", "inferred"]

class FieldProposal(BaseModel):
    name: str = Field(..., pattern=r"^[a-z0-9_]+$", description="Canonical snake_case field name")
    type: FieldType
    rationale: str = Field(..., max_length=280)
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    provenance: Provenance = Field(..., description="Was the field explicitly stated or inferred from cues?")
    # Optional hints / metadata
    enum_options: Optional[List[str]] = Field(
        default=None, description="If type='enum' or 'ordinal_enum', suggested options in intended order"
    )
    unit: Optional[str] = Field(
        default=None, description="If type in {'float','integer','range'}, preferred unit (e.g., 'W/m·K', 'kg/m³', 'min')"
    )
    applicability: Optional[List[str]] = Field(
        default=None, description="Tags like ['bio_based','mineral','foam','loose_fill','boards','batts','spray']"
    )
    evidence: Optional[List[str]] = Field(
        default=None, description="Short quotes/phrases from the EPD that support the field or its inference cue(s)"
    )
    inference_basis: Optional[List[str]] = Field(
        default=None, description="If inferred, brief domain-knowledge rules applied (e.g., 'XPS ⇒ polystyrene foam; closed-cell')"
    )

class ProposedFields(BaseModel):
    document_id: Optional[str] = None
    fields: List[FieldProposal]
