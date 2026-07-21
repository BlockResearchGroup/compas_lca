from textwrap import dedent
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import CurtainWallForm
from compas_lca.enums import CurtainWallType


class CurtainWallFacet(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True, str_strip_whitespace=True)
    curtain_wall_type: CurtainWallType = Field(
        CurtainWallType.unknown,
        description=dedent("""
            The primary structural or framing material system of the curtain wall.  
            Defines the main material used for mullions, transoms, or supporting profiles   
            If the curtain wall's framing material cannot be determined, set to `"unknown"`.
        """).strip(),
        examples=["timber_aluminium", "ceramic"],
    )
    curtain_wall_form: Optional[CurtainWallForm] = Field(
        None,
        description=dedent("""
            The construction or assembly method of the curtain wall system.  
            Describes how façade elements are manufactured, assembled, and installed. 
            Leave empty if the construction form is not stated or cannot be confidently inferred.
        """).strip(),
        examples=["stick_construction", "panelized"],
    )
