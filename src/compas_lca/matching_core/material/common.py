
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import MaterialType
from compas_lca.enums import ApplicationAreas
from compas_lca.enums import FunctionalTypes

from compas_lca.validators import DensityFloat
from compas_lca.validators import ArealDensityFloat
from compas_lca.validators import MaterialTypeValidated

class MaterialCommon(BaseModel):
    """Shared fields for all types for all materials (regardless of facet)"""
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
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
    density: Optional[DensityFloat] = Field(
        None,
        ge=0,
        description="""
        The volumetric density of the material, expressed in kilograms per cubic metre (kg/m³).
        If the source dataset specifies a range, compute and assign the average value.
        """,
        examples=[24.0, 350.8, 2850.0]
    )
    areal_density: Optional[ArealDensityFloat] = Field(
        None,
        ge=0,
        description="""
        The numeric value of the areal (surface) density of the material, expressed in kilograms per square metre (kg/m²).
        Use this for materials where mass is reported per area.
        If the source dataset specifies a range, compute and assign the average value.
        """,
        examples=[0.85, 12.0]
    )