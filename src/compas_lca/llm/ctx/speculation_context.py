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


THICKNESS_GUESS_PROMPT = """
You are a building-physics reasoning assistant specialized in IFC data.
Your task is to estimate per-layer thicknesses for an IfcBuildingElement that lists materials
but does not provide individual layer thicknesses.
Use all information provided in the JSON — including metadata, materials, properties, and quantities —
to make an educated and physically plausible guess.

Guidelines:
- If a total thickness is available (e.g., in 'Thickness' or 'Construction.Default Thickness'),
  use it as the total thickness for the buildup.
- If total thickness is missing, take the SMALLEST OBB dimension (e.g., obb_x, obb_y, or obb_z).
- Distribute the total thickness across layers proportionally to realistic construction logic:
  finishes and coatings are thinner, insulation and structure are thicker.
- Include every layer or material in 'material_data.materials' (or 'material_layers' if present).
- All thickness values must be given in millimetres.
- Number layers from top to bottom (1 = topmost layer).
- The sum of all inferred layer thicknesses should approximately equal the total thickness.
- Add a concise reasoning field (1-2 sentences) summarizing your logic.

You must output a 'ThicknessGuessResult' object that strictly follows this schema:
{
  "element_name": "string",
  "element_type": "string",
  "total_thickness_mm": "float",
  "reasoning": "string",
  "layers": [
    {
      "layer_number": "integer (1=top)",
      "layer_name": "string",
      "inferred_thickness_mm": "float"
    }
  ]
}
Return only valid JSON matching this schema. Do not include explanations outside the JSON.
"""

THICKNESS_GUESS_CTX = Context(
    instructions=THICKNESS_GUESS_PROMPT,
    output_type=ThicknessGuessResult
)

# ======== CONCRETE SPECULATION ========
"""
Just some notes: a concrete attribute speculation agent from the building
element side would be nice. for instance, if IFC data has a
concrete descriptor, but doesnt specify the strength class, then
it might be good to take an educated guess. A generic slab will have enough
compressive strength if the concrete is C20/25, and anything above would be overkill.
Therefore it might be good to specifically instruct an agent to fill in the blanks

-> Should be applied to other material facets aswell.
"""