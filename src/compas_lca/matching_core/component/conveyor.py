from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict

from compas_lca.enums import ConveyorType

class ConveyorFacet(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    conveyor_type: ConveyorType = Field(
        ConveyorType.unknown,
        description="""
        Type of conveyor
        """,
        examples=["elevator", "escalator"]
    )