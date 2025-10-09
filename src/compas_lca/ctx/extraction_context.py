from compas_lca.model.attributes.metadata import Metadata

from compas_lca.model.attributes.materialspec import ParsedMaterial

from compas_lca.inventory.item import InventoryItemLLM

from compas_lca.llm.agent import BaseAgent

from compas_lca.llm.context import Context

from compas_lca.llm.tools import RebarTable
from compas_lca.llm.tools import RebarRatio
from compas_lca.llm.tools import rebar_ratio_lookup
from compas_lca.llm.tools import REBAR_RATIO_CSV

"""
New approach:
Instead of llm/extraction_agents.py with instatiated agents,
the ctx folder predefines all relevant instructions for the BaseAgent class.
In workflow scripts, these contexts can be imported and used.

Example agent configuration:
    metadata_agent = BaseAgent.from_config(context=METADATA_CTX)
    building_element = Path("data/samples/element_1.json")
    raw = building_element.read_text(encoding="utf-8")
    run = metadata_agent.execute_run(raw)
    payload = getattr(run.result, "data", None) or getattr(run.result, "output", None)
    out_fp.write_text(payload.model_dump_json(indent=2), encoding="utf-8")

    to see example workflow for metadata extraction, go to:
    "compas_lca/workflows/extraction.py"
"""


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%% ELEMENT EXTRACTION CONTEXT %%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# ======== METADATA CONTEXT ========
# Defines context for relevant metadata from raw building element data

METADATA_CTX = Context(
    instructions=(
        "You are an expert at extracting important Metadata from building element data."
        "You are given raw building element data as a single JSON string."
        "Your task is to carefully EXTRACT all relevant information from this JSON and populate the fields of the `Metadata` output schema."
        "For each field in the schema, locate the corresponding value in the JSON."
        "Only add values in the output schema if they are explicitly present."
        "If a field is missing or cannot be determined, mark is with `null`. Do not invent or assume values."
        "Do not include any explanatory text outside of the schema output."
    ),
    output_type=Metadata
)


# ======== MATERIAL PARSING CONTEXT ========
# Outputs ParsedMaterial (normalize name, decide pure/composite, collect hints)

PARSE_MATERIAL_CTX = Context(
    instructions=(
        "You are an expert at identifying and labeling Material Information from building element data."
        "You will receive a single material descriptor string extracted from building element data.\n"
        "Prioritize data within the Building Element JSON file that clearly refer to Material specifications."
        "Always preserve the verbatim material label in `literal_name` when available."
        "Classify whether the descriptor is a 'pure' material or a 'composite' "
        "for downstream LCA-database mapping purposes:\n"
        "- pure → maps to a single LCA dataset even if internally a mixture (e.g., 'timber', 'brick', 'XPS insulation').\n"
        "- composite → clearly combines distinct materials that each require separate datasets "
        "(e.g., 'concrete' with loadbearing specification → concrete + rebar steel composite; 'metal stud cavity' → steel + air/insulation composite).\n"
        "Return a valid `ParsedMaterial` only. If uncertain, set material_type='unknown' and keep confidence low.\n"
        "Do not add any text outside the schema."
    ),
    output_type=ParsedMaterial,
)


# ======== MATERIAL DECOMPOSITION CONTEXT ========
# Agents for Material Decomposition of common composites
# More agents to come, for now only rebar

DECOMPOSE_REBAR_CTX = Context(
    instructions=(
        "Identify the reinforced-concrete building component mentioned by the user and "
        "return the **minimum** and **maximum** rebar ratios (m3/m3) for that component. "
        "Use the `rebar_ratio_lookup` tool to fetch values from the in-project CSV. "
        "If the wording is a close variant (e.g., 'retaining wall' vs 'retaining walls'), "
        "pick the closest match. The output MUST conform to the RebarRatio schema."
    ),
    output_type=RebarRatio,
    tool_resources_type=RebarTable,
    tools=[rebar_ratio_lookup]
)

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%% LCA DATABASE EXTRACTION CONTEXT %%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# ======== WEB_SCRAPING_AGENT  ========
# Identifies relevant data from a scraped HTML (refering to an online EPD)

WEB_SCRAPING_CTX = Context(
    instructions=(
        "placeholder"
    ),
    output_type="placeholder"
)

# ======== INVENTORY CONTEXT ========
# Extracts relevant data fields from LCA databases.
# Fills in functions and use type that cannot be extracted through a script.

INVENTORY_CONTEXT = Context(
    instructions=(
        "You are an expert at extracting important data from EPDs."
        "You are given data from an EPD in form of a JSON document as plain text."
        "Your task is to carefully EXTRACT all relevant information from this JSON and populate the fields of the `InventoryItem` output schema."
        "Your output must strictly conform to the `InventoryItem` schema."
        "For each field in the schema, locate the corresponding value in the JSON."
        "Only add values in the output schema if they are explicitly present."
        "If a field is missing or cannot be determined, mark it with `null`. Do not invent or assume values."
        "Do not include any explanatory text outside of the schema output."
    ),
    output_type=InventoryItemLLM
)


# ======== SPECULATION CONTEXT ========
# Tries to fill in the blanks

SPECULATION_CTX = Context(
    instructions=(
        "placeholder"
    ),
    output_type="placeholder"
)
