### DRAFT ###

from compas_lca.llm.context import Context

from compas_lca.llm.tools import RebarTable
from compas_lca.llm.tools import RebarRatio
from compas_lca.llm.tools import rebar_ratio_lookup


# ======== MATERIAL DECOMPOSITION CONTEXT ========
# Agents for Material Decomposition of common composites
# More agents to come, for now only rebar

DECOMPOSE_REBAR_PROMPT = """
Identify the reinforced-concrete building component mentioned by the user and
return the **minimum** and **maximum** rebar ratios (m3/m3) for that component.
Use the `rebar_ratio_lookup` tool to fetch values from the in-project CSV.
If the wording is a close variant (e.g., 'retaining wall' vs 'retaining walls'),
pick the closest match. The output MUST conform to the RebarRatio schema.
"""

DECOMPOSE_REBAR_CTX = Context(
    instructions=DECOMPOSE_REBAR_PROMPT,
    output_type=RebarRatio,
    tool_resources_type=RebarTable,
    tools=[rebar_ratio_lookup]
)