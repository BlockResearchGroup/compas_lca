from uuid import uuid4
from uuid import UUID

from typing import Optional
from typing import List
from typing import Annotated
from typing import Union

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field

from compas_lca.material.common import MaterialCommon
from compas_lca.material.bituminous import BituminousFacet
from compas_lca.material.concrete import ConcreteFacet
from compas_lca.material.ligneous import LigneousFacet
from compas_lca.material.metallic import MetallicFacet
from compas_lca.material.mineral import MineralFacet
from compas_lca.material.polymeric import PolymericFacet
from compas_lca.material.composite import CompositeFacet

from compas_lca.enums import ApplicationAreas
from compas_lca.enums import FunctionalTypes
from compas_lca.enums import MaterialType
from compas_lca.enums import Loadbearing
from compas_lca.enums import InteriorExterior

from compas_lca.validators import LoadbearingType
from compas_lca.validators import InteriorExteriorType
from compas_lca.validators import DensityFloat
from compas_lca.validators import ArealDensityFloat
from compas_lca.validators import ManufacturerStr
from compas_lca.validators import ThicknessFloat
from compas_lca.validators import UValueFloat
from compas_lca.validators import LambdaFloat

# discriminators
FacetUnion = Annotated[
    Union[
        BituminousFacet,
        ConcreteFacet,
        LigneousFacet,
        MetallicFacet,
        MineralFacet,
        PolymericFacet,
        CompositeFacet
    ],
    Field(discriminator="material_type")
]


class LcaMaterial(BaseModel):
    """
    LcaMaterial as container for any kind and nested/branched attributes
    This serves as a mixed bag of material, semantic, and functional attributes
    Perhaps somewhat awkward name convention? It does express more than just "Material"
    Is the matching core, and is a shared class for either EPD or building model elements
    """

    # model config (adjustable)
    model_config = ConfigDict(extra = "forbid")

    # create UUID for an LcaMaterial instance
    id: UUID = Field(default_factory=uuid4)

    # ratio (default=1.0, if inferred by dissection, e.g., reinforced concrete, injected by script)
    volumetric_ratio: float = 1.0

    # carry-over shared fields from LcaMaterialCommon
    name: str
    functional_types: List[FunctionalTypes] = [FunctionalTypes.unknown]
    application_areas: List[ApplicationAreas] = [ApplicationAreas.unknown]
    density: DensityFloat = Field(None, ge=0)
    areal_density: ArealDensityFloat = Field(None, ge=0)
    loadbearing: LoadbearingType = Loadbearing.unknown
    placement: InteriorExteriorType = InteriorExterior.unknown
    manufacturer: ManufacturerStr = None
    provenance: Optional[str] = None
    production_location: Optional[str] = None
    thickness: ThicknessFloat = Field(None, ge=0)
    thermal_conductivity: LambdaFloat = Field(None, ge=0)
    u_value: UValueFloat = Field(None, ge=0)
    fire_retardant: Optional[bool] = None
    water_vapour_resistant: Optional[bool] = None

    # discriminated facet
    facet: FacetUnion

    # dynamically compute the material_type based on FacetUnion
    @computed_field
    @property
    def material_type(self) -> MaterialType:
        return self.facet.material_type


# volumetric_ratio is always 1.0 by default
# if it is part of a disaggregation, then overwrite like so:
"""
mat = LcaMaterial(
    name="Reinforcement steel",
    volumetric_ratio=0.12, -> INFERRED BY LLM
    facet=MetallicFacet(material_type="metallic", ...)
)
"""

def assemble_lca_material(common: MaterialCommon, facet: FacetUnion) -> LcaMaterial:

    return LcaMaterial(

        # carry-over shared fields
        name=common.name,
        functional_types=common.functional_types,
        application_areas=common.application_areas,
        density=common.density,
        areal_density=common.areal_density,
        loadbearing=common.loadbearing,
        placement=common.placement,
        manufacturer=common.manufacturer,
        provenance=common.provenance,
        production_location=common.production_location,
        thickness=common.thickness,
        thermal_conductivity=common.thermal_conductivity,
        u_value=common.u_value,
        fire_retardant=common.fire_retardant,
        water_vapour_resistant=common.water_vapour_resistant,

        # facet (material type) details
        facet=facet
    )