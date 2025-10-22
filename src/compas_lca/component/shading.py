from typing import Optional
from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import ConfigDict

from compas_lca.enums import ComponentType
from compas_lca.enums import ShadingDeviceType
from compas_lca.enums import ShadingDeviceMaterial

# DRAFT
class ShadingDeviceFacet(BaseModel):

    model_config = ConfigDict(
        extra="forbid",                 # Forbid extra fields
        validate_assignment=True,       # Validate fields on assignment
        str_strip_whitespace=True       # Strip leading/trailing whitespace for str types
    )

    # Discriminator
    component_type: Literal[ComponentType.shading_device] = Field(ComponentType.shading_device)

    # Attributes to be inferred
    shading_device_type: ShadingDeviceType = Field(
        ShadingDeviceType.unknown,
        description="""
        Specifies the physical form or construction type of the shading device,
        """,
        examples=["external_fixed", "internal_blind", "between_glazing"]
    )
    shading_device_material: ShadingDeviceMaterial = Field(
        ShadingDeviceMaterial.unknown,
        description="""
        The dominant material for this shading device
        """,
        examples=["metal", "fabric", "plastic"]
    )