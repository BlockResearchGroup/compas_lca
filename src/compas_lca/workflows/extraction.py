from pathlib import Path

import json

from typing import Any
from typing import Callable
from typing import Dict
from typing import Literal
from typing import Mapping
from typing import Optional
from typing import Tuple
from typing import Union

from pydantic import Field

from compas_lca.helpers import load_json
from compas_lca.helpers import merge_llm_meta

from compas_lca.enums import EntryType

from compas_lca.llm.agent import BaseAgent
from compas_lca.llm.context import Context
from compas_lca.llm.ctx.extraction_context import ITEM_COMMON_CTX
from compas_lca.llm.ctx.extraction_context import ELEMENT_COMMON_CTX
from compas_lca.llm.ctx.extraction_context import LAYER_COMMON_CTX
from compas_lca.llm.ctx.extraction_context import MATERIAL_COMMON_CTX
from compas_lca.llm.ctx.extraction_context import MATERIAL_COMMON_LAYER_CTX
from compas_lca.llm.ctx.extraction_context import COMPONENT_COMMON_CTX

from compas_lca.maps import MAP_TO_ENTRY_TYPE
from compas_lca.maps import CTX_BY_COMP_TYPE
from compas_lca.maps import MODEL_BY_COMP_TYPE
from compas_lca.maps import CTX_BY_MAT_TYPE
from compas_lca.maps import MODEL_BY_MAT_TYPE

from compas_lca.matching_core.common import Common
from compas_lca.matching_core.material.common import MaterialCommon
from compas_lca.matching_core.component.common import ComponentCommon

from compas_lca.matching_core.core import assemble_matching_core
from compas_lca.matching_core.core import MatchingCore

from compas_lca.matching_core.material.core import assemble_material_core
from compas_lca.matching_core.component.core import assemble_component_core

from compas_lca.model.lca_element import LcaElement
from compas_lca.model.quantity import Quantities

from compas_lca.inventory.item import InventoryItem
from compas_lca.inventory.indicator import Indicators
from compas_lca.inventory.metadata import ItemMetadata
from compas_lca.inventory.reference import ReferenceInfo



#####################################################################
##########  ---------------------------------------------  ##########
##########            EXTRACT MATCHING CORE                ##########
##########  ---------------------------------------------  ##########
#####################################################################


