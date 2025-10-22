from typing import Optional
from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict

from compas_lca.enums import ComponentType
from compas_lca.enums import RoofType

# DRAFT
class RoofFacet(BaseModel):

    model_config = ConfigDict(
        extra="forbid",                 # Forbid extra fields
        validate_assignment=True,       # Validate fields on assignment
        str_strip_whitespace=True       # Strip leading/trailing whitespace for str types
    )

    # Discriminator
    component_type: Literal[ComponentType.roof] = Field(ComponentType.roof)

    # Attributes to be inferred
    roof_type: RoofType = Field(
        RoofType.unknown,
        description="""
        The type of roof or roof superstructure described in the dataset
        """,
        examples=["flat_roof", "pitched_roof", "green_roof"]
    )
