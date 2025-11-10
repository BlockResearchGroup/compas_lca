from typing import Optional
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import EntryType

from compas_lca.validators import LoadbearingType
from compas_lca.validators import InteriorExteriorType
from compas_lca.validators import ThicknessFloat
from compas_lca.validators import UValueFloat
from compas_lca.validators import LambdaFloat

class Common(BaseModel):
    """Shared fields for all types for all materials or components"""
    model_config = ConfigDict(
        extra = "forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    entry_type: EntryType = Field(
        ...,
        description="""
        Classify the dataset as a MATERIAL (homogeneous substance, monolithic unit, or uniform layer), 
        COMPONENT (assembled product or system-level element), 
        or UNKNOWN if insufficient evidence.
        """,
        examples=[
            "material",
            "component",
            "unknown"
            ]
    )
    name: str = Field(
        ...,
        description="""
        Exact material OR component name as found in the raw dataset.
        Depending on if the dataset describes materials or components,
        extract the material or component/element name verbatim.
        """,
        examples=[
            "Polyethylene foam", 
            "C30/37 Concrete",
            "Gypsum stone (CaSO4-Dihydrate)",
            "Brettschichtholz C24",
            "VELUX wooden roof window", 
            "Tür Forster Unico:Ausstattung Sage Glas",
            "HVAC System by Bosch"
            ]
    )
    loadbearing: Optional[LoadbearingType] = Field(
        None,
        description="""
        If the material or component is explicitly intended or unintended for loadbearing/structural use cases.
        If the dataset explicitly states that it can be used for both, assign 'either'.
        If there is no available information, and an answer can not be precisely inferred, leave empty.
        """,
        examples=["loadbearing", "non_loadbearing", "either"]
    )
    placement: Optional[InteriorExteriorType] = Field(
        None,
        description="""
        If the material or component is explicitly intended for exterior or interior use.
        If the dataset explicitly states that it can be used for both, assign 'either'.
        If there is no available information, and an answer can not be precisely inferred, leave empty.
        """,
        examples=["interior", "exterior", "either", "unknown"]
    )
    manufacturer: Optional[str] = Field(
        None,
        description="""
        The manufacturer or brand name, taken verbatim from the source dataset if available.
        If no manufacturer is specified, leave this field as null (None).
        Careful: do not mistake the "owner of the dataset" with the manufacturer, they are not always the same.
        """,
        examples=["Knauf", "Holcim", "EcoWorx"]
    )
    provenance: Optional[str] = Field(
        None,
        description="""
        A regional or country code indicating the geographic provenance or data scope of the material/component.
        Examples include ISO country codes (e.g., "DE" for Germany, "CH" for Switzerland)
        or broader regional groupings (e.g., "EU-27", "GLO" for global).
        If no provenance is specified in the dataset, leave this field as null (None).
        """,
        examples=["GB", "TW", "GLO", "DE", "CH", "EU-27"]
    )
    production_location: Optional[str] = Field(
        None,
        description="""
        The exact place/city/area of the plant or factory where the material or component was produced.
        If this is not explicitly stated in the dataset, leave this field as null (None).
        """,
        examples=["Rüdersdorf", "Jerez de la Frontera", "Bulacan"]
    )
    thickness: Optional[ThicknessFloat] = Field(
        None,
        ge=0,
        description="""
        The numeric value of the thickness (in milimeters) of the material or component dataset.
        If the source dataset specifies a range, compute and assign the average value.
        """,
        examples=[0.5, 5.0, 18.0]
    )
    thickness_source: Literal["from_data", "speculated"] = Field( #TRACABILITY
        "from_data",
        description="""
        Always leave default "from_data".
        """
    )
    thermal_conductivity: Optional[LambdaFloat] = Field(
        None,
        ge=0,
        description="""
        The float value of the thermal conductivity (lambda) of the material or component in W/mk.
        If the source dataset specifies a range, compute and assign the average value.
        """,
        examples=[0.3, 1.4, 2.0]
    )
    u_value: Optional[UValueFloat] = Field(
        None,
        ge=0,
        description="""
        The float value of the U-Value of the component in W/m^2K.
        If the source dataset specifies a range, compute and assign the average value.
        """,
        examples=[0.5, 1.1, 1.4]
    )
    fire_retardant: Optional[bool] = Field(
        None,
        description="""
        This boolean value describes if the material or component is fire retardant (True) or inflammable (False)
        Assign a boolean value if this information is explicitly stated in the input dataset,
        or if the value is unambiguously clear (common sense).
        """,
        examples=[True, False]
    )
    water_vapour_resistant: Optional[bool] = Field(
        None,
        description="""
        This field describes if the material or component is resistant against water vapour (True) or very permeable (False).
        Assign a boolean value if this information is explicitly stated in the input dataset,
        or if the value is unambiguously clear (common sense).
        """,
        examples=[True, False]
    )