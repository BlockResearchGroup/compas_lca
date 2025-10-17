from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import Loadbearing
from compas_lca.enums import InteriorExterior
from compas_lca.enums import ComponentType

from compas_lca.validators import LoadbearingType
from compas_lca.validators import InteriorExteriorType
from compas_lca.validators import ThicknessFloat
from compas_lca.validators import UValueFloat


class ComponentCommon(BaseModel):
    """Shared fields for all types of construction components (pre-assembled elements with multiple materials)"""

    # BaseModel configuration
    model_config = ConfigDict(
        extra = "forbid",           # Forbid extra fields
        validate_assignment=True,   # Validate fields on assignment
        str_strip_whitespace=True   # Strips leading and trailing whitespace for str types
    )

    # Fields for all construction materials
    component_name: str = Field(
        ...,
        description="""
        Exact name of the component or element as found in the data
        """,
        examples=[
            "VELUX wooden roof window", 
            "Tür Forster Unico:Ausstattung Sage Glas",
            "HVAC System by Bosch"
            ]
    )
    component_type: ComponentType = Field(
        ComponentType.unknown,
        description="""
        Overview of component types, yet to be defined more in detail
        """,
        examples=["window", "roof", "building_system"]
    )
    loadbearing: LoadbearingType = Field(
        Loadbearing.unknown,
        description="""
        If the component is explicitly intended or unintended for loadbearing elements or components
        If the dataset explicitly states that it can be used for both, assign 'either'
        If there is no available information, and an answer can not be precisely inferred, assign 'unknown'
        """,
        examples=["loadbearing", "non_loadbearing", "unknown"]
    )
    placement: InteriorExteriorType = Field(
        InteriorExterior.unknown,
        description="""
        If the component is explicitly intended for exterior or interior use
        If the dataset explicitly states that it can be used for both, assign 'either'
        If there is no available information, and an answer can not be precisely inferred, assign 'unknown'
        """,
        examples=["interior", "exterior", "either", "unknown"]
    )
    manufacturer: Optional[str] = Field(
        None,
        description="""
        The manufacturer or brand name, taken verbatim from the source dataset if available.
        If no manufacturer is specified, leave this field as null (None).
        Careful: do not mistake the "owner of the dataset" with the manufacturer, they are not always the same
        """,
        examples=["Knauf", "Holcim", "EcoWorx"]
    )
    provenance: Optional[str] = Field(
        None,
        description="""
        A regional or country code indicating the geographic provenance or data scope of the component.
        Examples include ISO country codes (e.g., "DE" for Germany, "CH" for Switzerland)
        or broader regional groupings (e.g., "EU-27", "GLO" for global).
        If no provenance is specified in the dataset, leave this field as null (None).
        """,
        examples=["GB", "TW", "GLO", "DE", "CH", "EU-27"]
    )
    production_location: Optional[str] = Field(
        None,
        description="""
        The exact place/city/area of the plant or factory where the component was produced.
        If this is not explicitly stated in the dataset, leave this field as null (None)
        """,
        examples=["Rüdersdorf", "Jerez de la Frontera", "Bulacan"]
    )
    thickness: ThicknessFloat = Field(
        None,
        ge=0,
        description="""
        The numeric value of the thickness (in milimeters) of the component dataset.
        If the source dataset specifies a range, compute and assign the average value.
        """,
        examples=[0.5, 5.0, 18.0]
    )
    u_value: UValueFloat = Field(
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
        This boolean value describes if the component is fire retardant (True) or inflammable (False)
        Assign a boolean value if this information is explicitly stated in the input dataset,
        or if the value unambiguously clear (common sense).
        """,
        examples=[True, False]
    )
    water_vapour_resistant: Optional[bool] = Field(
        None,
        description="""
        This field describes if the component is ressistant against water vapour (True) or very permeable (False)
        Assign a boolean value if this information is explicitly stated in the input dataset,
        or if the value unambiguously clear (common sense).
        """,
        examples=[True, False]
    )