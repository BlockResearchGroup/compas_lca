
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
        Classify the product by its dominant base material (composition), not shape, coating, or process.
        Choose exactly one of: 'mineral', 'concrete', 'wood', 'metallic', 'polymeric', 'bituminous', 'composite', 'unknown'.

        Decision rules (apply top-down):

        1) wood → Organic, lignocellulosic wood-based materials.
        Map to 'wood' if the name or description contains ANY of:
        english: wood, timber, lumber, parquet, plywood, veneer, LVL, laminated veneer lumber, glulam,
                    CLT, cross laminated timber, OSB, MDF, HDF, particleboard, chipboard, hardboard,
                    fibreboard/fiberboard, cork, bamboo
        german: Holz, Brettschichtholz, Brettsperrholz, Kreuzlagenholz, Sperrholz, Furnierschichtholz,
                LVL, Leimholz, Mehrschichtparkett, Parkett, Spanplatte, Faserplatte, MDF, HDF, OSB
        examples: Multi-layer parquet, Cross laminated timber (CLT), MDF (uncoated)

        2) concrete → Cementitious / hydraulic binder with aggregates.
        keywords: concrete, reinforced concrete, RC, mortar, grout, UHPC, screed

        3) mineral → Inorganic, nonmetallic, ceramic/stone/glass (excluding concrete).
        keywords: brick, tile, ceramic, porcelain, glass, stone, gypsum, plaster, rammed earth

        4) metallic → Metals and alloys.
        keywords: steel, stainless steel, aluminum, copper, zinc, lead, brass, bronze, cast iron

        5) polymeric → Synthetic organic polymers, plastics, rubbers, resins, foams (non-insulation context).
        keywords: PVC, PE, PP, PET, PUR, PU, EPDM, acrylic, polyester, polyamide, nylon

        6) bituminous → Hydrocarbon binders and composites.
        keywords: asphalt, bitumen, tar, bituminous membrane

        7) composite → Engineered combination where no single base material dominates OR explicitly named composite.
        keywords: FRP, GFRP, CFRP, sandwich panel (if core/skins differ and no dominant base)

        8) unknown → If none of the above can be determined from available text.

        Notes:
        • Ignore surface coatings (laminates, varnish, paint) when determining the base material.
        """,
        examples=["wood", "concrete", "mineral", "metallic", "polymeric", "bituminous", "composite"]
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