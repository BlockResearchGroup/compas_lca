from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict

from compas_lca.enums import RailingType

class RailingFacet(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    railing_type: RailingType = Field(
        RailingType.unknown,
        description="The type of railing described in the dataset",
        examples=["balustrade", "cable", "other"]
    )