from typing import Optional
from typing import List

from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict

from compas_lca.enums import FrameType
from compas_lca.enums import WindowOperation
from compas_lca.enums import GlazingCount

class WindowFacet(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    frame_type: FrameType = Field(
        FrameType.unknown,
        description="""
        The dominant **frame material type** of the window or glazing unit.  
        Refers to the material that forms the structural frame (e.g., aluminium, wood, PVC, steel, or composite).  
        If the frame material is not stated or cannot be inferred, set to `"unknown"`.
        """,
        examples=["aluminium", "wood", "unknown"]
    )
    glazing_count: Optional[GlazingCount] = Field(
        None,
        description="""
        The number of glazing layers in the window or glazing unit.  
        Indicates how many sheets of glass form the insulated assembly  
        If the glazing configuration is not specified, leave this field empty.
        """,
        examples=[
            ["single_glazing"],
            ["triple_glazing"],
            ["other"]
        ]
    )
    window_operation: Optional[List[WindowOperation]] = Field(
        None,
        description="""
        The **opening or operating mechanisms** of the window unit.  
        Specify how the window can be opened, moved, or positioned during use.  
        Use one or more values if the product supports multiple operations 
        If the operation type is not stated, leave this field empty.
        """,
        examples=[
            ["folding"],
            ["tilt_turn", "fixed"],
            ["other"]
        ]
    )
    acoustic_interlayer: Optional[bool] = Field(
        None,
        description="""
        This boolean value describes if window product has acoustic interlayer or acoustic glazing.
        Assign a boolean value if this information is explicitly stated in the input dataset.
        """,
        examples=[True, False]
    )
    window_height: Optional[float] = Field(
        None,
        description="""
        The height of the window product in milimeters (mm). Only assign this value if the height
        is explicitly mentioned within the dataset.
        """,
        examples=[1500, 1700]
    )
    window_width: Optional[float] = Field(
        None,
        description="""
        The width of the window product in milimeters (mm). Only assign this value if the height
        is explicitly mentioned within the dataset.
        """,
        examples=[900, 1200]
    )