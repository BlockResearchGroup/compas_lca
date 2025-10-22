from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict

from compas_lca.enums import ComponentType
from compas_lca.enums import ConveyorType

class ConveyorFacet(BaseModel):

    model_config = ConfigDict(
        extra="forbid",                 # Forbid extra fields
        validate_assignment=True,       # Validate fields on assignment
        str_strip_whitespace=True       # Strip leading/trailing whitespace for str types
    )

    # Discriminator
    component_type: Literal[ComponentType.conveyor] = Field(ComponentType.conveyor)

    # Attributes to be inferred
    conveyor_type: ConveyorType = Field(
        ConveyorType.unknown,
        description="""
        Type of conveyor
        """,
        examples=["elevator", "escalator", "wormhole"]
    )
