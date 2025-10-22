from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict

from compas_lca.enums import ComponentType
from compas_lca.enums import WindowFittingType

class WindowFittingFacet(BaseModel):

    model_config = ConfigDict(
        extra="forbid",                 # Forbid extra fields
        validate_assignment=True,       # Validate fields on assignment
        str_strip_whitespace=True       # Strip leading/trailing whitespace for str types
    )

    # Discriminator
    component_type: Literal[ComponentType.window_fitting] = Field(ComponentType.window_fitting)

    # Attributes to be inferred
    window_fitting_type: WindowFittingType = Field(
        WindowFittingType.unknown,
        description="""
        The material from which the window fitting is made
        """,
        examples=["aluminium", "brass", "zinc"]
    )