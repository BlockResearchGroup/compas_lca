from compas_lca.llm.context import Context

from compas_lca.matching_core.common import Common

from compas_lca.matching_core.material.common import MaterialCommon
from compas_lca.matching_core.material.bituminous import BituminousFacet
from compas_lca.matching_core.material.biobased import BiobasedFacet
from compas_lca.matching_core.material.composite import CompositeFacet
from compas_lca.matching_core.material.concrete import ConcreteFacet
from compas_lca.matching_core.material.biobased import BiobasedFacet
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
You are an expert at extracting data from a dataset describing a building MATERIAL or COMPONENT.

TASK: Extract all relevant information and populate the output schema fields.
- Copy values exactly from the input dataset.
- Only add values that are explicitly present.
- If a field is missing or unclear, leave its default. Do NOT infer or invent.
- Follow the field descriptions in the schema for classification rules.

═══════════════════════════════════════════════════════════════════════════════
CLASSIFICATION EXAMPLES (follow these patterns):
═══════════════════════════════════════════════════════════════════════════════

BIOBASED materials (non-wood plant/animal fibers):
  • "Hempflax Thermo Hemp Combi Jute" → entry_type: material, material_type: biobased
  • "Schafwolldämmung" (sheep wool insulation) → entry_type: material, material_type: biobased
  • "Cork insulation board" → entry_type: material, material_type: biobased
  • "Flax fiber insulation" → entry_type: material, material_type: biobased

METALLIC materials (single metal profiles/sheets/sections are materials, NOT components):
  • "Aluminium casement frame section, powder coated" → entry_type: material, material_type: metallic
  • "Steel beam IPE 200" → entry_type: material, material_type: metallic
  • "Aluminum profile for windows" → entry_type: material, material_type: metallic
  • "Copper pipe DN15" → entry_type: material, material_type: metallic

MINERAL materials (glass panes are materials, NOT components/infill):
  • "Float glass 6mm" → entry_type: material, material_type: mineral
  • "Laminated safety glass" → entry_type: material, material_type: mineral
  • "Gypsum board 12.5mm" → entry_type: material, material_type: mineral
  • "Mineral wool insulation" → entry_type: material, material_type: mineral

COMPONENTS (only for multi-material assemblies):
  • "Window unit with aluminium frame and double glazing" → entry_type: component
  • "PU boards with aluminium facing" → entry_type: component (insulation_element)
  • "ETICS system" → entry_type: component
  • "IGU triple glazing with argon fill" → entry_type: component
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
       * Check if this layer against the "other_layers" and determine if THIS layer is *realistically* the loadbearing part.
       * Examples:
           - Large thickness + Concrete, massive wood, steel, concrete → likely loadbearing.
           - Plaster, insulation, finish materials → not loadbearing.
       * If unclear, leave null.

3. PLACEMENT LOGIC
   - Use the "parent_element_properties" as a reference for the general placement (interior/exterior).
   - If the parent element is interior, assign "placement" = "interior"
   - If the parent element is exterior, infer the realistic placement of the target layer **within** that element, and within the context of the "other_layers":
       * Layers directly exposed to outdoor air, weather, or ground → "placement" = "exterior".
       * Layers directly exposed to indoor air → "placement" = "interior".
       * Layers embedded inside the construction (e.g., insulation, membranes, vapor barriers)
         → "placement" = "interior" (even if part of an exterior element).
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
    "\n\n"
    "CRITICAL: Follow the keyword detection rules in the field descriptions."
    " If the product name contains material keywords (e.g., hemp, aluminum, glass, steel, PVC),"
    " classify based on those keywords first before considering application context."
)

MATERIAL_COMMON_PROMPT = (
    "You are an expert at classifying building materials by their dominant composition.\n\n"
    "TASK: Determine the material_type based on keywords in the product name/description.\n\n"
    "═══════════════════════════════════════════════════════════════════════════════\n"
    "KEYWORD CLASSIFICATION (check product name FIRST):\n"
    "═══════════════════════════════════════════════════════════════════════════════\n\n"
    "BIOBASED (non-wood plant/animal fibers) → material_type: 'biobased'\n"
    "  Keywords: hemp, Hanf, Thermo-Hanf, Thermohanf, Hempflax, flax, Flachs, linen,\n"
    "            jute, Jute, sheep wool, Schafwolle, straw, Stroh, cork, Kork,\n"
    "            cotton, Baumwolle, bamboo, Bambus, coconut, Kokos, sisal, coir\n"
    "  Examples:\n"
    "    • 'Hempflax Thermo Hemp Combi Jute' → biobased\n"
    "    • 'Schafwolldämmung' → biobased\n"
    "    • 'Thermo Hanf Premium' → biobased\n"
    "    • 'Cork insulation board' → biobased\n"
    "    • 'Flax fiber insulation' → biobased\n\n"
    "WOOD (tree-derived) → material_type: 'wood'\n"
    "  Keywords: wood, Holz, timber, lumber, plywood, OSB, MDF, HDF, CLT, glulam\n\n"
    "METALLIC → material_type: 'metallic'\n"
    "  Keywords: steel, Stahl, aluminum, aluminium, copper, zinc, brass, iron\n\n"
    "POLYMERIC → material_type: 'polymeric'\n"
    "  Keywords: PVC, PE, PP, PUR, PIR, EPS, XPS, polystyrene, polyurethane, EPDM\n\n"
    "MINERAL → material_type: 'mineral'\n"
    "  Keywords: glass, gypsum, Gips, lime, brick, Ziegel, mineral wool, rock wool\n\n"
    "CONCRETE → material_type: 'concrete'\n"
    "  Keywords: concrete, Beton, precast, aerated concrete, Porenbeton\n\n"
    "═══════════════════════════════════════════════════════════════════════════════\n"
    "NEVER use 'unknown' if ANY material keyword is found in the product name.\n"
    "═══════════════════════════════════════════════════════════════════════════════\n"
)

MATERIAL_COMMON_CTX = Context(
    instructions=MATERIAL_COMMON_PROMPT,
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