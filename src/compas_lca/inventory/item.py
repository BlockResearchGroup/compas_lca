from __future__ import annotations

import re

from typing import Any
from typing import Optional
from typing import ClassVar
from typing import Tuple

from compas_lca.enum import YesNoEither
from compas_lca.enum import DataResolution

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator


class FloatParsingMixin:
    """mixin to normalize float-like fields across models."""
    FLOAT_FIELDS: ClassVar[Tuple[str, ...]] = ()

    @staticmethod
    def parse_float(v: Any) -> float | None:
        if v is None or v == "":
            return None
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).strip().replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None

    @model_validator(mode="before")
    @classmethod
    def _normalize_float_fields(cls, data: Any):
        if not isinstance(data, dict) or not getattr(cls, "FLOAT_FIELDS", ()):
            return data
        d = dict(data)
        for field in cls.FLOAT_FIELDS:
            if field in d:
                d[field] = cls.parse_float(d[field])
        return d


class InventoryItemEPD(BaseModel):
    """ILCD+EPD data format fields, which can be directly extracted from CSVs or EPDs
    These fields (in most cases) do not require LLM-based inferences.
    """

    # mixin normalizes chosen fields (this is a shared function now):
    FLOAT_FIELDS: ClassVar[tuple[str, ...]] = ("density_value", "thickness_value")

    uuid: str = Field(
        ..., 
        description="Unique ID of the dataset.",
        examples=["be06a50c-9a4a-4af7-837d-abc46d0d3da9"]
        )
    dataset_name: str = Field(
        ..., 
        description="Dataset name as given in ILCD+EPD.",
        examples=["MACMAT R Steel (Steel wire mesh reinforced geomat, Officine Maccaferri S.p.A.)"]
        )
    category: Optional[str] = Field(
        None, 
        description="Category chain in the database",
        examples=["Metals/Aluminium/Cast aluminium"]
        )
    location_code: Optional[str] = Field( # Maybe ENUM?
        None, 
        description="ISO 3166 country/region code",
        examples=["DE", "RER"]
        )
    dataset_type: Optional[str] = Field(
        None, 
        description="type of data regarding representativeness, e.g. 'generic dataset', 'specific dataset'",
        examples=["generic dataset", "specific dataset"]
        )
    dataset_owner: Optional[str] = Field(
        None, 
        description="Person or entity who owns this data set. Note: this is usually not the publisher of the data set.",
        examples=["German Cement Association", "Sphera Solutions GmbH"]
        )
    density_value: Optional[float] = Field(
        None, 
        description="Material density value."
        )
    density_unit: Optional[str] = Field(
        None, 
        description="Material density unit."
        )
    thickness_value: Optional[float] = Field(
        None, 
        description="Layer thickness value."
        )
    thickness_unit: Optional[str] = Field(
        None, 
        description="Layer thickness unit."
        )

class InventoryItemLLM(BaseModel):
    """
    Implicit data from some ILCD+EPD fields which should be inferred from an AI Agent
    These include fields such as 'Technical purpose of product or process', 'General Comments on data set', etc
    The purpose of this class is to identify and extract key information for subsequent LCA database matching
    Some fields are identical to the LcaElement attributes, effectively enabling smart filtering of viable matches
    note: these attributes are not part of the official ILCD+EPD classification schema
    """
    description: Optional[str] = Field(
        None,
        description="Short one-sentence description of the dataset.",
        examples=["Generic concrete material dataset, representing a regional average."]
    )
    component_use: Optional[str] = Field(
        None,
        description=(
            "If the dataset is typically used for specific building components (e.g., 'slab', 'wall', 'roof', 'foundation', etc.)"
            "While some datasets can be used for multiple components, some can be very specific"
            "List all components that typically use or include the material described in the dataset"
        ),
        examples=["wall", "slab"]
    )
    classification: Optional[str] = Field(
        None,
        description=(
            "Verbatim transcription of any official classification system reference if present. "
            "Copied exactly as in the source text, else null, if none provided."
        ),
        examples=['OmniClass 21-02 10 20', 'UniClass Ss_20_10_25']
    )
    loadbearing: YesNoEither = Field(
        YesNoEither.unknown,
        description=(
            "Whether the material/component described in the dataset is load-bearing.\n"
            "- yes → explicitly load-bearing.\n"
            "- no → explicitly not load-bearing.\n"
            "- either → it can appear as both structural and non-structural variants; context-dependent.\n"
            "- unknown → not specified."
        ),
        examples=["yes", "either"]
    )
    interior: YesNoEither = Field(
        YesNoEither.unknown,
        description=(
            "Whether the material/component described in the dataset is specified for interior use.\n"
            "- yes → explicitly interior.\n"
            "- no → explicitly exterior.\n"
            "- either → this dataset's material/component can theoretically be interior or exterior, context-dependent.\n"
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
    data_resolution: DataResolution = Field(
        DataResolution.generic,
        description=(
            "Choose EXACTLY ONE resolution level. Start at the most specific and stop at the first match:\n"
            "• site_specific → Single manufacturer AND single production site/plant.\n"
            "  Examples: 'ACME Insulation – Plant Y', 'Factory Linz – Line 2', 'BrandX Concrete, Plant 17'.\n"
            "• product_specific → Single manufacturer/brand (optionally model/SKU/EPD ID).\n"
            "  Examples: 'Forster Variotherm – 60 x 130', 'Sage Glas', 'ACME Model A123 (EPD-2025-001)'.\n"
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
        description="Manufacturer/brand name if explicitly provided. If not present, use null.",
        examples=["ACME Concrete Ltd."]
    )
    functional_constraints: Optional[str] = Field(
        None,
        description=(
        "Determine if the material described in the dataset is intended for a specific functional use case(es)."
        "Include a very brief description of any functional constraints the material or component might have"
        ),
        examples=["This material should only be used for laboratory and hospital typologies."]
    )


    @field_validator("description", "component_use", "classification", "manufacturer", mode="before")
    @classmethod
    def _strip_strings(cls, v: Any) -> Optional[str]:
        if isinstance(v, str):
            v = v.strip()
            return v or None
        return v

    @field_validator("u_value", mode="before")
    @classmethod
    def _normalize_u_value(cls, v: Any) -> Optional[float]:
        """Accept plain numbers or strings with units like '0.24 W/m²K'."""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).strip().lower()
        s = s.replace(",", ".")
        # remove common unit text
        s = re.sub(r"\s*w/?m[²2]k", "", s)
        try:
            return float(s)
        except ValueError:
            return None

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



class InventoryItem(InventoryItemEPD, InventoryItemLLM):
    """Final merged representation of an inventory item."""
    # include all fields from both
    uuid: str
    name: str
    category: Optional[str] = None
    reference_unit: Optional[str] = None
    source: Optional[str] = None
    data_resolution: Optional[DataResolution] = None
    density: Optional[float] = None
    description: Optional[str] = None
    manufacturer: Optional[str] = None

    @classmethod
    def from_parts(cls, csv_part: InventoryItemEPD, llm_part: InventoryItemLLM) -> "InventoryItem":
        """Merge CSV + LLM parts into one final object."""
        data = csv_part.dict()
        data.update(llm_part.dict(exclude_unset=True))
        return cls(**data)

