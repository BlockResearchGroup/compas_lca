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

from compas_lca.helpers import load_json
from compas_lca.helpers import merge_llm_meta

from compas_lca.enums import EntryType

from compas_lca.llm.agent import BaseAgent
from compas_lca.llm.context import Context
from compas_lca.llm.ctx.extraction_context import ITEM_COMMON_CTX
from compas_lca.llm.ctx.extraction_context import ELEMENT_COMMON_CTX
from compas_lca.llm.ctx.extraction_context import MATERIAL_COMMON_CTX
from compas_lca.llm.ctx.extraction_context import COMPONENT_COMMON_CTX
from compas_lca.llm.ctx.speculation_context import ThicknessGuessResult

from compas_lca.maps import MAP_TO_ENTRY_TYPE
from compas_lca.maps import CTX_BY_COMP_TYPE
from compas_lca.maps import MODEL_BY_COMP_TYPE
from compas_lca.maps import CTX_BY_MAT_TYPE
from compas_lca.maps import MODEL_BY_MAT_TYPE

from compas_lca.matching_core.common import Common
from compas_lca.matching_core.material.common import MaterialCommon
from compas_lca.matching_core.component.common import ComponentCommon

from compas_lca.matching_core.material.core import assemble_material_core
from compas_lca.matching_core.component.core import assemble_component_core
from compas_lca.matching_core.core import assemble_matching_core
from compas_lca.matching_core.core import MatchingCore

