from __future__ import annotations

from math import isfinite

from compas.data import Data
from compas_model.materials.material import Material
from compas_lca.enums.enums import PureComposite
from compas_lca.enums.enums import FractionBasis
from compas_lca.enums.enums import LabelOrigin
from compas_lca.enums.enums import MaterialRole

from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator


class ParsedMaterial(BaseModel):
    literal_name: Optional[str] = Field(
        None, 
        description="Verbatim Material Name AS FOUND in building element data",
        examples=["Stahl, 45-34, Pulverbeschichtung schwarz", 
                  "Glas SageGlassClimatop",
                  "Basic Wall:Innenwandelement Archisonic ohne MDF"] 
    )
    canonical_name: Optional[str] = Field(
        None, 
        description="Normalized material label",
        examples=["Reinforced Concrete", "Rigid Insulation", "Timber"] 
    )
    material_type: PureComposite = Field(
        PureComposite.unknown,
        description=(
            "Classify the material for LCA database mapping purposes:\n"
            "- pure → A material that maps directly to a single LCA database entry, "
            "even if it is itself a mixture of constituents (e.g., 'timber', 'brick', 'XPS insulation').\n"
            "- composite → A material descriptor that combines two or more distinct materials, "
            "each of which requires its own LCA database mapping. This includes elements that describe"
            "STRUCTURAL concrete (which always implicitly has reinforcement), STUD CONSTRUCTIONS,"
            "and any type of GRATING or RAILING (which will always have air gaps)"
            "(e.g., 'concrete + loadbearing' → concrete + rebar steel "
            "'metal stud cavity' → steel + air/insulation).\n"
            "- unknown → Cannot decide from the input."
        ),
        examples=["pure", "composite", "unknown"]
    )
    confidence: float = Field(
        ...,
        ge=0.0, le=1.0,
        description="Confidence score between 0 and 1 in the classification/mapping."
    )
    hints: List[str] = Field(
        default_factory=list,
        description="Qualifiers and hints that help downstream mapping to LCA database entries.",
        examples=['C30/37', 'B500B', 'rigid insulation', 'loose fill material']
    )

    @field_validator("literal_name", "canonical_name", mode="before")
    @classmethod
    def _strip_empty(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v or None
        return v


class ComponentShare(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(
        ...,
        description="Pure material name used downstream (literal for pure, canonical for composite material).",
        examples=["Concrete", "Rebar steel", "Timber studs", "Mineral wool", "Air"]
    )
    label_kind: LabelOrigin = Field(
        LabelOrigin.canonical,
        description="Whether 'name' is taken verbatim from the source (literal) or is a normalized label (canonical)."
    )
    # Optional, helps prevent overly generic names in composites
    role: MaterialRole = Field(
        MaterialRole.unknown,
        description="Functional role to disambiguate generic materials",
        examples=["grating", "adhesive"]
    )
    fraction: float = Field(
        ...,
        ge=0.0, le=1.0,
        description="Share on the parent basis (volume)."
    )
    notes: Optional[str] = None

    @field_validator("name")
    @classmethod
    def _trim_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("name must be non-empty")
        return s

    @field_validator("fraction")
    @classmethod
    def _finite_fraction(cls, v: float) -> float:
        if not isfinite(v):
            raise ValueError("fraction must be finite")
        if -1e-9 <= v < 0:
            return 0.0
        if 1 < v <= 1 + 1e-9:
            return 1.0
        return v


class MaterialBreakdown(BaseModel):
    """Decomposition of a material into pure components with fractions; extraction-only result."""
    model_config = ConfigDict(extra="ignore")
    canonical_name: str = Field(..., description="Normalized name of the (possibly composite) material.")
    basis: FractionBasis = Field("mass", description="Interpretation of component fractions.")
    components: List[ComponentShare] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list, description="Defaults used (e.g., rebar ratio).")
    uncertainty: Optional[str] = None
    provenance: Optional[str] = None

    @model_validator(mode="after")
    def _check_sum(self):
        if not self.components:
            raise ValueError("components must not be empty")
        total = sum(c.fraction for c in self.components)
        if not (0.999 <= total <= 1.001):
            raise ValueError(f"component fractions sum to {total:.6f}, expected ~1.0")
        return self