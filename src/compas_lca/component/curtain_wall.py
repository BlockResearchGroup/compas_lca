from typing import Optional
from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict

from compas_lca.enums import ComponentType
from compas_lca.enums import CurtainWallType
from compas_lca.enums import CurtainWallForm

class WallFacet(BaseModel):

    model_config = ConfigDict(
        extra="forbid",                 # Forbid extra fields
        validate_assignment=True,       # Validate fields on assignment
        str_strip_whitespace=True       # Strip leading/trailing whitespace for str types
    )

    # Discriminator
    component_type: Literal[ComponentType.curtain_wall] = Field(ComponentType.curtain_wall)

    # Attributes to be inferred
    curtain_wall_type: CurtainWallType = Field(
        CurtainWallType.unknown,
        description="""
        The primary structural or framing material system of the curtain wall.  
        Defines the main material used for mullions, transoms, or supporting profiles   
        If the curtain wall's framing material cannot be determined, set to `"unknown"`.
        """,
        examples=["timber_aluminium", "ceramic"]
    )
    curtain_wall_form: Optional[CurtainWallForm] = Field(
        None,
        description="""
        The construction or assembly method of the curtain wall system.  
        Describes how façade elements are manufactured, assembled, and installed. 
        Leave empty if the construction form is not stated or cannot be confidently inferred.
        """,
        examples=["stick_construction", "panelized"]
    )
