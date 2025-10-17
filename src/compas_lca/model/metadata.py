from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ElementMetadata(BaseModel):
    """
    Metadata from a building model Element
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
    description: Optional[str] = Field(
        None,
        description="""
        Short one-sentence description of the element using 
        only information present in the source text.
        """,
        examples=["Cast-in-place concrete wall for core enclosure."]
    )
    element_type: Optional[str] = Field(
        None,
        description="""
        Generic element type if explicitly indicated (e.g., 'slab', 'wall', 'roof', 'window',
        'column', 'beam', 'foundation').
        """,
        examples=["wall", "slab"]
    )
    object_type: Optional[str] = Field(
        None,
        description="""
        Element's object or layer type label if present (e.g., 'ObjectType', 'Type Name', 'Layer').
        Use the text verbatim from the source.
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



"""
    spatial_relationship: Optional[str] = Field(
        None,
        description=
        DRAFT: Here it is unsure what kind of data type this is, but here it might be important
        to state what adjacent elements are, what the spatial situation is etc.
        Not yet entirely clear if this is necessary
        ,
        examples=["?"]
    )
"""