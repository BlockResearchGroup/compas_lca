from pathlib import Path

import json

from compas_lca.enums import InputFormat
from compas_lca.enums import EntryType

from compas_lca.llm.agent import BaseAgent
from compas_lca.llm.context import Context
from compas_lca.llm.ctx.extraction_context import COMMON_CTX
from compas_lca.llm.ctx.extraction_context import MATERIAL_COMMON_CTX
from compas_lca.llm.ctx.extraction_context import COMPONENT_COMMON_CTX

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

# ===================================================================
# Run a BaseAgent on a JSON input file and save its structured output
# ===================================================================

def extract_json_with_agent(
    input_path: str | Path,
    output_dir: str | Path,
    context: Context,
    write_meta: bool = True,
    *,
    suffix: str | None = None,
) -> None:
    """
    Run a BaseAgent on a JSON input file and save its structured output.

    The output JSON will have the same filename as the input,
    written to the specified output directory.

    Optionally, a separate '_meta' JSON file can be written containing
    run metadata and token usage.

    Args:
        input_path:  Path to input JSON file
        output_dir:  Directory where output JSON should be saved
        context:     The agent context (choose from llm/ctx)
        write_meta:   If True, write a separate metadata JSON file (default: True)
        suffix:      If specified, add a custom suffix for the output filename (before ".json")
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine output file paths
    if suffix:
        output_path = output_dir / f"{input_path.stem}{suffix}.json"
    else:
        output_path = output_dir / input_path.name
    meta_path = output_path.with_stem(output_path.stem + "_meta")

    # Load the input JSON
    with input_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    raw_json = json.dumps(payload, ensure_ascii=False, indent=2)

    # Initialize and run the agent
    agent = BaseAgent.from_config(context=context)
    run = agent.execute_run(raw_json)

    # Write structured output
    llm_output = run.result.output
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(llm_output.model_dump(mode="json"), f, ensure_ascii=False, indent=2)

    # Optionally write metadata
    meta = run.metadata
    usage = getattr(meta, "usage", None)
    meta_summary = {
        "model": meta.model,
        "duration_s": meta.duration_s,
        "input_tokens": getattr(usage, "input_tokens", None) if usage else None,
        "output_tokens": getattr(usage, "output_tokens", None) if usage else None,
        "currency": meta.currency,
        "total_cost": meta.total_cost,
    }

    if write_meta:
        with meta_path.open("w", encoding="utf-8") as f:
            json.dump(meta_summary, f, ensure_ascii=False, indent=2)

    # Print summary to console
    print(f"[OK] wrote {output_path}")


# ===================================================================
# Run a BaseAgent on a PDF input file and save its structured output
# ===================================================================

def extract_pdf_with_agent():
    pass

# ===================================================================
# Run a BaseAgent on a TXT input file and save its structured output
# ===================================================================

def extract_txt_with_agent():
    pass


# ===================================================================
# Convert an input JSON, PDF, or TXT to an LcaMaterial Instance
# ===================================================================

# Register extractors by format
EXTRACTOR_BY_FORMAT = {
    InputFormat.json: extract_json_with_agent,
    InputFormat.pdf:  extract_pdf_with_agent,
    InputFormat.txt:  extract_txt_with_agent,
}

def to_matching_core(
    input_path: str | Path,
    output_dir: str | Path,
    write_output: bool = False,
    write_meta: bool = False,
    input_format: InputFormat = InputFormat.json
) -> MatchingCore:
    """
    Process a single input file (json/pdf/txt) into a MatchingCore instance.
    Extracts information from any source describing a material or component with a BaseAgent.

    Args:
        input_path:     Path to input file
        output_dir:     Directory where the returned MatchingCore should be saved
        write_output:   If True, serialize the MatchingCore as JSON file (default: False)
        write_meta:     If True, write a separate metadata JSON file (default: False)
        input_format:   Specify input format ("json", "pdf", "txt")

    Pipeline:
        Pass 1: Run the generic COMMON context to infer `entry_type` (material|component) and shared fields (-> Common)
        Pass 2: Run the entry-specific common context (-> MaterialCommon or ComponentCommon)
        Pass 3: Run the facet context based on type (-> corresponding Facet)
    """
    # allow passing a plain string like "PDF" or "pdf"
    if isinstance(input_format, str):
        try:
            input_format = InputFormat(input_format.lower())
        except ValueError as e:
            raise ValueError(
                f"Unsupported input_format '{input_format}'. Use one of: {[m.value for m in InputFormat]}"
            ) from e

    extractor = EXTRACTOR_BY_FORMAT.get(input_format)
    if extractor is None:
        raise ValueError(f"No extractor registered for input_format '{input_format.value}'.")

    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ----------------------
    # PASS 1: Generic Common
    # ----------------------
    extractor(
        input_path=input_path,
        output_dir=output_dir,
        context=COMMON_CTX,
        write_meta=write_meta,
        suffix="_common"
    )
    common_out_path = output_dir / f"{input_path.stem}_common.json"
    with common_out_path.open("r", encoding="utf-8") as f:
        common_payload = json.load(f)
    common = Common.model_validate(common_payload)

    if common.entry_type is None:
        raise ValueError("'entry_type' was not inferred (None). Expected 'material' or 'component'.")

    # -----------------
    # PASS 2: Entry-specific Common
    # -----------------
    if common.entry_type == EntryType.material:
        extractor(
            input_path=input_path,
            output_dir=output_dir,
            context=MATERIAL_COMMON_CTX,
            write_meta=write_meta,
            suffix="_material_common",
        )
        spec_common_out = output_dir / f"{input_path.stem}_material_common.json"
        with spec_common_out.open("r", encoding="utf-8") as f:
            spec_common_payload = json.load(f)
        specific_common = MaterialCommon.model_validate(spec_common_payload)

        mtype = specific_common.material_type
        name = getattr(mtype, "value", getattr(mtype, "name", str(mtype)))
        if name.lower() in {"unknown", "other"} or \
        mtype not in CTX_BY_MAT_TYPE or mtype not in MODEL_BY_MAT_TYPE:
            facet_ctx = None
            facet_model = None
            facet = {}        # we'll just use this below
        else:
            facet_ctx = CTX_BY_MAT_TYPE[mtype]
            facet_model = MODEL_BY_MAT_TYPE[mtype]
            facet = None

    elif common.entry_type == EntryType.component:
        extractor(
            input_path=input_path,
            output_dir=output_dir,
            context=COMPONENT_COMMON_CTX,
            write_meta=write_meta,
            suffix="_component_common",
        )
        spec_common_out = output_dir / f"{input_path.stem}_component_common.json"
        with spec_common_out.open("r", encoding="utf-8") as f:
            spec_common_payload = json.load(f)
        specific_common = ComponentCommon.model_validate(spec_common_payload)

        ctype = specific_common.component_type
        name = getattr(ctype, "value", getattr(ctype, "name", str(ctype)))
        if name.lower() in {"unknown", "other"} or \
        ctype not in CTX_BY_COMP_TYPE or ctype not in MODEL_BY_COMP_TYPE:
            facet_ctx = None
            facet_model = None
            facet = {}        # just skip facet extraction
        else:
            facet_ctx = CTX_BY_COMP_TYPE[ctype]
            facet_model = MODEL_BY_COMP_TYPE[ctype]
            facet = None

    else:
        raise ValueError(f"Unsupported entry_type '{common.entry_type}'.")

    # -----------------
    # PASS 3: Facet
    # -----------------
    if facet_ctx is not None:
        extractor(
            input_path=input_path,
            output_dir=output_dir,
            context=facet_ctx,
            write_meta=write_meta,
            suffix="_facet",
        )
        facet_out_path = output_dir / f"{input_path.stem}_facet.json"
        with facet_out_path.open("r", encoding="utf-8") as f:
            facet_payload = json.load(f)
        facet = facet_model.model_validate(facet_payload)
    else:
        # Skip Pass 3 for unknown/other → facet already {}
        pass

    # -----------------
    # Assemble cores
    # -----------------
    if common.entry_type == EntryType.material:
        material_core = assemble_material_core(specific_common, facet)
        matching_core = assemble_matching_core(common, material_core)
        out_name = f"{input_path.stem}_matching_core_material.json"
    else:
        component_core = assemble_component_core(specific_common, facet)
        matching_core = assemble_matching_core(common, component_core)
        out_name = f"{input_path.stem}_matching_core_component.json"

    # Optional: persist final MatchingCore
    if write_output:
        core_path = output_dir / out_name
        with core_path.open("w", encoding="utf-8") as f:
            json.dump(matching_core.model_dump(mode="json"), f, ensure_ascii=False, indent=2)
        print(f"[OK] wrote {core_path}")

    return matching_core