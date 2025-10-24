from compas_lca.llm.context import Context

from compas_lca.matching_core.common import Common

from compas_lca.matching_core.material.common import MaterialCommon
from compas_lca.matching_core.material.bituminous import BituminousFacet
from compas_lca.matching_core.material.composite import CompositeFacet
from compas_lca.matching_core.material.concrete import ConcreteFacet
from compas_lca.matching_core.material.ligneous import LigneousFacet
from compas_lca.matching_core.material.metallic import MetallicFacet
from compas_lca.matching_core.material.mineral import MineralFacet
from compas_lca.matching_core.material.polymeric import PolymericFacet

from compas_lca.matching_core.component.common import ComponentCommon
from compas_lca.matching_core.component.building_service import BuildingServiceFacet
from compas_lca.matching_core.component.ceiling import CeilingFacet
from compas_lca.matching_core.component.conveyor import ConveyorFacet
from compas_lca.matching_core.component.curtain_wall import CurtainWallFacet
from compas_lca.matching_core.component.door import DoorFacet
from compas_lca.matching_core.component.roof import RoofFacet
from compas_lca.matching_core.component.shading import ShadingFacet
from compas_lca.matching_core.component.window import WindowFacet
from compas_lca.matching_core.component.window_fitting import WindowFittingFacet

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%% COMMON EXTRACTION CONTEXT %%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

COMMON_CTX = Context(
    instructions=(
        "You are an expert at extracting important data from a dataset describing a building MATERIAL or COMPONENT."
        " INPUT may be a JSON string, PDF text, or TXT. Carefully EXTRACT all relevant information and populate the output schema."
        " For each field in the schema, copy the value exactly from the input."
        " Only add values that are explicitly present in the input."
        " If a field is missing or unclear, leave its default. Do NOT infer or invent."
        " Return ONLY the JSON for the output schema—no extra text."
        "\n"
        "\n"
        "CRITICAL TASK: Determine `entry_type` accurately using the rules and examples below.\n"
        "\n"
        "DEFINITIONS\n"
        "- MATERIAL: A single homogeneous substance or a uniform material layer defined by physical/chemical nature "
        "(mineral, metallic, polymeric, bituminous, ligneous, or integrated composite). “Integrated composite” means the parts are "
        "bonded/formed into one monolithic layer (e.g., reinforced concrete, fiber-cement, WPC, EPS-integrated blocks) and NOT installed "
        "as a functional unit by itself.\n"
        "- COMPONENT: A manufactured assembly or device intended to be installed as a functional building element "
        "(e.g., closes an opening, provides services). Typically delivered as a unit/module/system with distinct separable parts or "
        "interfaces (frame+glass+hardware, tiles+grid, casing+driver, panel+mounting, duct run with fittings).\n"
        "\n"
        "DECISION ORDER (apply top-to-bottom)\n"
        "1) If the dataset clearly describes an installable element that performs a building function AS DELIVERED "
        "(window unit, door unit, shading device, HVAC device/duct run, lighting fixture, curtain-wall module, ceiling system with tiles+grid, conveyor, solar panel) "
        "→ entry_type=\"component\".\n"
        "2) Else, if it describes a single material or uniform layer—including integrated composites where sub-parts are fused into one monolithic product "
        "(e.g., reinforced concrete, concrete blocks with integrated EPS, metal or wood stud layer, plywood, fiber-cement, WPC) → entry_type=\"material\".\n"
        "3) If information is insufficient or contradictory → entry_type=\"unknown\".\n"
        "\n"
        "DISAMBIGUATION / NAMING TRAPS (override naive keyword heuristics)\n"
        "- Words like “unit/system/module/device/structure/block/frame” ALONE do NOT make it a component. "
        "Check whether the described thing is delivered/installed as a functional element with separable parts and an explicit building function. "
        "If not, classify as MATERIAL.\n"
        "- A material used for making a component (e.g., “spruce wooden window frame” as a material grade/section) is still MATERIAL unless the dataset "
        "includes the full installable unit (frame+glazing+hardware).\n"
        "- “Precast concrete elements … for walls/pillars/beams” describing a concrete recipe/grade or generic element material spec → MATERIAL (concrete). "
        "If it specifies a finished, project-specific element with reinforcement, embeds, hardware, lifting anchors, or erection details as a supplied unit → COMPONENT.\n"
        "- “Shuttering block / formwork block with integrated insulation” that is a single block/layer product → MATERIAL (integrated composite), not a component assembly.\n"
    ),
    output_type=Common
)


