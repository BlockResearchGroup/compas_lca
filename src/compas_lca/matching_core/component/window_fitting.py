from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict

from compas_lca.enums import WindowFittingType

class WindowFittingFacet(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    window_fitting_type: WindowFittingType = Field(
        WindowFittingType.unknown,
        description="""
        The material from which the window fitting is made
        """,
        examples=["aluminium", "brass", "zinc"]
    )