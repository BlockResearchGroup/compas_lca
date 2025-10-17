from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import MaterialType
from compas_lca.enums import CompositeType

"""
This represents a Facet for materials that have compounds from different types
such as concrete + insulation, or wood-plastic-composites (WPC)
Some of these have direct entries in environmentaly databases
Which means that if there is a composite modeled in a building model, and it has a
composite in the inventory, then there is no need to dissect it into different
LcaMaterial instances.

for now: generic placeholder facet (attributes need to be defined)
"""

class CompositeFacet(BaseModel):

    model_config = ConfigDict(
        extra = "forbid",           # Forbid extra fields
        validate_assignment=True,   # Validate fields on assignment
        str_strip_whitespace=True   # Strips leading and trailing whitespace for str types
    )

    # Discriminator
    material_type: Literal[MaterialType.composite] = Field(MaterialType.composite)

    # attributes to be inferred
    composite_type: CompositeType = Field(
        CompositeType.unknown,
        description="",
        examples=["placeholder"]
    )