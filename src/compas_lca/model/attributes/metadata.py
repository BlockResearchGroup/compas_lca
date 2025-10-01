from __future__ import annotations

import re

from typing import Any
from typing import Optional

from compas_lca.enum import YesNoEither
from compas_lca.enum import DataResolution

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

class Metadata(BaseModel):
    """Source-agnostic Metadata attributes for LCA database mapping."""
    element_name: str = Field(
        ...,
        description="Exact element name as found in the raw building element data.",
        examples=["Wall W-23", "Type: C30/37 Concrete Wall"]
    )
    description: Optional[str] = Field(
        None,
        description="Short one-sentence description of the element using only information present in the source text.",
        examples=["Cast-in-place concrete wall for core enclosure."]
    )
    component_type: Optional[str] = Field(
        None,
        description=(
            "Generic component type if explicitly indicated (e.g., 'slab', 'wall', 'roof', 'window', "
            "'column', 'beam', 'foundation')."
        ),
        examples=["wall", "slab"]
    )
    object_type: Optional[str] = Field(
        None,
        description=(
            "Element's object or layer type label if present (e.g., 'ObjectType', 'Type Name', 'Layer'). "
            "Use the text verbatim from the source."
        ),
        examples=["Structural - Concrete", "Type A-200"]
    )
    classification: Optional[str] = Field(
        None,
        description=(
            "Verbatim transcription of any official classification system reference if present. "
            "Copy exactly as in the source text."
        ),
        examples=['OmniClass 21-02 10 20', 'UniClass Ss_20_10_25']
    )
    loadbearing: YesNoEither = Field(
        YesNoEither.unknown,
        description=(
            "Whether the element is load-bearing.\n"
            "- yes → explicitly load-bearing.\n"
            "- no → explicitly not load-bearing.\n"
            "- either → this element type can appear as both structural and non-structural variants; context-dependent.\n"
            "- unknown → not specified."
        ),
        examples=["yes", "either"]
    )
    interior: YesNoEither = Field(
        YesNoEither.unknown,
        description=(
            "Whether the element is specified for interior use.\n"
            "- yes → explicitly interior.\n"
            "- no → explicitly exterior.\n"
            "- either → this element can theoretically be interior or exterior, context-dependent.\n"
            "- unknown → not specified."
        ),
        examples=["yes", "either", "unknown"]
    )
    u_value: Optional[float] = Field(
        None,
        ge=0,
        description="Thermal transmittance in W/m²K. Only set if explicitly present.",
        examples=[0.24]
    )
    density: Optional[float] = Field(
        None,
        ge=0,
        description="Material density in kilograms per cubic metre (kg/m³).",
        examples=[2400.0, 120.5]
    )
    data_resolution: DataResolution = Field(
        DataResolution.generic,
        description=(
            "Choose EXACTLY ONE resolution level. Start at the most specific and stop at the first match:\n"
            "• site_specific → Single manufacturer AND single production site/plant.\n"
            "  Examples: 'ACME Insulation - Plant Y', 'Factory Linz - Line 2', 'BrandX Concrete, Plant 17'.\n"
            "• product_specific → Single manufacturer/brand (optionally model/SKU/EPD ID).\n"
            "  Examples: 'Forster Variotherm - 60 x 130', 'Sage Glas', 'ACME Model A123 (EPD-2025-001)'.\n"
            "• industry_specific → Sector/association dataset or collective of multiple producers.\n"
            "  Examples: 'European Cement Association sector EPD', 'Aluminium association average', 'Timber consortium EPD'.\n"
            "• category_specific → Specific material category without a manufacturer; market/national/regional averages.\n"
            "  Examples: 'OSB', 'XPS', 'Gypsum Fiber Board', 'Brettschichtholz'.\n"
            "• generic → Too vague or template-like, representing broad material or component category.\n"
            "  Examples: 'wood', 'concrete', 'insulation', 'steel', 'flooring'.\n"
        ),
        examples=["product_specific", "category_specific", "generic"]
    )
    manufacturer: Optional[str] = Field(
        None,
        description="Manufacturer/brand name if explicitly provided.",
        examples=["ACME Concrete Ltd."]
    )

    @field_validator("element_name", "description", "component_type", "object_type", "manufacturer", mode="before")
    @classmethod
    def _strip_strings(cls, v: Any):
        if isinstance(v, str):
            v = v.strip()
            return v or None
        return v

    @field_validator("loadbearing", mode="before")
    @classmethod
    def _normalize_loadbearing(cls, v: Any):
        if v is None:
            return YesNoEither.unknown
        if isinstance(v, YesNoEither):
            return v
        s = str(v).strip().lower()
        if s in {"yes", "true", "y", "1", "structural", "load-bearing", "loadbearing"}:
            return YesNoEither.yes
        if s in {"no", "false", "n", "0", "non-structural", "nonstructural", "not load-bearing"}:
            return YesNoEither.no
        if s in {
            "either",
            "both",
            "variable",
            "depends",
            "sometimes",
            "mixed",
            "contextual",
            "maybe",
        }:
            return YesNoEither.either
        return YesNoEither.unknown

    @field_validator("interior", mode="before")
    @classmethod
    def _normalize_interior(cls, v: Any) -> YesNoEither:
        if v is None:
            return YesNoEither.unknown
        if isinstance(v, YesNoEither):
            return v
        s = str(v).strip().lower()
        if s in {"yes", "true", "y", "1", "interior", "inside", "indoor"}:
            return YesNoEither.yes
        if s in {"no", "false", "n", "0", "exterior", "outside", "outdoor", "façade", "facade"}:
            return YesNoEither.no
        if s in {"either", "both", "variable", "mixed", "contextual"}:
            return YesNoEither.either
        return YesNoEither.unknown

    @field_validator("data_resolution", mode="before")
    @classmethod
    def _normalize_data_resolution(cls, v: Any) -> DataResolution:
        if v is None:
            return DataResolution.generic
        if isinstance(v, DataResolution):
            return v
        s = str(v).strip().lower()
        s = re.sub(r"[\s\-_]+", " ", s)
        if any(k in s for k in ["site specific", "single site", "plant", "production site", "factory"]):
            return DataResolution.site_specific
        if any(k in s for k in ["product specific", "manufacturer specific", "vendor specific", "brand"]):
            return DataResolution.product_specific
        if any(k in s for k in ["industry", "association", "sector", "collective", "consortium"]):
            return DataResolution.industry_specific
        if any(k in s for k in ["category", "market average", "national average", "regional average", "representative"]):
            return DataResolution.category_specific
        if any(k in s for k in ["generic", "template", "placeholder", "unspecific", "sample epd"]):
            return DataResolution.generic
        return DataResolution.generic
    
    @field_validator("density", mode="before")
    @classmethod
    def _normalize_density(cls, v: Any) -> Optional[float]:
        """
        Normalize density values:
        - Accept numbers directly (int/float)
        - Accept strings with units like '2400 kg/m3', '1,200 kg/m³'
        - Strip commas, whitespace, and unit text
        - Return float or None
        """
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)

        s = str(v).strip().lower()
        if not s:
            return None

        # Remove thousands separators
        s = s.replace(",", "")
        # Remove unit labels
        s = re.sub(r"\s*(kg\s*/?\s*m\^?3|kg\s*per\s*m3|kg/m³)\s*", "", s)

        try:
            return float(s)
        except ValueError:
            return None
