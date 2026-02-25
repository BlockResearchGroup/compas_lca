from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from compas_lca.llm.context import Context

from compas_lca.enums import ConcreteStrength

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


# ======== CONCRETE ENRICHMENT ========

class ConcreteStrengthResult(BaseModel):
    strength_class: ConcreteStrength = Field(
        ...,
        description="Inferred EN 206 / EN 1992-1-1 compressive strength class. Must be one of the ConcreteStrength enum values."
    )
    explanation: str = Field(
        ...,
        description="1–3 sentences explaining the cues (element type, exposure, loadbearing, thickness) and how rules were applied."
    )

CONCRETE_STRENGTH_PROMPT = """
You infer a reasonable EN 206 / EN 1992-1-1 concrete compressive strength class for a building element, even if not explicitly stated.

You MUST produce structured output matching the schema:
- strength_class: one of ConcreteStrength enum values
- explanation: 1-3 sentences (no bullet lists, no long text)
(If confidence field exists, fill it too.)

Hard constraints:
- strength_class must be exactly one of:
  C8/10, C12/15, C16/20, C20/25, C25/30, C30/37, C35/45, C40/50, C45/55, C50/60, C55/67, C60/75, C80/95
- Never output a class above C40/50 unless the JSON explicitly states a higher class.
  If you would choose above C40/50 based on inference alone, return C40/50.

Procedure:
1) Extract cues from JSON:
   - element type/category: metadata.entity, metadata.name, metadata.object_type
   - structural role: LoadBearing, Structural Usage, Function
   - exposure/durability hints: IsExternal, "Foundation"/"Footing"/"Retaining"/"Basement"/"Subgrade"
   - geometry: material layer thickness and/or Width (mm or m)

2) Assign one bucket:
   A Non-structural (finishes/screed/thin topping)
   B Internal structural wall/slab (not foundation)
   C External structural above-grade (weather exposure)
   D Below-grade / foundation / retaining / ground-contact
   E Primary highly-loaded (columns, transfer beams, long spans) if indicated

3) Choose base class:
   A -> C16/20 (or C12/15 if clearly lean/mass fill)
   B -> C25/30
   C -> C30/37
   D -> C30/37
   E -> C35/45

4) Adjust by at most ±1 step unless there is strong evidence:
   - thickness < 120mm and non-structural -> down 1 step
   - thickness 150-250mm and structural -> keep base
   - thickness > 300mm and (LoadBearing=True or retaining/basement cues) -> up 1 step
   - foundation/footing/retaining/basement/subgrade implies minimum C30/37
   - generic “Concrete - Cast In Situ” alone is not enough to go above C30/37

Step ladder:
C8/10 -> C12/15 -> C16/20 -> C20/25 -> C25/30 -> C30/37 -> C35/45 -> C40/50 -> C45/55 -> C50/60 -> C55/67 -> C60/75 -> C80/95

Explain briefly which cues drove the bucket and any adjustment.
"""

CONCRETE_STRENGTH_CTX = Context(
    instructions=CONCRETE_STRENGTH_PROMPT,
    output_type=ConcreteStrengthResult,
)

REINFORCEMENT_RATIO_CTX = Context(
    instructions=(
        "placeholder"
    ),
    output_type=LayerGuess, # PLACEHOLDER , should be a ReinforcementRatio class with float (ratio), tool to be implemented
)

# ======== CAVITY ENRICHMENT ========
# for stud layers, railings, gratings, etc. (to fix quantities basically)

class StudRatioResult(BaseModel):
    stud_ratio: float = Field(
        ...,
        description="Inferred volumetric ratio of STUD material in a stud layer (i.e., fraction of timber or metal volume within the stud layer volume). Must be one of [0.08, 0.10, 0.12, 0.15, 0.18, 0.22, 0.25]."
    )
    explanation: str = Field(
        ...,
        description="1-3 sentences explaining the cues (element type, exposure, loadbearing, thickness) and how rules were applied."
    )

STUD_RATIO_PROMPT = """
You infer a reasonable volumetric ratio of STUD material in a stud layer
(i.e., fraction of timber or metal volume within the stud layer volume),
even if not explicitly stated.

You MUST produce structured output matching the schema:
- stud_ratio: exactly one of [0.08, 0.10, 0.12, 0.15, 0.18, 0.22, 0.25]
- explanation: 1-3 sentences (no bullet lists, no long text)

General meaning of levels (reference only, do not output this section):
  0.08 → very light framing (wide spacing, minimal plates)
  0.10 → light non-load-bearing partition
  0.12 → typical internal partition
  0.15 → typical load-bearing residential wall
  0.18 → dense load-bearing or 400 mm spacing
  0.22 → structural/shear wall with added framing
  0.25 → very dense / double stud configuration

Procedure:

1) Extract cues from JSON:
   - IsLoadBearing
   - IsExternal
   - ShearWall / Bracing / StructuralWall indication
   - spacing (if stated)
   - stud layer thickness (proxy for stud depth)
   - explicit wording like "double stud", "dense framing", "acoustic double wall"
   - presence of many openings

2) Assign framing category:

   A Light non-structural partition
      → 0.10
   B Standard internal partition (timber stud wall, no structural hints)
      → 0.12
   C Load-bearing residential wall (internal or external)
      → 0.15
   D Dense structural wall (400 mm spacing, bracing wall, shear wall)
      → 0.18
   E Heavy structural / highly detailed framing
      → 0.22
   F Explicit double stud or ≤300 mm spacing
      → 0.25

3) Sanity bounds:

   - Typical modern residential walls should land between 0.12 and 0.18.
   - Do not assume dense framing without explicit indication.
   - If uncertain, choose the more conservative (lower) plausible value.

Explain briefly which cues determined the category.
"""

STUD_RATIO_CTX = Context(
    instructions=STUD_RATIO_PROMPT,
    output_type=StudRatioResult,
)


# ======== WOOD ENRICHMENT ========
# If certain wood can be used interior or exterior
ENRICH_WOOD_PLACEMENT = Context(
    instructions=(
        "placeholder"
    ),
    output_type=LayerGuess, # # enum, use tool
)

# If certain wood is used for loadbearing or non-loadbearing
ENRICH_WOOD_STRUCTURAL = Context(
    instructions=(
        "placeholder"
    ),
    output_type=LayerGuess, # # enum, use tool
)

# ======== METALLIC ENRICHMENT ========

# Often generic "metal" descriptor refers to carbon steel
# Help give context when generic "metal" should be carbon steel and not "unknown"
ENRICH_CARBON_STEEL = Context(
    instructions=(
        "placeholder"
    ),
    output_type=LayerGuess, # bool, use tool (or maybe only additional context in instruction prompt)
)
