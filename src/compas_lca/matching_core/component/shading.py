from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import ShadingDeviceMaterial
from compas_lca.enums import ShadingDeviceType


class ShadingFacet(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True, str_strip_whitespace=True)
    shading_device_type: ShadingDeviceType = Field(
        ShadingDeviceType.unknown,
        description="Specifies the physical form or construction type of the shading device.",
        examples=["external_fixed", "internal_blind", "between_glazing"],
    )
    shading_device_material: Optional[ShadingDeviceMaterial] = Field(None, description="The dominant material for this shading device.", examples=["metal", "fabric", "plastic"])
