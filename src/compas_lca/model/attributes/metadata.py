from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from compas_lca.validators import DensityFloat
from compas_lca.validators import StrippedStr
from compas_lca.validators import LoadbearingType
from compas_lca.validators import InteriorExteriorType
from compas_lca.validators import DataResolutionType
from compas_lca.validators import UValueFloat
from compas_lca.validators import LambdaFloat

from compas_lca.enums import Loadbearing
from compas_lca.enums import InteriorExterior
from compas_lca.enums import DataResolution

class Metadata(BaseModel):
    """Source-agnostic Metadata attributes for LCA database mapping."""
    element_name: str = Field(
        ...,
        description="Exact element name as found in the raw building element data.",
        examples=["Wall W-23", "Type: C30/37 Concrete Wall"]
    )
    description: StrippedStr = Field(
        None,
        description="Short one-sentence description of the element using only information present in the source text.",
        examples=["Cast-in-place concrete wall for core enclosure."]
    )
    element_type: StrippedStr = Field(
        None,
        description=(
            "Generic element type if explicitly indicated (e.g., 'slab', 'wall', 'roof', 'window', "
            "'column', 'beam', 'foundation')."
        ),
        examples=["wall", "slab"]
    )
    object_type: StrippedStr = Field(
        None,
        description=(
            "Element's object or layer type label if present (e.g., 'ObjectType', 'Type Name', 'Layer'). "
            "Use the text verbatim from the source."
        ),
        examples=["Structural - Concrete", "Type A-200"]
    )
    classification: StrippedStr = Field(
        None,
        description=(
            "Verbatim transcription of any official classification system reference if present. "
            "Copy exactly as in the source text."
        ),
        examples=['OmniClass 21-02 10 20', 'UniClass Ss_20_10_25']
    )
    loadbearing: LoadbearingType = Field(
        Loadbearing.unknown,
        description=(
            "Whether the element is load-bearing.\n"
            "- yes → explicitly load-bearing.\n"
            "- no → explicitly not load-bearing.\n"
            "- either → this element type can appear as both structural and non-structural variants; context-dependent.\n"
            "- unknown → not specified."
        ),
        examples=["yes", "either"]
    )
    placement: InteriorExteriorType = Field(
        InteriorExterior.unknown,
        description=(
            "Whether the element is specified for interior use.\n"
            "- interior → explicitly interior.\n"
            "- exterior → explicitly exterior.\n"
            "- either → this element can theoretically be interior or exterior, context-dependent.\n"
            "- unknown → unclear if it is interior, exterior, or either, and nothing specified in data."
        ),
        examples=["yes", "either", "unknown"]
    )
    lambda_value: LambdaFloat = Field(
        None,
        ge=0,
        description="Thermal conductivity (lambda) in W/mK. Only set if explicitly present.",
        examples=[0.035],
    )
    u_value: UValueFloat = Field(
        None,
        ge=0,
        description="Thermal transmittance in W/m²K. Only set if explicitly present.",
        examples=[0.24]
    )
    density: DensityFloat = Field(
        None,
        ge=0,
        description="Material density in kilograms per cubic metre (kg/m³).",
        examples=[2400.0, 120.5]
    )
    density_unit: StrippedStr = Field(
        None, 
        description="Material density unit."
        )
    data_resolution: DataResolutionType = Field(
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
    manufacturer: StrippedStr = Field(
        None,
        description="Manufacturer/brand name if explicitly provided.",
        examples=["ACME Concrete Ltd."]
    )