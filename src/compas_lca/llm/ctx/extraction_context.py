from compas_lca.llm.context import Context

from compas_lca.matching_core.common import Common

from compas_lca.matching_core.material.common import MaterialCommon
from compas_lca.matching_core.material.bituminous import BituminousFacet
from compas_lca.matching_core.material.biobased import BiobasedFacet
from compas_lca.matching_core.material.composite import CompositeFacet
from compas_lca.matching_core.material.concrete import ConcreteFacet
from compas_lca.matching_core.material.wood import WoodFacet
from compas_lca.matching_core.material.metallic import MetallicFacet
from compas_lca.matching_core.material.mineral import MineralFacet
from compas_lca.matching_core.material.polymeric import PolymericFacet

from compas_lca.matching_core.component.common import ComponentCommon
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
from compas_lca.matching_core.component.window import WindowFacet
from compas_lca.matching_core.component.window_fitting import WindowFittingFacet

"""
TO DO:
Test TEMPLATE_LAYER and LAYER_COMMON_CTX and
add layer contexts in ifc extraction workflow
"""

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%% COMMON EXTRACTION CONTEXT %%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


ELEMENT_COMMON_PROMPT = """
TASK
Classify a BUILDING MODEL ELEMENT record as "material", "component", or "unknown".
Populate only the requested fields. Do not invent data. Do not interpret the definitions
of "material" or "component" beyond what is given in the instructions below.

YOU ARE CLASSIFYING THE CURRENT RECORD ONLY
- Always classify the dataset/record itself, not the larger building system it belongs to.
- An element can be part of a curtain wall, façade, roof, or other assembly and still be "material"
  if THIS record describes only a single material section.

ABSOLUTE PRIORITY RULE (APPLY FIRST)
- If the buildng element represents a window or door assembly (e.g. IfcWindow or IfcDoor), always
  assign entry_type = "component"
- Otherwise, if the record clearly describes exactly ONE material for this element, and there is no evidence
  of multiple materials or a multi-layer build-up, you MUST set entry_type = "material".

HARD OVERRIDES:
1. SINGLE-MATERIAL RULE (highest priority)
   If the dataset meets the conditions above (one clear material in material_data and no indication
   of multiple materials or layers), then:
   → entry_type = "material".

2. UNITIZED / MULTI-MATERIAL COMPONENT RULE
   Only if rule 1 does NOT apply:
   - If the record clearly describes an installable product or system that:
       * performs a building function as delivered (e.g., closes an opening, provides a service), AND
       * involves multiple materials or separable parts (for example, frame + glass + hardware,
         tiles + grid, panel + substructure, casing + driver),
     then:
     → entry_type = "component".

   Typical examples include (when multiple materials or full units are described):
   - windows, doors, HVAC devices, lighting fixtures, solar panels,
     ceiling systems with tiles and grid, composite panels with fixings.

3. UNKNOWN RULE
   If neither 1 nor 2 can be applied confidently, and the record is ambiguous or purely administrative:
   → entry_type = "unknown".

GENERAL PRINCIPLES

- Prefer "material" whenever there is a single, uniform material and a uniform thickness/section for the element.
- Use "component" only when there is clear evidence of an installable assembly with multiple separable materials.
- Do not infer missing values; base the classification only on what is present in the record.
"""




ELEMENT_COMMON_CTX = Context(
    instructions=ELEMENT_COMMON_PROMPT,
    output_type=Common
)


