from compas_lca.enums import MaterialType
from compas_lca.enums import EntryType
from compas_lca.enums import ComponentType

from compas_lca.llm.ctx.extraction_context import MINERAL_CTX
from compas_lca.llm.ctx.extraction_context import CONCRETE_CTX
from compas_lca.llm.ctx.extraction_context import WOOD_CTX
from compas_lca.llm.ctx.extraction_context import METALLIC_CTX
from compas_lca.llm.ctx.extraction_context import POLYMERIC_CTX
from compas_lca.llm.ctx.extraction_context import BIOBASED_CTX
from compas_lca.llm.ctx.extraction_context import BITUMINOUS_CTX
from compas_lca.llm.ctx.extraction_context import COMPOSITE_CTX

from compas_lca.llm.ctx.extraction_context import BUILDING_SERVICE_CTX
from compas_lca.llm.ctx.extraction_context import CEILING_CTX
from compas_lca.llm.ctx.extraction_context import CONVEYOR_CTX
from compas_lca.llm.ctx.extraction_context import CURTAIN_WALL_CTX
from compas_lca.llm.ctx.extraction_context import DOOR_CTX
from compas_lca.llm.ctx.extraction_context import ROOF_CTX
from compas_lca.llm.ctx.extraction_context import INFILL_CTX
from compas_lca.llm.ctx.extraction_context import INSULATION_ELEMENT_CTX
from compas_lca.llm.ctx.extraction_context import SHADING_CTX
from compas_lca.llm.ctx.extraction_context import STAIR_CTX
from compas_lca.llm.ctx.extraction_context import RAILING_CTX
from compas_lca.llm.ctx.extraction_context import WINDOW_FITTING_CTX
from compas_lca.llm.ctx.extraction_context import WINDOW_CTX

from compas_lca.matching_core.material.bituminous import BituminousFacet
from compas_lca.matching_core.material.concrete import ConcreteFacet
from compas_lca.matching_core.material.wood import WoodFacet
from compas_lca.matching_core.material.metallic import MetallicFacet
from compas_lca.matching_core.material.mineral import MineralFacet
from compas_lca.matching_core.material.biobased import BiobasedFacet
from compas_lca.matching_core.material.polymeric import PolymericFacet
from compas_lca.matching_core.material.composite import CompositeFacet

from compas_lca.matching_core.component.building_service import BuildingServiceFacet
from compas_lca.matching_core.component.ceiling import CeilingFacet
from compas_lca.matching_core.component.conveyor import ConveyorFacet
from compas_lca.matching_core.component.curtain_wall import CurtainWallFacet
from compas_lca.matching_core.component.door import DoorFacet
from compas_lca.matching_core.component.infill import InfillFacet
from compas_lca.matching_core.component.insulation_element import InsulationElementFacet
from compas_lca.matching_core.component.roof import RoofFacet
from compas_lca.matching_core.component.shading import ShadingFacet
from compas_lca.matching_core.component.stairs import StairFacet
from compas_lca.matching_core.component.railing import RailingFacet
from compas_lca.matching_core.component.window_fitting import WindowFittingFacet
from compas_lca.matching_core.component.window import WindowFacet

# Map entry type Literal for optional forcing of EntryType
MAP_TO_ENTRY_TYPE = {
    "material": EntryType.material,
    "component": EntryType.component,
    "unknown": EntryType.unknown,
}


# Map material type to its LLM extraction context
CTX_BY_MAT_TYPE = {
    MaterialType.mineral: MINERAL_CTX,
    MaterialType.concrete: CONCRETE_CTX,
    MaterialType.wood: WOOD_CTX,
    MaterialType.metallic: METALLIC_CTX,
    MaterialType.polymeric: POLYMERIC_CTX,
    MaterialType.biobased: BIOBASED_CTX,
    MaterialType.bituminous: BITUMINOUS_CTX,
    MaterialType.composite: COMPOSITE_CTX,
}

# Map material type to its corresponding facet model
MODEL_BY_MAT_TYPE = {
    MaterialType.mineral: MineralFacet,
    MaterialType.concrete: ConcreteFacet,
    MaterialType.wood: WoodFacet,
    MaterialType.metallic: MetallicFacet,
    MaterialType.polymeric: PolymericFacet,
    MaterialType.biobased: BiobasedFacet,
    MaterialType.bituminous: BituminousFacet,
    MaterialType.composite: CompositeFacet,
}

# Map component type to its LLM extraction context
CTX_BY_COMP_TYPE = {
    ComponentType.building_service: BUILDING_SERVICE_CTX,
    ComponentType.ceiling: CEILING_CTX,
    ComponentType.conveyor: CONVEYOR_CTX,
    ComponentType.curtain_wall: CURTAIN_WALL_CTX,
    ComponentType.door: DOOR_CTX,
    ComponentType.infill: INFILL_CTX,
    ComponentType.insulation_element: INSULATION_ELEMENT_CTX,
    ComponentType.roof: ROOF_CTX,
    ComponentType.shading_device: SHADING_CTX,
    ComponentType.stairs: STAIR_CTX,
    ComponentType.railing: RAILING_CTX,
    ComponentType.window_fitting: WINDOW_FITTING_CTX,
    ComponentType.window: WINDOW_CTX,
}

# Map component type to its corresponding facet model
MODEL_BY_COMP_TYPE = {
    ComponentType.building_service: BuildingServiceFacet,
    ComponentType.ceiling: CeilingFacet,
    ComponentType.conveyor: ConveyorFacet,
    ComponentType.curtain_wall: CurtainWallFacet,
    ComponentType.door: DoorFacet,
    ComponentType.infill: InfillFacet,
    ComponentType.insulation_element: InsulationElementFacet,
    ComponentType.roof: RoofFacet,
    ComponentType.shading_device: ShadingFacet,
    ComponentType.stairs: StairFacet,
    ComponentType.railing: RailingFacet,
    ComponentType.window_fitting: WindowFittingFacet,
    ComponentType.window: WindowFacet,
}
