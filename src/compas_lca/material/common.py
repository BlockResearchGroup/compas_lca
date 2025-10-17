from typing import Optional
from typing import List

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import MaterialType
from compas_lca.enums import ApplicationAreas
from compas_lca.enums import FunctionalTypes
from compas_lca.enums import Loadbearing
from compas_lca.enums import InteriorExterior

from compas_lca.validators import DensityFloat
from compas_lca.validators import ArealDensityFloat
from compas_lca.validators import LoadbearingType
from compas_lca.validators import InteriorExteriorType
from compas_lca.validators import MaterialTypeValidated
from compas_lca.validators import ThicknessFloat
from compas_lca.validators import UValueFloat
from compas_lca.validators import LambdaFloat


class MaterialCommon(BaseModel):
    """Shared fields for all types for all materials (regardless of facet)"""

    # BaseModel configuration
    model_config = ConfigDict(
        extra = "forbid",           # Forbid extra fields
        validate_assignment=True,   # Validate fields on assignment
        str_strip_whitespace=True   # Strips leading and trailing whitespace for str types
    )

    # Fields for output schema enforced by LLM
    name: str = Field(
        ...,
        description="""
        Exact material name as found in the raw dataset.
        Extract the name verbatim.
        """,
        examples=[
            "Polyethylene foam", 
            "C30/37 Concrete",
            "Gypsum stone (CaSO4-Dihydrate)",
            "Brettschichtholz C24"
            ]
    )
    material_type: MaterialTypeValidated = Field(
        MaterialType.unknown,
        description="""
        The broader material classification indicating the dominant material composition or origin.
        Choose the option that best describes the material's main substance or structural base,
        according to the following rules:
        • 'mineral' → Inorganic, nonmetallic, geological or ceramic-based materials 
        (excluding concrete and cement-based composites).
        e.g., brick, tile, glass, stone, gypsum, ceramics, rammed earth.
        • 'concrete' → Cementitious and aggregate-based materials or products primarily composed of
        hydraulic binders.
        e.g., concrete, reinforced concrete, lightweight concrete, mortar, grout.
        • 'ligneous' → Organic materials derived from wood or other lignocellulosic biomass.
        e.g., timber, plywood, MDF, OSB, bamboo, cork, straw-based panels.
        • 'metallic' → Metallic materials and alloys.
        e.g., steel, stainless steel, aluminum, copper, zinc, lead.
        • 'polymeric' → Synthetic organic polymer materials.
        e.g., plastics, rubbers, resins, foams (not classified as insulation).
        • 'bituminous' → Hydrocarbon-based binders or composites.
        e.g., asphalt, bitumen, tar, bituminous membranes.
        • 'composite' → Engineered combinations of two or more material types.
        choose 'composite' if unclear between dominant materials, and do not assign 'either'.
        If uncertain or the information is insufficient, assign 'unknown'.
        """,
        examples=[
            "mineral", "concrete", "ligneous", "metallic", 
            "polymeric", "bituminous", "composite"
        ]
    )
    functional_types: List[FunctionalTypes] = Field(
        [FunctionalTypes.unknown],
        description="""
        List of the product's intended functional roles (i.e., function or function-related layer type)
        as explicitly declared in the input dataset.

        Rules:
        - Choose one single best PRIMARY intent whenever possible.
        - Add additional values ONLY if the material/product explicitly serves multiple 
        primary functions simultaneously (e.g., “thermal + acoustic insulation” panel).
        - If the role is not clearly stated in the raw data, keep “unknown”.
        """,
        examples=[
            ["structural"],
            ["thermal_insulation", "acoustic_insulation"],
            ["covering", "lining"],
            ["membrane", "waterproofing"]
        ]
    )
    application_areas: List[ApplicationAreas] = Field(
        [ApplicationAreas.unknown],
        description="""
        List of all explicitly stated application areas of a building (e.g., walls, floors, roofs). 
        This field allows multiple values if the material is applicable to several component types. 
        Only assign application areas that are explicitly stated in the raw data, or unambiguously
        common sense (e.g., ready-mixed concrete can be used for slabs, walls, columns, etc.)
        """,
        examples=[
            ["balcony", "railing"],
            ["wall", "slab", "column"],
            ["floor", "ceiling"]
        ]
    )
    density: DensityFloat = Field(
        None,
        ge=0,
        description="""
        The volumetric density of the material, expressed in kilograms per cubic metre (kg/m³).
        If the source dataset specifies a range, compute and assign the average value.
        """,
        examples=[24.0, 350.8, 2850.0]
    )
    areal_density: ArealDensityFloat = Field(
        None,
        ge=0,
        description="""
        The numeric value of the areal (surface) density of the material, expressed in kilograms per square metre (kg/m²).
        Use this for materials where mass is reported per area.
        If the source dataset specifies a range, compute and assign the average value.
        """,
        examples=[0.85, 12.0]
    )
    loadbearing: LoadbearingType = Field(
        Loadbearing.unknown,
        description="""
        If the material is explicitly intended or unintended for loadbearing elements or components
        If the dataset explicitly states that it can be used for both, assign 'either'
        If there is no available information, and an answer can not be precisely inferred, assign 'unknown'
        """,
        examples=["loadbearing", "non_loadbearing", "unknown"]
    )
    placement: InteriorExteriorType = Field(
        InteriorExterior.unknown,
        description="""
        If the material is explicitly intended for exterior or interior use
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
        A regional or country code indicating the geographic provenance or data scope of the material.
        Examples include ISO country codes (e.g., "DE" for Germany, "CH" for Switzerland)
        or broader regional groupings (e.g., "EU-27", "GLO" for global).
        If no provenance is specified in the dataset, leave this field as null (None).
        """,
        examples=["GB", "TW", "GLO", "DE", "CH", "EU-27"]
    )
    production_location: Optional[str] = Field(
        None,
        description="""
        The exact place/city/area of the plant or factory where the material was produced.
        If this is not explicitly stated in the dataset, leave this field as null (None)
        """,
        examples=["Rüdersdorf", "Jerez de la Frontera", "Bulacan"]
    )
    thickness: ThicknessFloat = Field(
        None,
        ge=0,
        description="""
        The numeric value of the thickness (in milimeters) of the material dataset.
        If the source dataset specifies a range, compute and assign the average value.
        """,
        examples=[0.5, 5.0, 18.0]
    )
    thermal_conductivity: LambdaFloat = Field(
        None,
        ge=0,
        description="""
        The float value of the thermal conductivity (lambda) of the material in W/mk.
        If the source dataset specifies a range, compute and assign the average value.
        """,
        examples=[0.3, 1.4, 2.0]
    )
    u_value: UValueFloat = Field(
        None,
        ge=0,
        description="""
        The float value of the U-Value of the material in W/m^2K.
        If the source dataset specifies a range, compute and assign the average value.
        """,
        examples=[0.5, 1.1, 1.4]
    )
    fire_retardant: Optional[bool] = Field(
        None,
        description="""
        This boolean value describes if the material is fire retardant (True) or inflammable (False)
        Assign a boolean value if this information is explicitly stated in the input dataset,
        or if the value unambiguously clear (common sense).
        """,
        examples=[True, False]
    )
    water_vapour_resistant: Optional[bool] = Field(
        None,
        description="""
        This field describes if the material is ressistant against water vapour (True) or very permeable (False)
        Assign a boolean value if this information is explicitly stated in the input dataset,
        or if the value unambiguously clear (common sense).
        """,
        examples=[True, False]
    )