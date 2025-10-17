from pathlib import Path

import json

from compas_lca.llm.agent import BaseAgent
from compas_lca.llm.context import Context
from compas_lca.llm.ctx.material_context import COMMON_CTX

from compas_lca.enums import InputFormat

from compas_lca.maps import CTX_BY_TYPE
from compas_lca.maps import MODEL_BY_TYPE

from compas_lca.material.common import MaterialCommon

from compas_lca.material.lca_material import LcaMaterial
from compas_lca.material.lca_material import assemble_lca_material


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

def to_lca_material(
    input_path: str | Path,
    output_dir: str | Path,
    write_output: bool = False,
    write_meta: bool = False,
    input_format: InputFormat = InputFormat.json
) -> LcaMaterial:
    """
    Process a single input file (json/pdf/txt) into an LcaMaterial instance.
    Extracts information  from any source describing a material with a BaseAgent.

    Args:
        input_path:     Path to input file
        output_dir:     Directory where the returned LcaMaterial should be saved
        write_output:   If True, serialize the LcaMaterial as JSON file (default: False)
        write_meta:     If True, write a separate metadata JSON file (default: False)
        input_format:   Specify input format ("json", "pdf", "txt")

    Pipeline:
      1) Run COMMON_CONTEXT with the selected extractor (by input_format)
      2) Inspect common.type (MaterialType)
      3) Run the matching facet context with the same extractor
      4) Assemble LcaMaterial(common, facet)
      5) Optionally write '<stem>_lca_material.json'
    """
    # allow passing a plain string like "PDF" or "pdf"
    if isinstance(input_format, str):
        try:
            input_format = InputFormat(input_format.lower())
        except ValueError as e:
            raise ValueError(f"Unsupported input_format '{input_format}'. "
                             f"Use one of: {[m.value for m in InputFormat]}") from e

    extractor = EXTRACTOR_BY_FORMAT.get(input_format)
    if extractor is None:
        raise ValueError(f"No extractor registered for input_format '{input_format.value}'.")

    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # PASS 1: MaterialCommon
    extractor(
        input_path=input_path,
        output_dir=output_dir,
        context=COMMON_CTX,
        write_meta=write_meta,
        suffix="_common"
    )

    # Read the common output for inferred material type
    common_out_path = output_dir / f"{input_path.stem}_common.json"
    with common_out_path.open("r", encoding="utf-8") as f:
        common_payload = json.load(f)
    common = MaterialCommon.model_validate(common_payload)
    type = common.material_type
    if type is None:
        raise ValueError("'material_type' was not inferred (None).")
    if type not in CTX_BY_TYPE or type not in MODEL_BY_TYPE:
        raise ValueError(
            f"No facet mapping defined for material type '{type}'. "
        )
    facet_ctx = CTX_BY_TYPE[type]
    facet_model = MODEL_BY_TYPE[type]

    # PASS 2: Facet matching the inferred type
    extractor(
        input_path=input_path,
        output_dir=output_dir,
        context=facet_ctx,
        write_meta=write_meta,
        suffix="_facet"
    )

    # Read the facet output 
    facet_out_path = output_dir / f"{input_path.stem}_facet.json"
    with facet_out_path.open("r", encoding="utf-8") as f:
        facet_payload = json.load(f)
    facet = facet_model.model_validate(facet_payload)

    # Assemble LcaMaterial instance
    lca_material = assemble_lca_material(common, facet)

    # Optional: persist the assembled result
    if write_output:
        material_path = output_dir / f"{input_path.stem}_lca_material.json" # note: perhaps the UUID instead?
        with material_path.open("w", encoding="utf-8") as f:
            json.dump(lca_material.model_dump(mode="json"), f, ensure_ascii=False, indent=2)
        print(f"[OK] wrote {material_path}")

    return lca_material