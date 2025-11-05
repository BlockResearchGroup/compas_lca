from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from compas_lca.llm.context import Context

# ======== THICKNESS-GUESS CONTEXT ========
"""
This is the output schema for an Agent if there are clear material names
present in a building element, and if there is a total thickness present
(i.e., property set thickness, or smalles OBB dimension). Then it needs to
infer the thicknesses of each layer and reason.
"""
class LayerGuess(BaseModel):
    """Represents a guessed thickness for one material layer."""
    layer_number: int = Field(..., description="Position in the buildup (1 = topmost layer)")
    layer_name: str = Field(..., description="Material or product name of this layer")
    inferred_thickness_mm: float = Field(..., ge=0, description="Guessed thickness in millimetres")


class ThicknessGuessResult(BaseModel):
    """Structured LLM output: total + per-layer guessed thicknesses."""
    element_name: Optional[str] = Field(
        None, description="Name or identifier of the IFC element"
    )
    element_type: Optional[str] = Field(
        None, description="Element category (wall, slab, roof, etc.)"
    )
    total_thickness_mm: float = Field(
        ..., ge=0, description="Total element thickness used or inferred (mm)"
    )
    reasoning: Optional[str] = Field(
        None, description="Short textual explanation of how thicknesses were inferred"
    )
    layers: List[LayerGuess] = Field(
        ..., description="List of layers with inferred thicknesses (top to bottom)"
    )


THICKNESS_GUESS_CTX = Context(
    instructions=(
        "You are a building-physics reasoning assistant specialized in IFC data. "
        "Your task is to estimate per-layer thicknesses for an IfcBuildingElement that lists materials "
        "but does not provide individual layer thicknesses. "
        "Use all information provided in the JSON — including metadata, materials, properties, and quantities — "
        "to make an educated and physically plausible guess.\n\n"

        "Guidelines:\n"
        "- If a total thickness is available (e.g., in 'Thickness' or 'Construction.Default Thickness'), "
        "use it as the total thickness for the buildup.\n"
        "- If total thickness is missing, take the SMALLEST OBB dimension (e.g., obb_x, obb_y, or obb_z) "
        "- Distribute the total thickness across layers proportionally to realistic construction logic: "
        "finishes and coatings are thinner, insulation and structure are thicker.\n"
        "- Include every layer or material in 'material_data.materials' (or 'material_layers' if present).\n"
        "- All thickness values must be given in millimetres.\n"
        "- Number layers from top to bottom (1 = topmost layer).\n"
        "- The sum of all inferred layer thicknesses should approximately equal the total thickness.\n"
        "- Add a concise reasoning field (1-2 sentences) summarizing your logic.\n\n"

        "You must output a 'ThicknessGuessResult' object that strictly follows this schema:\n"
        "{\n"
        '  "element_name": "string",\n'
        '  "element_type": "string",\n'
        '  "total_thickness_mm": "float",\n'
        '  "reasoning": "string",\n'
        '  "layers": [\n'
        '    {\n'
        '      "layer_number": "integer (1=top)",\n'
        '      "layer_name": "string",\n'
        '      "inferred_thickness_mm": "float"\n'
        '    }\n'
        '  ]\n'
        "}\n\n"

        "Return only valid JSON matching this schema. Do not include explanations outside the JSON."
    ),
    output_type=ThicknessGuessResult
)


# ======== SPECULATION CONTEXT ========
# Tries to fill in the blanks

SPECULATION_CTX = Context(
    instructions=(
        "placeholder"
    ),
    output_type="placeholder"
)
