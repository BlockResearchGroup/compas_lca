from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from compas_lca.validators import DensityFloat
from compas_lca.validators import LambdaFloat
from compas_lca.validators import UValueFloat
from compas_lca.validators import ThicknessFloat
from compas_lca.validators import StrippedStr
from compas_lca.validators import LoadbearingType
from compas_lca.validators import InteriorExteriorType
from compas_lca.validators import DataResolutionType

from compas_lca.enums import Loadbearing
from compas_lca.enums import InteriorExterior
from compas_lca.enums import DataResolution

class InventoryItemEPD(BaseModel):
    """
    ILCD+EPD data format fields, which can be directly extracted from CSVs or EPDs
    These fields (ONLY IN THE OEKOBAUDAT CASE) do not require LLM-based inferences.
    Problem here is that it is not generalizable, only valid for the specific OBD CSV file
    Perhaps everything should be extracted by the LLM, and a new UUID should be created regardless
    That's why validators are preemptively included (to normalize LLM output, just to be 100% sure)
    """

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
    category: StrippedStr = Field(
        None, 
        description="Category chain in the database",
        examples=["Metals/Aluminium/Cast aluminium"]
        )
    provencance: StrippedStr = Field(
        None, 
        description="ISO 3166 country/region code",
        examples=["DE", "RER"]
        )
    dataset_type: StrippedStr = Field(
        None, 
        description="type of data regarding representativeness, e.g. 'generic dataset', 'specific dataset'",
        examples=["generic dataset", "specific dataset"]
        )
    dataset_owner: StrippedStr = Field(
        None, 
        description="Person or entity who owns this data set. Note: this is usually not the publisher of the data set.",
        examples=["German Cement Association", "Sphera Solutions GmbH"]
        )
    density_value: DensityFloat = Field(
        None, 
        description="Material density value."
        )
    density_unit: StrippedStr = Field(
        None, 
        description="Material density unit."
        )
    thickness_value: ThicknessFloat = Field(
        None, 
        description="Layer thickness value."
        )
    thickness_unit: StrippedStr = Field(
        None, 
        description="Layer thickness unit."
        )
    reference_unit: StrippedStr = Field(    # probably Enum (piece, length, area, volume, kg)
        None, 
        description="The specified reference unit used for emissions calculation"
        )

class InventoryItemLLM(BaseModel):
    """
    Implicit data from some ILCD+EPD fields which should be inferred from an AI Agent
    These include fields such as 'Technical purpose of product or process', 'General Comments on data set', etc
    The purpose of this class is to identify and extract key information for subsequent LCA database matching
    Some fields are identical to the LcaElement attributes, effectively enabling smart filtering of viable matches
    note: these attributes are not part of the official ILCD+EPD classification schema
    """
    description: StrippedStr = Field(
        None,
        description="Short one-sentence description of the dataset.",
        examples=["Generic concrete material dataset, representing a regional average."]
    )
    element_type: StrippedStr = Field(  # This will probably be an Enum (albeit a large Enum set)
        None,
        description=(
            "If the dataset is typically used for specific building components (e.g., 'slab', 'wall', 'roof', 'foundation', etc.)"
            "While some datasets can be used for multiple components, some can be very specific"
            "List all components that typically use or include the material described in the dataset"
        ),
        examples=["wall", "slab"]
    )
    classification: StrippedStr = Field(
        None,
        description=(
            "Verbatim transcription of any official classification system reference if present. "
            "Copied exactly as in the source text, else null, if none provided."
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
        description="Manufacturer/brand name if explicitly provided. If not present, use null.",
        examples=["ACME Concrete Ltd."]
    )
    functional_constraints: StrippedStr = Field(
        None,
        description=(
        "Determine if the material described in the dataset is intended for a specific functional use case(es)."
        "Include a very brief description of any functional constraints the material or component might have"
        ),
        examples=["This material should only be used for laboratory and hospital typologies."]
    )

class InventoryItem(InventoryItemEPD, InventoryItemLLM):
    """
    Final merged representation of an inventory item.
    The InventoryItem class might be the only class from the get-go (without stiching together).
    Because for now, the workflow extracts some datasets from the OBD CSV (hard-coded)
    and other datasets from the HTML scrapes (Agent-based), and are glued together in this final class.
    If we want to be as generalizable as possible, probably we should not include the CSV extraction
    and instead extract every field with an Agent.
    """

    # TO-DO:
    # requires updated validators (from validators.py)
    # requires default value (from enums.py)
    # will be included once workflow fully defined (all agent-based vs partially hardcoded)

    # InventoryItemEPD
    uuid: str
    dataset_name: str
    category: Optional[str] = None
    provenance: Optional[str] = None
    dataset_type: Optional[str] = None
    dataset_owner: Optional[str] = None
    density_value: Optional[float] = None
    density_unit: Optional[str] = None
    thickness_value: Optional[float] = None
    thickness_unit: Optional[str] = None
    reference_unit: Optional[str] = None

    # InventoryItemLLM
    description: Optional[str] = None
    element_type: Optional[str] = None
    classification: Optional[str] = None
    loadbearing: Optional[str] = None
    placement: Optional[str] = None
    lambda_value: Optional[float] = None
    u_value: Optional[float] = None
    data_resolution: Optional[DataResolution] = None
    manufacturer: Optional[str] = None
    functional_constraints: Optional[str] = None

    @classmethod
    def from_parts(cls, csv_part: InventoryItemEPD, llm_part: InventoryItemLLM) -> "InventoryItem":
        """Merge CSV + LLM parts into one final object."""
        data = csv_part.model_dump()
        data.update(llm_part.model_dump(exclude_unset=True))
        return cls(**data)