TEMPLATE = (
    "You are an expert at extracting important information from a dataset describing {entry}."
    " This dataset is either a single JSON string, a PDF file, or a TXT file."
    " Your task is to carefully EXTRACT all relevant information and populate the fields of the output schema."
    " For each field in the schema, locate the corresponding value in input dataset."
    " Only add values in the output schema if they are explicitly present."
    " If a field is missing or cannot be determined, leave the default value. Do not invent or assume values."
    " Do not include any explanatory text outside of the schema output."
)

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%% MATERIAL EXTRACTION CONTEXT %%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

MATERIAL_COMMON_CTX = Context(
    instructions=TEMPLATE.format(entry="a material"),
    output_type=MaterialCommon
)

BITUMINOUS_CTX = Context(
    instructions=TEMPLATE.format(entry="a bituminous material"),
    output_type=BituminousFacet
)

COMPOSITE_CTX = Context(
    instructions=TEMPLATE.format(entry="a composite material"),
    output_type=CompositeFacet
)

CONCRETE_CTX = Context(
    instructions=TEMPLATE.format(entry="a concrete/cementitious material"),
    output_type=ConcreteFacet
)

LIGNEOUS_CTX = Context(
    instructions=TEMPLATE.format(entry="a ligneous material"),
    output_type=LigneousFacet
)

METALLIC_CTX = Context(
    instructions=TEMPLATE.format(entry="a metallic material"),
    output_type=MetallicFacet
)

MINERAL_CTX = Context(
    instructions=TEMPLATE.format(entry="a mineral material"),
    output_type=MineralFacet
)

POLYMERIC_CTX = Context(
    instructions=TEMPLATE.format(entry="a polymeric material"),
    output_type=PolymericFacet
)

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%% COMPONENT EXTRACTION CONTEXT %%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

COMPONENT_COMMON_CTX = Context(
    instructions=TEMPLATE.format(entry="a component or a system-level assembly"),
    output_type=ComponentCommon
)

BUILDING_SERVICE_CTX = Context(
    instructions=TEMPLATE.format(entry="a building service system or component"),
    output_type=BuildingServiceFacet
)

CEILING_CTX = Context(
    instructions=TEMPLATE.format(entry="a (pre-fabricated) ceiling assembly"),
    output_type=CeilingFacet
)

CONVEYOR_CTX = Context(
    instructions=TEMPLATE.format(entry="a conveyor component"),
    output_type=ConveyorFacet
)

CURTAIN_WALL_CTX = Context(
    instructions=TEMPLATE.format(entry="a curtain wall module, component or assembly"),
    output_type=CurtainWallFacet
)

DOOR_CTX = Context(
    instructions=TEMPLATE.format(entry="a door unit or door components"),
    output_type=DoorFacet
)

ROOF_CTX = Context(
    instructions=TEMPLATE.format(entry="a roof assembly or roof component"),
    output_type=RoofFacet
)

SHADING_CTX = Context(
    instructions=TEMPLATE.format(entry="a shading device"),
    output_type=ShadingFacet
)

WINDOW_CTX = Context(
    instructions=TEMPLATE.format(entry="a window unit or assembly"),
    output_type=WindowFacet
)

WINDOW_FITTING_CTX = Context(
    instructions=TEMPLATE.format(entry="a window fitting product"),
    output_type=WindowFittingFacet
)