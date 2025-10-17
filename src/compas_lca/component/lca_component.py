from uuid import uuid4
from uuid import UUID

from typing import Optional
from typing import Annotated
from typing import Union

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import computed_field

from compas_lca.component.common import ComponentCommon
from compas_lca.component.building_system import BuildingSystemFacet
from compas_lca.component.ceiling import CeilingFacet
from compas_lca.component.conveyor import ConveyorFacet
from compas_lca.component.door import DoorFacet
from compas_lca.component.roof import RoofFacet
from compas_lca.component.wall import WallFacet
from compas_lca.component.window import WindowFacet

from compas_lca.enums import ComponentType
from compas_lca.enums import Loadbearing
from compas_lca.enums import InteriorExterior

from compas_lca.validators import LoadbearingType
from compas_lca.validators import InteriorExteriorType
from compas_lca.validators import ManufacturerStr
from compas_lca.validators import ThicknessFloat
from compas_lca.validators import UValueFloat

# discriminators (drafts)
FacetUnion = Annotated[
    Union[
        WindowFacet,
        DoorFacet,
        RoofFacet,
        WallFacet,
        CeilingFacet,
        BuildingSystemFacet,
        ConveyorFacet
    ],
    Field(discriminator="material_type")
]


class LcaComponent(BaseModel):
    """
    LcaComponent as container for any kind and nested/branched attributes
    This serves as a mixed bag of pre-made component's semantic, and functional attributes
    Reverts to this, if 1.) Building model element is abstract (i.e., window modeled as surface)
    or if 2.) the LCA inventory data is a pre-assembled product
    """

    # model config (adjustable)
    model_config = ConfigDict(extra = "forbid")

    # create UUID for an LcaMaterial instance
    id: UUID = Field(default_factory=uuid4)

    # carry-over shared fields from LcaMaterialCommon
    component_name: str
    loadbearing: LoadbearingType = Loadbearing.unknown
    placement: InteriorExteriorType = InteriorExterior.unknown
    manufacturer: ManufacturerStr = None
    provenance: Optional[str] = None
    production_location: Optional[str] = None
    thickness: ThicknessFloat = Field(None, ge=0)
    u_value: UValueFloat = Field(None, ge=0)
    fire_retardant = Optional[bool] = None
    water_vapour_resistant = Optional[bool] = None

    # discriminated facet
    facet: FacetUnion

    # dynamically compute the material_type based on FacetUnion
    @computed_field
    @property
    def component_type(self) -> ComponentType:
        return self.facet.component_type


def assemble_lca_material(common: ComponentCommon, facet: FacetUnion) -> LcaComponent:

    return LcaComponent(

        # carry-over shared fields
        component_name=common.component_name,
        loadbearing=common.loadbearing,
        placement=common.placement,
        manufacturer=common.manufacturer,
        provenance=common.provenance,
        production_location=common.production_location,
        thickness=common.thickness,
        u_value=common.u_value,
        fire_retardant=common.fire_retardant,
        water_vapour_resistant=common.water_vapour_resistant,

        # facet (material type) details
        facet=facet
    )