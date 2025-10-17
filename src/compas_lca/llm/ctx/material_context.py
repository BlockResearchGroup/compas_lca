from compas_lca.llm.context import Context

from compas_lca.material.common import MaterialCommon
from compas_lca.material.bituminous import BituminousFacet
from compas_lca.material.composite import CompositeFacet
from compas_lca.material.concrete import ConcreteFacet
from compas_lca.material.ligneous import LigneousFacet
from compas_lca.material.metallic import MetallicFacet
from compas_lca.material.mineral import MineralFacet
from compas_lca.material.polymeric import PolymericFacet

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%% LCA MATERIAL EXTRACTION CONTEXT %%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

COMMON_CTX = Context(
    instructions=(
        "You are an expert at extracting important data from a dataset describing a material."
        "This dataset is either a single JSON string, a PDF file, or a TXT file."
        "Your task is to carefully EXTRACT all relevant information and populate the fields of the output schema."
        "For each field in the schema, locate the corresponding value in input dataset."
        "Only add values in the output schema if they are explicitly present."
        "If a field is missing or cannot be determined, leave the default value. Do not invent or assume values."
        "Do not include any explanatory text outside of the schema output."
    ),
    output_type=MaterialCommon
)

BITUMINOUS_CTX = Context(
    instructions=(
        "You are an expert at extracting important bituminous-related data from a dataset describing a bituminous material."
        "This dataset is either a single JSON string, a PDF file, or a TXT file."
        "Your task is to carefully EXTRACT all relevant information and populate the fields of the output schema."
        "For each field in the schema, locate the corresponding value in input dataset."
        "Only add values in the output schema if they are explicitly present."
        "If a field is missing or cannot be determined, leave the default value. Do not invent or assume values."
        "Do not include any explanatory text outside of the schema output."
    ),
    output_type=BituminousFacet
)

COMPOSITE_CTX = Context(
    instructions=(
        "You are an expert at extracting important composite-related data from a dataset describing a composite material."
        "This dataset is either a single JSON string, a PDF file, or a TXT file."
        "Your task is to carefully EXTRACT all relevant information and populate the fields of the output schema."
        "For each field in the schema, locate the corresponding value in input dataset."
        "Only add values in the output schema if they are explicitly present."
        "If a field is missing or cannot be determined, leave the default value. Do not invent or assume values."
        "Do not include any explanatory text outside of the schema output."
    ),
    output_type=CompositeFacet
)

CONCRETE_CTX = Context(
    instructions=(
        "You are an expert at extracting important concrete-related data from a dataset describing a concrete material."
        "This dataset is either a single JSON string, a PDF file, or a TXT file."
        "Your task is to carefully EXTRACT all relevant information and populate the fields of the output schema."
        "For each field in the schema, locate the corresponding value in input dataset."
        "Only add values in the output schema if they are explicitly present."
        "If a field is missing or cannot be determined, leave the default value. Do not invent or assume values."
        "Do not include any explanatory text outside of the schema output."
    ),
    output_type=ConcreteFacet
)

LIGNEOUS_CTX = Context(
    instructions=(
        "You are an expert at extracting important ligneous-related data from a dataset describing a ligneous material."
        "This dataset is either a single JSON string, a PDF file, or a TXT file."
        "Your task is to carefully EXTRACT all relevant information and populate the fields of the output schema."
        "For each field in the schema, locate the corresponding value in input dataset."
        "Only add values in the output schema if they are explicitly present."
        "If a field is missing or cannot be determined, leave the default value. Do not invent or assume values."
        "Do not include any explanatory text outside of the schema output."
    ),
    output_type=LigneousFacet
)

METALLIC_CTX = Context(
    instructions=(
        "You are an expert at extracting important metallic-related data from a dataset describing a metallic material."
        "This dataset is either a single JSON string, a PDF file, or a TXT file."
        "Your task is to carefully EXTRACT all relevant information and populate the fields of the output schema."
        "For each field in the schema, locate the corresponding value in input dataset."
        "Only add values in the output schema if they are explicitly present."
        "If a field is missing or cannot be determined, leave the default value. Do not invent or assume values."
        "Do not include any explanatory text outside of the schema output."
    ),
    output_type=MetallicFacet
)

MINERAL_CTX = Context(
    instructions=(
        "You are an expert at extracting important meineralic-related data from a dataset describing a mineral material."
        "This dataset is either a single JSON string, a PDF file, or a TXT file."
        "Your task is to carefully EXTRACT all relevant information and populate the fields of the output schema."
        "For each field in the schema, locate the corresponding value in input dataset."
        "Only add values in the output schema if they are explicitly present."
        "If a field is missing or cannot be determined, leave the default value. Do not invent or assume values."
        "Do not include any explanatory text outside of the schema output."
    ),
    output_type=MineralFacet
)

POLYMERIC_CTX = Context(
    instructions=(
        "You are an expert at extracting important polymeric-related data from a dataset describing a polymeric material."
        "This dataset is either a single JSON string, a PDF file, or a TXT file."
        "Your task is to carefully EXTRACT all relevant information and populate the fields of the output schema."
        "For each field in the schema, locate the corresponding value in input dataset."
        "Only add values in the output schema if they are explicitly present."
        "If a field is missing or cannot be determined, leave the default value. Do not invent or assume values."
        "Do not include any explanatory text outside of the schema output."
    ),
    output_type=PolymericFacet
)
