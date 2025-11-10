
from compas_lca.model.descriptor import ElementDescriptor
from compas_lca.model.quantity import Quantity

from compas_lca.llm.context import Context

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%% ELEMENT EXTRACTION CONTEXT %%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


DESCRIPTOR_PROMPT = """
You are an expert at extracting important descriptive data from building element data.
You are given raw building element data as a single JSON string.
Your task is to carefully EXTRACT all relevant information from this JSON and populate the fields of the `ElementDescriptor` output schema.
For each field in the schema, locate the corresponding value in the JSON.
Only add values in the output schema if they are explicitly present.
If a field is missing or cannot be determined, mark is with `null`. Do not invent or assume values.
Do not include any explanatory text outside of the schema output.
"""

DESCRIPTOR_CTX = Context(
    instructions=DESCRIPTOR_PROMPT,
    output_type=ElementDescriptor
)

"""
This is only relevant if the agent needs to extract
quantities from unorganized building element data.
If it can be calculated with COMPAS, or if it can be
extracted through a script, it should always be preferred.
"""
QUANTITY_CTX = Context(
    instructions=(
        "placeholder"
    ),
    output_type=Quantity,
)