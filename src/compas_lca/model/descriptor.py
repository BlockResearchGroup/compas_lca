from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ElementDescriptor(BaseModel):
    """
    Descriptive high-level data not inside MatchingCore from a building model Element
    Note: Many attributes have been shifted to the LcaMaterial class
    """

    # BaseModel configuration
    model_config = ConfigDict(
        extra = "forbid",           # Forbid extra fields
        validate_assignment=True,   # Validate fields on assignment
        str_strip_whitespace=True   # Strips leading and trailing whitespace for str types
    )
    element_name: str = Field(
        ...,
        description="""
        Exact element name as found in the raw building element data.
        """,
        examples=[
            "Wall W-23", 
            "Type: C30/37 Concrete Wall",
            "Basic Wall:BSP 140 - 5s:2012837"]
    )
    element_uuid: str = Field(
        ...,
        description="""
        Exact element UUID or GlobalId as found in the raw building element data.
        """,
        examples=[
            "0kF45Qs8L9PAM9kmb1lT2B", 
            "2OrWItJ6zAwBNp0OUxK$Dw",
            "1s1jVhK8z0pgKYcr9jt7AB"]
    )
    is_multilayer: bool = Field(
        False,
        description="""
        Boolean flag indicating whether the element represents a **layered construction**.

        Set to **True** if:
        - The element's material composition includes **two or more distinct material layers** 
        that are **physically adjacent** and form an **ordered stack or sequence** (e.g., interior → insulation → exterior finish), **or**
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
    layer_count: Optional[int] = Field(
        None,
        description="""
        Integer indicating the **number of material layers** that make up the element's construction.

        This field is **mandatory whenever** `is_multilayer = True`.

        Set to a positive integer (≥2) if:
        - The element is multilayered (`is_multilayer = True`), **and**
        - The total number of distinct, adjacent material layers can be determined 
        or reliably inferred (for example, from an `IfcMaterialLayerSet`, descriptive data, 
        or explicit enumeration of layers).

        If `is_multilayer = True`, this field **must not be left empty** —  
        provide the best available count, even if approximate or derived from context.

        Leave empty (`None`) only if:
        - The element is not multilayered (`is_multilayer = False`), **or**
        - The record clearly represents a single homogeneous material or non-layered composite
        (e.g., beam, column, door, window, or equipment).
        """,
        examples=[2, 3, 5, 6]
    )
    has_layer_thickness: Optional[bool] = Field(
        None,
        description="""
        Boolean flag indicating whether **each individual material layer** in a multilayer element
        has its **own explicitly defined numeric thickness**.

        Set to **True** if:
        - The element is multilayered (`is_multilayer = True`), **and**
        - Every layer has a distinct, explicitly stated numeric thickness value
        (e.g., as in an `IfcMaterialLayerSet` where each layer defines its own thickness).

        Set to **False** if:
        - The element has multiple identifiable layers, but **thickness is only given once**
        (e.g., a single overall or total thickness for the full build-up), **or**
        - Layers are described qualitatively or by material names only, without individual numeric thicknesses.

        Leave empty (`None`) if:
        - The element is not multilayered (`is_multilayer = False`), or
        - It represents a single material or non-layered composite
        (e.g., window, door, beam, column).
        """,
        examples=[True, False, None]
    )
    object_type: Optional[str] = Field(
        None,
        description="""
        Element's object type label if present (e.g., 'ObjectType', 'Type Name', 'Layer').
        Use the text verbatim from the source. If no "typed" information is present, leave empty.
        """,
        examples=["Structural - Concrete", "Type A-200"]
    )
    classification: Optional[str] = Field(
        None,
        description="""
        Verbatim transcription of any official classification system reference if present.
        Copy exactly as in the source text.
        """,
        examples=['OmniClass 21-02 10 20', 'UniClass Ss_20_10_25']
    )