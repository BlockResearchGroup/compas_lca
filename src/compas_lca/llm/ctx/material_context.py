from compas_lca.llm.context import Context

from compas_lca.material.data_kind import DataKind
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


MATERIAL_OR_COMPONENT_CTX = Context(
    instructions=(
        "You are an expert at classifying an EPD or a building-related dataset as MATERIAL, COMPONENT, or UNKNOWN.\n"
        "\n"
        "INPUT may be a JSON string, PDF text, or TXT. Read it carefully. Return ONLY the JSON for the output schema—no extra text.\n"
        "\n"
        "DEFINITIONS\n"
        "- MATERIAL: A single homogeneous substance or a uniform material layer defined by its physical/chemical nature rather than its assembly or function. It is an input to components/structures and lacks distinct sub-parts/interfaces. It fits a material family: mineral, metallic, polymeric, bituminous, ligneous, or composite. Integrated composites (e.g., reinforced concrete, WPC, fiber-cement, plywood) are MATERIALS.\n"
        "- COMPONENT: A manufactured/constructed assembly that combines multiple materials or sub-parts into one functional building element; usually installable as a unit. Examples: window unit, door unit, curtain-wall module, shading device assembly, ceiling system (tiles+grid), HVAC system, lighting fixture, solar panel.\n"
        "\n"
        "DECISION CRITERIA (apply in order):\n"
        "1) If the dataset clearly represents an installable assembly or a system-level product (mentions unit/device/system/module, includes multiple distinct materials/parts, or a building-level function like closing an opening, distributing services) → COMPONENT.\n"
        "2) Else, if it represents a single material or a uniform material layer (homogeneous or an integrated composite; no distinct separable parts/interfaces) → MATERIAL.\n"
        "3) If information is insufficient or contradictory → UNKNOWN.\n"
        "\n"
        "CLARIFICATIONS\n"
        "- Reinforced concrete modeled as a material layer is a MATERIAL (may be mechanically composite and later disaggregated for LCA, but it is not a system/assembly).\n"
        "- Items named as '<something> system', 'unit', 'module', 'device', or that group frame+glazing+hardware, tiles+grid, casing+driver, etc. → typically COMPONENT.\n"
        "- If the dataset is a wall/roof/partition 'assembly' without explicit layer breakdown → COMPONENT. If it is a single explicit layer (e.g., 'metal stud layer', 'mineral wool layer') → MATERIAL.\n"
        "\n"
        "OUTPUT RULES\n"
        "- Populate the output schema fields strictly.\n"
        "- 'rationale' must be one concise sentence.\n"
        "- 'evidence' is a list of exact strings/fields copied from the input that support the decision (e.g., product names, material lists, phrases like 'unit', 'system', 'frame+glass').\n"
        "- If uncertain, choose 'unknown' and say why.\n"
    ),
    output_type=DataKind,
)

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
