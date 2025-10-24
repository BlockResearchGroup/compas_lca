from compas_lca.model.metadata import ElementMetadata
from compas_lca.model.quantity import Quantity

from compas_lca.llm.context import Context

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
    output_type=ElementMetadata
)

QUANTITY_CTX = Context(
    instructions=(
        "placeholder"
    ),
    output_type=Quantity,
)