from __future__ import annotations

from typing import Optional

from compas_lca.enums.enums import YesNoEither
from compas_lca.enums.enums import YesNoUnknown
from compas_lca.enums.enums import DataResolution
from compas_lca.enums.enums import MaterialCategories
from compas_lca.enums.enums import Components

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

"""
There could be conditional expansion of matching core, according to the material categories
(e.g. if material_category == "concrete" → require strength_class, if "timber" → require wood_species, if "insulation" → require thermal_conductivity, etc.)
Compare material_categories.json with matching_core_expansion.json
"""

class MatchingCore(BaseModel):
    """
    Core attributes for matching building elements to LCA datasets.
    These are the common denominator attributes along which the inventory solution space can be filtered.
    """
    material_name: Optional[str] = Field(
        None,
        description=(
            "Verbatim name name of the main material or material system of the building element."
            "This is typically a high-level label such as 'concrete', 'brick', 'timber', 'steel', 'glass', 'insulation'."
            "Avoid overly specific trade names or product codes."
            "If the element is a composite, use the dominant material by volume or weight."
        ),
        examples=["Stone mastic asphalt (SMA)", "3-Schicht-Platte", "Gypsum plasterboard", "OSB", "Reinforced concrete", "SwissPor XPS insulation"]
    ),
    material_category: Optional[MaterialCategories] = Field(
        None,
        description=(
            "Broad material category of the main material or material system of the building element."
            "This is used for coarse filtering of LCA datasets."
            "If uncertain, leave as null."
        ),
        examples=["concrete", "masonry", "wood", "metal", "glass", "plastic", "insulation"]
    ),
    component_use: Optional[Components] = Field(
        None,
        description=(
            "Intended functional use of the building element within the building structure."
            "This is either explicitly stated in the source data or can be reasonably inferred."
            "It can either be one "
            "If uncertain, leave as null."
        ),
        examples=["slab", "wall", "roof", "flooring"]
    ),
    manufacturer: Optional[str] = Field(
        None,
        description=(
            "Name of the manufacturer or brand of the building element if explicitly known."
            "This can help in identifying specific product datasets if available."
            "If unknown, leave as null."
        ),
        examples=["Lafarge", "Kingspan", "Velux"]
    ),
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
    ),
    interior: YesNoEither = Field(
        YesNoEither.unknown,
        description=(
            "Whether the element is specified for interior use.\n"
            "- yes → explicitly interior.\n"
            "- no → explicitly exterior.\n"
            "- either → this element can theoretically be interior or exterior, context-dependent.\n"
            "- unknown → not specified."
        ),
        examples=["yes", "either"]
    ),
    composite: YesNoUnknown = Field(
        YesNoUnknown.unknown,
        description=(
            "Whether the element is a composite of multiple distinct materials.\n"
            "- yes → clearly combines distinct materials that each require separate datasets (e.g., 'concrete' with loadbearing specification → concrete + rebar steel composite; 'metal stud cavity' → steel + air/insulation composite).\n"
            "- no → maps to a single LCA dataset even if internally a mixture (e.g., 'timber', 'brick', 'XPS insulation').\n"
            "- unknown → not specified."
        ),
        examples=["yes", "no"]
    ),
    density: Optional[float] = Field(
        None,
        description=(
            "Density of the main material or material system of the building element in kg/m³."
            "This can help in selecting more accurate LCA datasets that match the physical properties of the material."
            "If unknown, leave as null."
        ),
        examples=[2400, 1800, 600]
    ),
    classification: Optional[str] = Field(
        None,
        description=(
            "Official classification code or standard reference for the building element if available."
            "This can help in precisely identifying the type and specifications of the element."
            "If unknown, leave as null."
        ),
        examples=["OmniClass 21-02 10 20", "UniClass Ss_20_10_25"]
    ),
    thermal_conductivity: Optional[float] = Field(
        None,
        ge=0,
        description=(
            "Thermal or heat conductivity of the material in W/mK if explicitly specified."
            "This can help in identifying elements with specific thermal performance requirements."
            "If unknown or not applicable, leave as null."
        ),
        examples=[0.24, 0.35]
    ),
    thickness: Optional[float] = Field(
        None,
        ge=0,
        description=(
            "Nominal thickness of the building element in millimetres (mm) if explicitly specified."
            "This can help in distinguishing between different variants of the same material or component type."
            "If unknown or not applicable, leave as null."
        ),
        examples=[200, 300, 50]
    ),
    provenance: Optional[str] = Field(
        None,
        description=(
            "Geographical origin of the main material or material system of the building element if known."
            "This can help in selecting region-specific LCA datasets that account for local production impacts."
            "If unknown, leave as null."
        ),
        examples=["DE", "RER", "EU", "NA","RO", "Singapore"]
    ),
    additional_constraints: Optional[str] = Field(
        None,
        description=(
            "Free-text description of the building element to capture any additional relevant details not covered by other fields."
            "This can include specific product features (such as cement mixes, strength classes), special treatments, or contextual information that may aid precisely describing the material properties."
            "If no additional details, leave as null."
        ),
        examples=["Cast-in-place concrete wall for core enclosure.", "Cement type CEM III/A 42.5N", "Reinforced concrete with B500B rebar"]
    ),
    data_resolution: DataResolution = Field(
        DataResolution.unknown,
        description=(
            "Level of specificity of the available data for the building element.\n"
            "- generic → very broad, non-specific data (e.g., 'concrete', 'brick', 'timber').\n"
            "- category_specific → data specific to a product/type family but no manufacturer (e.g., 'autoclaved aerated concrete blocks', 'facing brick').\n"
            "- industry_specific → data representative of an industry sector or multi-manufacturer average (e.g., association/sector representative).\n"
            "- product_specific → data for a single manufacturer/brand (optionally model/line) but no specific production site (e.g., 'Lafarge Beton C30/37').\n"
            "- site_specific → highly specific data for a single manufacturer AND single production site (e.g., 'Lafarge Beton C30/37 from Berlin plant')."
        ),
        examples=["generic", "category_specific", "industry_specific", "product_specific", "site_specific"]
    )
    pass