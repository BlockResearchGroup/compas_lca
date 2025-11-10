from typing import Optional
from typing import List

from textwrap import dedent

from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict

from compas_lca.enums import DoorType
from compas_lca.enums import DoorOperation
from compas_lca.enums import SafetyFunction

class DoorFacet(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    door_type: DoorType = Field(
        DoorType.unknown,
        description=dedent("""
            The primary material that forms infill of the door.
            If the door material stated or cannot be inferred, set to `"unknown"`.
        """).strip(),
        examples=["aluminium", "wood", "unknown"]
    )
    door_operation: Optional[List[DoorOperation]] = Field(
        None,
        description=dedent("""
            The opening or operating mechanisms of the door unit.  
            Specifies how the door can be opened, moved, or positioned during use.  
            Use one or more values if the product supports multiple operations 
            If the operation type is not stated, leave this field empty.
        """).strip(),
        examples=[
            ["swing_hinged"],
            ["folding", "sliding"],
            ["other"]
        ]
    )
    safety_function: Optional[List[SafetyFunction]] = Field(
        None,
        description=dedent("""
            The safety-related functions performed by the door, window, or building product.  
            Specify one or more functions that contribute to protection, safety, or controlled access in normal or emergency conditions.  
            If no specific safety function is mentioned or implied, leave empty.
        """).strip(),
        examples=[
            ["security_access_control"],
            ["fire_protection", "smoke_protection"]
        ]
    )
    door_automatization: Optional[bool] = Field(
        None,
        description=dedent("""
            Indicates whether the door includes automatic opening or closing mechanisms 
            (e.g., motorized or sensor-controlled operation). Set to `True` if automated, otherwise `False`.
        """).strip(),
        examples=[True, False]
    )
    door_height: Optional[float] = Field(
        None,
        description=dedent("""
            The height of the door unit in milimeters (mm). Only assign this value if the height
            is explicitly mentioned within the dataset.
        """).strip(),
        examples=[1500, 1700]
    )
    door_width: Optional[float] = Field(
        None,
        description=dedent("""
            The width of the door unit in milimeters (mm). Only assign this value if the height
            is explicitly mentioned within the dataset.
        """).strip(),
        examples=[900, 1200]
    )