from typing import Optional
from typing import List

from textwrap import dedent

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from compas_lca.enums import FrameType
from compas_lca.enums import WindowOperation
from compas_lca.enums import GlazingCount
from compas_lca.matching_core.normalization import normalize_frame_type

class WindowFacet(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    frame_type: FrameType = Field(
        FrameType.unknown,
        description=dedent("""
            The dominant **frame material type** of the window or glazing unit.  
            Refers to the material that forms the structural frame (e.g., aluminium, wood, PVC, steel, or composite).  
            If the SPECIFICALLY the frame material is not stated or cannot be inferred, set to `"unknown"`.
        """).strip(),
        examples=["aluminium", "wood", "unknown"]
    )
    @field_validator("frame_type", mode="before")
    @classmethod
    def _normalize_frame_type(cls, value):
        return normalize_frame_type(value)
    glazing_count: Optional[GlazingCount] = Field(
        None,
        description=dedent("""
            The number of glazing layers in the window or glazing unit.  
            Indicates how many sheets of glass form the insulated assembly  
            If the glazing configuration is not specified, leave this field empty.
        """).strip(),
        examples=[
            ["single_glazing"],
            ["triple_glazing"],
            ["other"]
        ]
    )
    window_operation: Optional[List[WindowOperation]] = Field(
        None,
        description=dedent("""
            The opening or operating mechanisms of the window unit.  
            Specify how the window can be opened, moved, or positioned during use.  
            Use one or more values if the product supports multiple operations 
            If the operation type is not stated, leave this field empty.
        """).strip(),
        examples=[
            ["folding"],
            ["tilt_turn", "fixed"],
            ["other"]
        ]
    )
    acoustic_interlayer: bool = Field(
        False,
        description=dedent("""
            This boolean value describes if window product has acoustic interlayer or acoustic glazing.
            Assign a boolean value if this information is explicitly stated in the input dataset.
        """).strip(),
        examples=[True, False]
    )
    roof_window: bool = Field(
        False,
        description=dedent("""
            This boolean value describes if the window product is EXPLICITLY a roof window, in which case the value is True. 
            If it doesn't state in the dataset that the window is a roof window, set to False.
        """).strip(),
        examples=[True, False]
    )
    window_height: Optional[float] = Field(
        None,
        description=dedent("""
            The height of the window product in milimeters (mm). Only assign this value if the height
            is explicitly mentioned within the dataset.
        """).strip(),
        examples=[1500, 1700]
    )
    window_width: Optional[float] = Field(
        None,
        description=dedent("""
            The width of the window product in milimeters (mm). Only assign this value if the height
            is explicitly mentioned within the dataset.
        """).strip(),
        examples=[900, 1200]
    )