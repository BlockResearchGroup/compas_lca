from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.model.descriptor import ElementDescriptor
from compas_lca.model.quantity import Quantity

from compas_lca.llm.context import Context

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%% ELEMENT EXTRACTION CONTEXT %%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

class MultilayerBool(BaseModel):
    """
    Bool for whether an element is a layered construction or not.
    """
    model_config = ConfigDict(
        extra = "forbid",           # Forbid extra fields
        validate_assignment=True,   # Validate fields on assignment
        str_strip_whitespace=True   # Strips leading and trailing whitespace for str types
    )
    is_multilayer: bool = Field(
        False,
        description="""
        Boolean flag indicating whether the element represents a **layered construction**.

        Set to **True** if:
        - The element's material composition includes **two or more distinct material layers** 
        that are implied to be **physically adjacent** and form an **ordered stack or sequence** (e.g., interior → insulation → exterior finish), **or**
        - The element is a **wall, roof, slab, floor, or ceiling** and has an **IfcMaterialList** with **two or more materials**
        (treated as a layered build-up by default), **or**
        - Each layer either has an explicitly defined numeric thickness **or** a clearly implied relative position/thickness
        within the build-up.

        Set to **False** if:
        - The element consists of a single material, or of multiple materials that are **integrated/fused/mixed** rather than layered.
        - Typical non-layered examples: **windows, doors, columns, beams, frames, trusses, pipes, mechanical equipment**.

        In summary, this flag is **True only when the materials are explicitly or implicitly layered in sequence**, forming a stratified composition.
        """,
        examples=[True, False]
    )

MULTILAYER_PROMPT = """
You are an expert at determining if a building elelment represents a layered construction or not, based on its material composition and metadata.
"""

MULTILAYER_CTX = Context(
    instructions=MULTILAYER_PROMPT,
    output_type=MultilayerBool
)





DESCRIPTOR_PROMPT = """
You are an expert at extracting important descriptive data from building element data.
You are given raw building element data as a single JSON string.
Your task is to carefully EXTRACT all relevant information from this JSON and populate the fields of the `ElementDescriptor` output schema.
For each field in the schema, locate the corresponding value in the JSON.
Only add values in the output schema if they are explicitly present.
If a field is missing or cannot be determined, mark is with `null`. Do not invent or assume values.
Do not include any explanatory text outside of the schema output.
"""

DESCRIPTOR_CTX = Context(
    instructions=DESCRIPTOR_PROMPT,
    output_type=ElementDescriptor
)

"""
This is only relevant if the agent needs to extract
quantities from unorganized building element data.
If it can be calculated with COMPAS, or if it can be
extracted through a script, it should always be preferred.
"""
QUANTITY_CTX = Context(
    instructions=(
        "placeholder"
    ),
    output_type=Quantity,
)