from compas_lca.model.lca_element import LcaElement
from compas_lca.model.materialspec import MaterialSpec
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
    context: Context,
    output_dir: Optional[Path | str] = None,
    write_meta: bool = False,
    base_name: str = "input"
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

    # Optional write
    if output_dir is not None:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{base_name}.json"
        out_path.write_text(json.dumps(llm_output_dict, ensure_ascii=False, indent=2), encoding="utf-8")

        if write_meta:
            meta_dir = out_dir / "meta"
            meta_dir.mkdir(parents=True, exist_ok=True)  # <-- critical fix
            (meta_dir / f"{base_name}.json").write_text(
                json.dumps(meta_summary, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

        print(f"[OK] wrote {out_path}")

    return llm_output_dict, meta_summary


# ===================================================================
# Run a BaseAgent on a PDF input file and save its structured output
# ===================================================================

def extract_pdf_with_agent(*, input_data: Any, context: Any, output_dir: Optional[Path], write_meta: bool, base_name: str):
    raise NotImplementedError("PDF extraction is not implemented yet.")

# ===================================================================
# Run a BaseAgent on a TXT input file and save its structured output
# ===================================================================

def extract_txt_with_agent(*, input_data: Any, context: Any, output_dir: Optional[Path], write_meta: bool, base_name: str):
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

# Type alias for all extractor functions (JSON, PDF, TXT, etc.)
# Each extractor must return a tuple: (parsed_data_dict, optional_metadata_dict)
# This allows extract_matching_core() to treat all extractors interchangeably.
ExtractorFn = Callable[..., Tuple[dict, Optional[dict]]]


def extract_matching_core(
    *,
    input_type: Literal["inventory_item", "building_element"],
    input_data: Union[dict, str, bytes, Path],
    input_format: Literal["json", "pdf", "txt"] = "json",
    write_output: bool = False,
    write_meta: bool = False,
    output_dir: Optional[Path | str] = None,
    base_name: str = "input",
    force_entry_type: Optional[Literal["material", "component", "unknown"]] = None
) -> Tuple[MatchingCore, dict]:
    """
    Process input data (JSON/PDF/TXT) into a MatchingCore instance.
    Extracts information using the BaseAgent pipeline.

    Writes (when write_output=True):
    matchingcore_material/     -> {base_name}.json   (aggregated data for all passes)
    matchingcore_component/    -> {base_name}.json   (aggregated data for all passes)
    metadata/                  -> {base_name}.json   (AGGREGATED meta for all passes)

    Parameters
    ----------
    input_type : Literal[str]
        One of two options for what is being processed. Determines the instructions of
        the first pass (COMMON_CTX_ITEM vs. COMMON_CTX_ELEMENT)
    input_data : dict | str | bytes | Path
        In-memory payload (for JSON: dict or JSON string; for PDF/TXT later: raw bytes or Path).
    input_format : Literal["json", "pdf", "txt"]
        Selects the extractor pipeline. Only "json" is implemented right now.
    write_output : bool
        If True, write all agent outputs and the final MatchingCore to disk.
    write_meta : bool
        If True, also write AGGREGATED metadata JSON file (single flat object).
    output_dir : Path | str | None
        Directory for writing output JSONs (required if write_output=True).
        Ignored otherwise.
    base_name : str
        Base filename for all output JSON files (defaults to "input").
    force_entry_type : Optional[Literal["material", "component", "unknown"]]
        Force the first pass entry_type regardless of inference.

    Returns
    -------
    (MatchingCore, dict)
        The assembled MatchingCore and the AGGREGATED meta dict, matching the schema of
        extract_json_with_agent()'s meta_summary (e.g., model, duration_s, input_tokens, etc.).
    """
    # --- Validate arguments ---
    if write_output and output_dir is None:
        raise ValueError("If write_output=True, you must provide an output_dir.")
    if not write_output:
        output_dir = None

    # Normalize output_dir if provided
    if output_dir is not None:
        output_dir = Path(output_dir)
        # subdirectories for stages + metadata
        mc_dir_mat = output_dir / "matchingcore_material"
        mc_dir_comp = output_dir / "matchingcore_component"
        meta_dir = output_dir / "metadata"
        for d in (mc_dir_mat, mc_dir_comp, meta_dir):
            d.mkdir(parents=True, exist_ok=True)

    def _write_json(dirpath: Path, obj: dict) -> None:
        """Write JSON with consistent encoding/indent."""
        path = dirpath / f"{base_name}.json"
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

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
    else:
        COMMON_CTX = ELEMENT_COMMON_CTX

    # ----------------------
    # --- Pass 1: Common ---
    # ----------------------
    common_dict, common_meta = extractor(
        input_json=normalized_input,   # extractor expects 'input_json'
        context=COMMON_CTX,
        output_dir=None,
        write_meta=write_meta,
        base_name=base_name
    )
    if write_meta and common_meta:
        aggregated_meta = merge_llm_meta(aggregated_meta, common_meta)

    common = Common.model_validate(common_dict)
    if common.entry_type is None:
        raise ValueError("'entry_type' was not inferred (None). Expected 'material' or 'component'.")

    # Optionally enforce entry_type
    if force_entry_type is not None:
        try:
            forced = MAP_TO_ENTRY_TYPE[force_entry_type]
        except KeyError:
            raise ValueError("force_entry_type must be 'material', 'component', or 'unknown'.")
        common.entry_type = forced
        # Keep dict in sync if you ever write/log it
        common_dict["entry_type"] = forced.value if hasattr(forced, "value") else str(forced)

    # -------------------------------------
    # --- Pass 2: Entry-specific Common ---
    # -------------------------------------
    if common.entry_type == EntryType.material:
        ctx2, model2 = MATERIAL_COMMON_CTX, MaterialCommon
        etype_attr, ctx_map, model_map = "material_type", CTX_BY_MAT_TYPE, MODEL_BY_MAT_TYPE
    else:
        ctx2, model2 = COMPONENT_COMMON_CTX, ComponentCommon
        etype_attr, ctx_map, model_map = "component_type", CTX_BY_COMP_TYPE, MODEL_BY_COMP_TYPE

    spec_common_dict, spec_meta = extractor(
        input_json=normalized_input,
        context=ctx2,
        output_dir=None,
        write_meta=write_meta,
        base_name=base_name
    )
    if write_meta and spec_meta:
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

    # ---------------------
    # --- Pass 3: Facet ---
    # ---------------------
    if facet_ctx is not None:
        facet_dict, facet_meta = extractor(
            input_json=normalized_input,
            context=facet_ctx,
            output_dir=None,
            write_meta=write_meta,
            base_name=base_name
        )
        if write_meta and facet_meta:
            aggregated_meta = merge_llm_meta(aggregated_meta, facet_meta)
        # validate facet
        facet = facet_model.model_validate(facet_dict)

    # ------------------------
    # --- Assemble core(s) ---
    # ------------------------
    if common.entry_type == EntryType.material:
        material_core = assemble_material_core(specific_common, facet)
        matching_core = assemble_matching_core(common, material_core)
        if write_output and output_dir:
            _write_json(mc_dir_mat, matching_core.model_dump(mode="json"))
    else:
        component_core = assemble_component_core(specific_common, facet)
        matching_core = assemble_matching_core(common, component_core)
        if write_output and output_dir:
            _write_json(mc_dir_comp, matching_core.model_dump(mode="json"))

    # Optional: write AGGREGATED meta (flat schema identical to extract_json_with_agent)
    if write_output and write_meta and output_dir:
        _write_json(meta_dir, aggregated_meta)

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


def determine_multilayer(element: ElementRaw) -> Tuple[bool, Optional[bool], Optional[int]]:
    """
    Determine if element represents a multilayer element with DEFINED material layers.
    LLM is instructed to determine this, if it is IfcMaterialList for a window, and it
    specifies window frame -> this is not layered. for IfcMaterialList it only applies
    if the entity is an IfcRoof, IfcSlab, IfcFloor, or IfcWall, IfcWallStandardCase.
    (this will all be prompted).
    This is done with a BaseAgent (define BaseModel and typecheck with this later
    instead of Tuple[bool, Optional[bool], Optional[int]])
    Returns:
        - is_multilayer: bool
        - has_thickness: Optional[bool]
        - layer_count: Optional[int]
    """
    raise NotImplementedError

def guess_layer_thickness(element: ElementRaw) -> ThicknessGuessResult:
    raise NotImplementedError

def extract_material_spec(element: ElementRaw) -> MaterialSpec:
    """
    Extract raw building model element material specs and format into MaterialSpec object.
    """
    raise NotImplementedError

def extract_layer(element: ElementRaw, index) -> MaterialSpec:
    """
    Extract raw building model element individual material and format into LcaLayer object.
    The INDEX (i) will dynamically format the string in the LLM instruction and say which 
    layer number it must extract (index = len(layer_count)).
    Eventhough it extracts the same as extract_material_spec, the prompt must be dynamically
    altered (or the input must be dynamically altered), as the ElementRaw must be dissected
    into individual layers
    """
    # layer = extract_matching_core(layer)
    raise NotImplementedError

def extract_quantities(element: ElementRaw) -> Quantities:
    """
    Extract raw building model element quantities and format into Quantites object.
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