ITEM_COMMON_PROMPT = """
You are an expert at extracting important data from a dataset describing a building MATERIAL or COMPONENT.
INPUT may be a JSON string, PDF text, or TXT. Carefully EXTRACT all relevant information and populate the output schema.
For each field in the schema, copy the value exactly from the input.
Only add values that are explicitly present in the input.
If a field is missing or unclear, leave its default. Do NOT infer or invent.
Return ONLY the JSON for the output schema—no extra text.

CRITICAL TASK: Determine `entry_type` accurately using the rules and examples below.

DEFINITIONS
- MATERIAL: A single homogeneous substance or a uniform material layer defined by physical/chemical nature
  (mineral, metallic, polymeric, bituminous, wood-based, or integrated composite). “Integrated composite” means the parts are
  bonded/formed into one monolithic layer (e.g., reinforced concrete, fiber-cement, WPC, EPS-integrated blocks) and NOT installed
  as a functional unit by itself.
  NOTE: Flat glass as a single pane is classified as MATERIAL unless the dataset describes a multi-pane assembly or functional
  glazing unit.

- COMPONENT: A manufactured assembly, product, or device intended to be installed as a functional building element or
  preassembled unit (e.g., glazing units, window/door units, ceiling systems, HVAC devices, lighting fixtures).
  This also includes multi-material **insulation elements** such as sandwich panels, masonry units with infill,
  insulation profiles, ETICS systems, or similar products where multiple distinct materials are
  combined into one functional insulation element.

DECISION ORDER (apply top-to-bottom)
1) If the dataset describes a single material or uniform layer—including monolithic integrated composites—set entry_type="material".
2) If the dataset describes:
     • a functional installable building element composed of MULTIPLE materials, OR
     • an insulation element composed of MULTIPLE different materials (e.g., sandwich panel, sandwich board, masonry unit with infill,
       layered-bonded insulation, ETICS system)
   → set entry_type="component".
     • if the insulation element or product is made from ONE material only, then set entry_type="material"!!
3) If information is insufficient or contradictory → entry_type="unknown".

DISAMBIGUATION / NAMING TRAPS (override naive keyword heuristics)
- Words like “unit/system/module/device/structure/block/frame” ALONE do NOT make it a component.
  Check whether the described thing is delivered/installed as a functional element with separable parts made from different materials.
  If not, classify as MATERIAL.
- A material used for making a component (e.g., “wooden window frame”) is still MATERIAL unless the dataset includes the full 
  installable unit (e.g., glazing assembly, frame+glass+hardware) with multiple materials.
"""

ITEM_COMMON_CTX = Context(
    instructions=ITEM_COMMON_PROMPT,
    output_type=Common
)

# Layer context (for now very specific to the IFC workflow)
LAYER_COMMON_PROMPT = """
You are an expert in interpreting building data (IFC-based) and populating fields in the 'Common' schema
for a **single material layer** of a multi-layer building element.

Your task:
Fill out the 'Common' JSON fields based ONLY on the data provided.

The input JSON always contains:
- "target_layer": describing ONE material layer (the material to classify)
- "parent_element_context": describing the full element (used only for applicability)

INSTRUCTIONS & RULES:
1. FIELD SOURCING
   - Use ONLY "target_layer" fields to infer:
       * name
       * thickness (converted to millimeters)
   - Use "parent_element_context" ONLY for applicability:
       * loadbearing
       * placement (interior/exterior)
       * manufacturer (if explicitly applies to the layer)
   - Any other properties (thermal_conductivity, u_value, fire_retardant, water_vapour_resistant)
     must be assigned ONLY if the dataset makes them *unambiguously clear for the target layer*.

2. LOADBEARING LOGIC
   - If parent element is loadbearing:
       * Check if this layer is *realistically* the loadbearing part.
       * Examples:
           - Concrete, massive wood, steel, concrete → likely loadbearing.
           - Plaster, insulation, finish materials → not loadbearing.
       * If unclear, leave null.

3. PLACEMENT LOGIC
   - Use the parent element's context (interior/exterior) as a reference for the general environment.
   - Then infer the realistic placement of the target layer **within** that element:
       * Layers directly exposed to outdoor air, weather, or ground → exterior.
       * Layers directly exposed to indoor air → interior.
       * Layers embedded inside the construction (e.g., insulation, membranes, vapor barriers)
         → interior (even if part of an exterior element).
   - If the placement cannot be confidently inferred, or the context is missing, leave null.

4. MANUFACTURER
   - If a manufacturer name is found directly related to the target layer, use it.
   - If the manufacturer is clearly only for the whole assembly, leave null.

5. OTHER FIELDS (thermal_conductivity, u_value, fire_retardant, water_vapour_resistant)
   - Assign only if explicitly stated or can be inferred with *high confidence* from material type.
   - Avoid guessing from element context (e.g., don't infer λ just because it's insulation).

6. MISSING OR UNCLEAR VALUES
   - Leave them as null (do not fabricate).
   - Never hallucinate a manufacturer, property value, or performance number.

OUTPUT FORMAT:
Return ONLY a single valid JSON object strictly matching the 'Common' schema.
Do not include any explanation, reasoning, comments, or text before or after the JSON.
"""