def extract_json_with_agent(
    *,
    input_json: Union[dict, str],
    context: Context
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Run BaseAgent on an in-memory JSON payload (dict or JSON string).
    Optionally write the structured output + meta to disk.

    The output JSON will have the same name as base_name
    written to the specified output directory.

    Optionally, a separate '_meta' JSON file can be written containing
    run metadata and token usage.

    Args:
        input_json:  JSON payload
        output_dir:  Directory where output JSON should be saved
        context:     The agent context (choose from llm/ctx)
        write_meta:   If True, write a separate metadata JSON file (default: True)
    """
    
    # Normalize payload to JSON string
    raw_json = input_json if isinstance(input_json, str) else json.dumps(input_json, ensure_ascii=False, indent=2)

    # Run agent
    agent = BaseAgent.from_config(context=context)
    run = agent.execute_run(raw_json)
    llm_output_dict = run.result.output.model_dump(mode="json")

    # Meta summary
    meta_summary = run.metadata.summary()

    return llm_output_dict, meta_summary


# ===================================================================
# Run a BaseAgent on a PDF input file and save its structured output
# ===================================================================

def extract_pdf_with_agent(*, input_data: Any, context: Any):
    raise NotImplementedError("PDF extraction is not implemented yet.")

# ===================================================================
# Run a BaseAgent on a TXT input file and save its structured output
# ===================================================================

def extract_txt_with_agent(*, input_data: Any, context: Any):
    raise NotImplementedError("TXT extraction is not implemented yet.")


# ===================================================================
# Convert an input JSON, PDF, or TXT to an LcaMaterial Instance
# ===================================================================


# Different extractor selection for extract_matching_core coming up
EXTRACTOR_BY_FORMAT = {
    "json": extract_json_with_agent,
    "pdf":  extract_pdf_with_agent,
    "txt":  extract_txt_with_agent,
}

ExtractorFn = Callable[..., Tuple[dict, Optional[dict]]]


def extract_matching_core(
    *,
    input_type: Literal["inventory_item", "building_element", "layer"] = Field("building_element"), # requires different prompts / context
    input_data: Union[dict, str, bytes, Path],
    input_format: Literal["json", "pdf", "txt"] = "json",
    force_entry_type: Optional[Literal["material", "component", "unknown"]] = None
) -> Tuple[MatchingCore, dict]:
    """
    Process input data (JSON/PDF/TXT) into a MatchingCore instance.
    Extracts information using the BaseAgent pipeline.

    Parameters
    ----------
    input_type : Literal[str]
        One of two options for what is being processed. Determines the instructions of
        each pass (ITEM_COMMON_CONTEXT vs. ELEMENT_COMMON_CTX VS. LAYER_COMMON_CTX).
        "inventory_item": frames the instructions around EPD / LCA Database entries, etc.
        "building_element": reverts to building element data (extracted from IFC, 3DM, etc)
        "layer": references a single material layer of a multilayer element (for now only IFC and 
        has a special data schema that it references, i.e., "target_layer" vs. "element_context")
    input_data : dict | str | bytes | Path
        In-memory payload (for JSON: dict or JSON string; for PDF/TXT later: raw bytes or Path).
    input_format : Literal["json", "pdf", "txt"]
        Selects the extractor pipeline. Only "json" is implemented right now.
    force_entry_type : Optional[Literal["material", "component", "unknown"]]
        Force the first pass entry_type regardless of inference.

    Returns
    -------
    (MatchingCore, dict)
        The assembled MatchingCore and the AGGREGATED meta dict, matching the schema of
        extract_json_with_agent()'s meta_summary (e.g., model, duration_s, input_tokens, etc.).
    """

    # -------- Aggregated meta (flat schema) --------
    # Will be merged from each pass using merge_llm_meta()
    aggregated_meta: dict = {}

    # Pick extractor based on input_format
    try:
        extractor: ExtractorFn = EXTRACTOR_BY_FORMAT[input_format]
    except KeyError:
        raise ValueError(f"Unsupported input_format: {input_format!r}. Use one of {list(EXTRACTOR_BY_FORMAT)}.")

    # Normalize input for the selected format
    if input_format == "json":
        normalized_input = load_json(input_data)  # dict
    else:
        # For future formats we just pass through the raw data (bytes/Path/etc.)
        normalized_input = input_data

    # Choose the common context based on input_type
    if input_type == "inventory_item":
        COMMON_CTX = ITEM_COMMON_CTX
    elif input_type == "layer":
        COMMON_CTX = LAYER_COMMON_CTX
    else:
        COMMON_CTX = ELEMENT_COMMON_CTX

    # ----------------------
    # --- Pass 1: Common ---
    # ----------------------
    common_dict, common_meta = extractor(
        input_json=normalized_input,   # extractor expects 'input_json'
        context=COMMON_CTX
    )
    if common_meta:
        aggregated_meta = merge_llm_meta(aggregated_meta, common_meta)

    common = Common.model_validate(common_dict)

    if common.entry_type is None:
        raise ValueError("'entry_type' was not inferred (None). Expected 'material', 'component', or 'unknown'.")

    # Optionally enforce entry_type
    if force_entry_type is not None:
        try:
            forced = MAP_TO_ENTRY_TYPE[force_entry_type]
        except KeyError:
            raise ValueError("force_entry_type must be 'material', 'component', or 'unknown'.")
        common.entry_type = forced
        common_dict["entry_type"] = forced.value if hasattr(forced, "value") else str(forced)

    # -------------------------------------
    # --- Pass 2: Entry-specific Common ---
    # -------------------------------------
    if common.entry_type == EntryType.material:
        ctx2 = MATERIAL_COMMON_LAYER_CTX if input_type == "layer" else MATERIAL_COMMON_CTX
        model2 = MaterialCommon
        etype_attr, ctx_map, model_map = "material_type", CTX_BY_MAT_TYPE, MODEL_BY_MAT_TYPE

    elif common.entry_type == EntryType.component:
        ctx2, model2 = COMPONENT_COMMON_CTX, ComponentCommon
        etype_attr, ctx_map, model_map = "component_type", CTX_BY_COMP_TYPE, MODEL_BY_COMP_TYPE

    else:
        # EntryType.unknown (or any unhandled type) -> skip pass 2 and facets entirely
        ctx2 = None
        model2 = None
        etype_attr = None
        ctx_map = None
        model_map = None

    if ctx2 is not None and model2 is not None:

        spec_common_dict, spec_meta = extractor(
            input_json=normalized_input,
            context=ctx2
        )
        if spec_meta:
            aggregated_meta = merge_llm_meta(aggregated_meta, spec_meta)

        specific_common = model2.model_validate(spec_common_dict)

        etype = getattr(specific_common, etype_attr)
        name = getattr(etype, "value", getattr(etype, "name", str(etype)))

        # Determine facet context/model
        if name and isinstance(name, str) and name.lower() in {"unknown", "other"}:
            facet_ctx = None
            facet_model = None
            facet = {}
        elif etype not in ctx_map or etype not in model_map:
            facet_ctx = None
            facet_model = None
            facet = {}
        else:
            facet_ctx = ctx_map[etype]
            facet_model = model_map[etype]
            facet = None

    else:
        # Unknown entry type: no entry-specific common, no facet extraction
        specific_common = None
        facet_ctx = None
        facet_model = None
        facet = {}


    # ---------------------
    # --- Pass 3: Facet ---
    # ---------------------
    if facet_ctx is not None:
        facet_dict, facet_meta = extractor(
            input_json=normalized_input,
            context=facet_ctx
        )
        if facet_meta:
            aggregated_meta = merge_llm_meta(aggregated_meta, facet_meta)
        # validate facet
        facet = facet_model.model_validate(facet_dict)

    # ------------------------
    # --- Assemble core(s) ---
    # ------------------------
    if common.entry_type == EntryType.material:
        material_core = assemble_material_core(specific_common, facet)
        matching_core = assemble_matching_core(common, material_core)
    elif common.entry_type == EntryType.component:
        component_core = assemble_component_core(specific_common, facet)
        matching_core = assemble_matching_core(common, component_core)
    else:
        matching_core = assemble_matching_core(common, None)

    return matching_core, aggregated_meta


#####################################################################
##########  ---------------------------------------------  ##########
##########              EXTRACT LCA ELEMENT                ##########
##########  ---------------------------------------------  ##########
#####################################################################
"""
Universal extraction method for every output_schema related to InventoryItem
"""

# ==================================================================
# From Element
# ==================================================================


ElementRaw = Union[Mapping[str, Any], Any]  # dict-like or a source-specific object
ele_source = Literal["IFC", "3DM", "RVT"]


def extract_quantities(element: ElementRaw) -> Quantities:
    """
    Extract raw building model element quantities and format into Quantites object with Agent.
    """
    raise NotImplementedError


def extract_lca_element(element: ElementRaw) -> LcaElement:
    """
    Extract raw building model element data and format into LcaElement object.
    """
    raise NotImplementedError



#####################################################################
##########  ---------------------------------------------  ##########
##########           EXTRACT INVENTORY ITEM                ##########
##########  ---------------------------------------------  ##########
#####################################################################
"""
Universal extraction method for every output_schema related to InventoryItem
"""

EPDRaw = Union[Mapping[str, Any], Any]  # dict-like or a source-specific object, maybe PDF idk

def extract_indicators(epd: EPDRaw) -> Indicators:
    """
    Parse EPD impact indicators (e.g., GWP, ODP, etc.) and build an Indicators model.
    """
    raise NotImplementedError


def extract_reference(epd: EPDRaw) -> ReferenceInfo:
    """
    Return (reference_size, reference_unit) for the EPD's declared unit.
    Example return: (1, "m2") or (1, "kg").
    """
    raise NotImplementedError


def extract_metadata_item(epd: EPDRaw) -> Optional[ItemMetadata]:
    """
    Return the ItemMetadata for provenance/metadata (e.g., 'Ökobau.dat', 'KBOB', publisher, version).
    """
    raise NotImplementedError

def extract_inventory_item(epd: EPDRaw) -> InventoryItem:
    """
    Return the Assembled inventory item.
    """
    # Extract
    core = extract_matching_core(epd)
    indicators = extract_indicators(epd)
    reference = extract_reference(epd)
    source = extract_metadata_item(epd)

    # Assemble
    item = InventoryItem(
        item_core=core,
        indicators=indicators,
        reference=reference,
        source=source,
    )



