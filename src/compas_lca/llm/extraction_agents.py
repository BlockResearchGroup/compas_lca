from compas_lca.model.attributes.metadata import Metadata
from compas_lca.model.attributes.materialspec import ParsedMaterial
from compas_lca.model.attributes.materialspec import MaterialBreakdown
from compas_lca.inventory.item import InventoryItemLLM

from compas_lca.llm.agent import Context

from compas_lca.llm.tools import DataTable
from compas_lca.llm.tools import rebar_mass_fraction
from compas_lca.llm.tools import density_lookup
from compas_lca.llm.tools import studs_steel_volume_fraction

from compas_lca.llm.config import load_agent


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%% ELEMENT EXTRACTION AGENTS %%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# ======== METADATA AGENT ========
# Extracts relevant metadata from raw building element data

METADATA_AGENT = load_agent(
    context=Context(
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
)

# ======== MATERIAL PARSING AGENT ========
# Outputs ParsedMaterial (normalize name, decide pure/composite, collect hints)

PARSE_MATERIAL_AGENT = load_agent(
    context=Context(
        instructions=(
            "You are an expert at identifying and labeling Material Information from building element data."
            "You will receive a single material descriptor string extracted from building element data.\n"
            "Prioritize data within the Building Element JSON file that clearly refer to Material specifications"
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
)

# ======== MATERIAL DECOMPOSITION AGENT ========
# Outputs Material Decomposition 

DECOMPOSE_MATERIAL_AGENT = load_agent(
    context=Context(
        instructions=(
            "You receive either:\n"
            "  (a) a ParsedMaterial object, or\n"
            "  (b) a JSON with enough fields to determine if the material is composite.\n\n"
            "Your job: if the material is COMPOSITE, break it down into pure components with **fractions that sum to ~1.0**.\n"
            "You have callable tools: rebar_mass_fraction, density_lookup, studs_steel_volume_fraction.\n"
            "Use the tools below when appropriate:\n"
            "• rebar_mass_fraction(...) → for reinforced concrete, returns steel mass share.\n"
            "• density_lookup(name) → to convert between volume↔mass shares when needed.\n"
            "• studs_steel_volume_fraction(...) → for metal stud cavity walls.\n\n"
            "Rules:\n"
            "1) **Reinforced concrete:** call rebar_mass_fraction(...) to get steel mass share. "
            "   Convert to VOLUME basis if required using density_lookup('Rebar steel') and density_lookup('Concrete'). "
            "   Components should be canonical names: 'Concrete', 'Rebar steel'. Record any assumption in `assumptions`.\n"
            "2) **Stud cavity walls:** call studs_steel_volume_fraction(...) for steel share; "
            "   remaining volume is cavity/insulation or air; add boards as needed.\n"
            "3) If the material is PURE, return a single ComponentShare with fraction=1.0 and stop.\n"
            "4) Fractions must sum to ~1.0 (±0.001). No extra prose; return a valid MaterialBreakdown.\n"
            "\n"
            "Do NOT guess ratios when a tool is available. Prefer mass basis for rebar lookups, convert carefully.\n"
            "Use concise canonical component names (e.g., 'Concrete', 'Rebar steel', 'Timber studs', 'Mineral wool', 'Air')."
        ),
        output_type=MaterialBreakdown,
        deps_type=DataTable,  # enable DI of the DataTable object into tools via the 'deps' parameter
        tools=[rebar_mass_fraction, density_lookup, studs_steel_volume_fraction]
    )
)


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%% LCA DATABASE EXTRACTION AGENTS %%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# ======== WEB_SCRAPING_AGENT  ========
# Identifies relevant data from a scraped HTML (refering to an online EPD)

WEB_SCRAPING_AGENT = load_agent(
    context=Context(
        instructions=(
            "placeholder"
        ),
        output_type="placeholder"
    )
)


# ======== INVENTORY AGENT ========
# Extracts relevant data fields from LCA databases.
# Fills in functions and use type that cannot be extracted through a script.

INVENTORY_AGENT = load_agent(
    context=Context(
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
)


# ======== SPECULATION AGENT ========
# Tries to fill in the blanks

SPECULATION_AGENT = load_agent(
    context=Context(
        instructions=(
            "placeholder"
        ),
        output_type="placeholder"
    )
)