LAYER_COMMON_CTX = Context(
    instructions=LAYER_COMMON_PROMPT,
    output_type=Common
)


TEMPLATE_LAYER = (
    "You are an expert at extracting important information from a dataset describing {entry}. "
    "The dataset may include a 'target_layer' and a 'parent_element_context'. "
    ""
    "DATA SOURCES & PRIORITY:\n"
    "1) For the following fields, read ONLY from 'target_layer': "
    "   - 'material_type', 'functional_types', 'density', 'areal_density'. "
    "   If these fields are NOT explicitly present (or are ambiguous) in 'target_layer', leave defaults; "
    "   do NOT infer or guess from any other key.\n"
    "2) You may consult 'parent_element_context' ONLY for 'application_areas'. "
    "   For 'application_areas', extract the element being described from 'parent_element_context' "
    "   (e.g., the 'entity' or, if necessary, the element referenced in 'name').\n"
    ""
    "STRICT PROHIBITIONS (NO INFERENCE FROM HOST ELEMENT):\n"
    "- Never use 'parent_element_context' (e.g., 'name' like 'Floor:Finish Floor - Wood', 'object_type', or host categories) "
    "  to infer 'material_type', 'functional_types', 'density', or 'areal_density'. "
    "- Example: If 'target_layer.material_name' is 'Insulation' without a specified subtype, "
    "  do NOT infer 'material_type' as 'wood', 'polymeric', or 'mineral' from a host like 'Wood' in 'parent_element_context'. "
    "- If 'target_layer' does not unambiguously specify a value, leave the schema default for that field.\n"
    ""
    "CLARITY & AMBIGUITY RULES:\n"
    "- Only add values that are explicitly present and unambiguous in 'target_layer' (or, for 'application_areas', "
    "  explicitly present in 'parent_element_context'). "
    "- If a numeric value lacks a unit and no unit is explicitly given, leave the default (do not assume units). "
    "- If terms are generic (e.g., 'Insulation' without subtype), treat them as insufficient to determine subtype or composition.\n"
    ""
    "OUTPUT RULES:\n"
    "- For each field in the schema, supply the value ONLY if the above rules allow it. "
    "- If a field is missing or cannot be determined under these rules, leave the default value. "
    "- Do not include any explanatory text outside of the schema output."
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

MATERIAL_COMMON_LAYER_CTX = Context(
    instructions=TEMPLATE_LAYER.format(entry="a material"),
    output_type=MaterialCommon
)

BIOBASED_CTX = Context(
    instructions=TEMPLATE.format(entry="a bio-based material"),
    output_type=BiobasedFacet
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

WOOD_CTX = Context(
    instructions=TEMPLATE.format(entry="a wood-based material"),
    output_type=WoodFacet
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

INFILL_CTX = Context(
    instructions=TEMPLATE.format(entry="an infill for windows, doors, or curtain wall units"),
    output_type=InfillFacet
)

INSULATION_ELEMENT_CTX = Context(
    instructions=TEMPLATE.format(entry="an insulation element"),
    output_type=InsulationElementFacet
)

ROOF_CTX = Context(
    instructions=TEMPLATE.format(entry="a roof assembly or roof component"),
    output_type=RoofFacet
)

SHADING_CTX = Context(
    instructions=TEMPLATE.format(entry="a shading device"),
    output_type=ShadingFacet
)

STAIR_CTX = Context(
    instructions=TEMPLATE.format(entry="a stair"),
    output_type=StairFacet
)

RAILING_CTX = Context(
    instructions=TEMPLATE.format(entry="a railing"),
    output_type=RailingFacet
)

WINDOW_CTX = Context(
    instructions=TEMPLATE.format(entry="a window unit or assembly"),
    output_type=WindowFacet
)

WINDOW_FITTING_CTX = Context(
    instructions=TEMPLATE.format(entry="a window fitting product"),
    output_type=WindowFittingFacet
)