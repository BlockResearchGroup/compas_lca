from pathlib import Path

from typing import Callable
from typing import Literal
from typing import Optional
from typing import Tuple
from typing import Union

from compas_lca.helpers import load_json

from compas_lca.workflows.extraction import extract_json_with_agent
from compas_lca.workflows.extraction import extract_pdf_with_agent
from compas_lca.workflows.extraction import extract_txt_with_agent

from compas_lca.llm.ctx.speculation_context import ThicknessGuessResult
from compas_lca.llm.ctx.speculation_context import THICKNESS_GUESS_CTX

# ===============================================================================
# Initialize
# ===============================================================================

# Different extractor selection
EXTRACTOR_BY_FORMAT = {
    "json": extract_json_with_agent,
    "pdf":  extract_pdf_with_agent,
    "txt":  extract_txt_with_agent,
}

ExtractorFn = Callable[..., Tuple[dict, Optional[dict]]]

# ===============================================================================
# Guess the thicknesses of a multilayer element with no defined individual layers
# ===============================================================================

def speculate_layer_thicknesses(
    *,
    input_data: Union[dict, str, bytes, Path],
    input_format: Literal["json", "pdf", "txt"] = "json",     
    base_name: str = "input"
) -> Tuple[ThicknessGuessResult, dict]:
    
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

    llm_output_dict, llm_meta = extractor(
        input_json=normalized_input,   # extractor expects 'input_json'
        context=THICKNESS_GUESS_CTX,
        base_name=base_name
    )

    thickness_result = ThicknessGuessResult.model_validate(llm_output_dict)

    return thickness_result, llm_meta