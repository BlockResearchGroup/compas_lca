from typing import Optional
from typing import Literal

from uuid import UUID
from uuid import uuid4

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator

from compas_lca.matching_core.common import Common
from compas_lca.matching_core.material.core import MaterialCore
from compas_lca.matching_core.component.core import ComponentCore

from compas_lca.enums import EntryType

from compas_lca.validators import LoadbearingType
from compas_lca.validators import InteriorExteriorType
from compas_lca.validators import ManufacturerStr
from compas_lca.validators import ThicknessFloat
from compas_lca.validators import LambdaFloat
from compas_lca.validators import UValueFloat

# Map material type to its corresponding facet model
MODEL_BY_ENTRY_TYPE = {
    EntryType.material: MaterialCore,
    EntryType.component: ComponentCore,
    EntryType.unknown: None
}

class MatchingCore(BaseModel):
    """
    MatchingCore as container for any kind and nested/branched attributes of construction materials or components.
    Allows the dynamic filtering between LCA Data and building model materials/elemenets.
    """
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )
    core_id: UUID = Field(default_factory=uuid4) # core_id for matching InventoryItem matches to individual layers (individual MatchingCore objects)
    entry_type: EntryType
    name: str
    loadbearing: Optional[LoadbearingType] = None
    placement: Optional[InteriorExteriorType] = None
    manufacturer: Optional[ManufacturerStr] = None
    provenance: Optional[str] = None
    production_location: Optional[str] = None
    thickness: Optional[ThicknessFloat] = Field(None, ge=0)
    thickness_source: Optional[Literal["from_data", "speculated"]] = None
    thermal_conductivity: Optional[LambdaFloat] = Field(None, ge=0)
    u_value: Optional[UValueFloat] = Field(None, ge=0)
    fire_retardant: Optional[bool] = None
    water_vapour_resistant: Optional[bool] = None
    facet: object

    @model_validator(mode="before")
    @classmethod
    def _route_facet(cls, data: dict):
        if not isinstance(data, dict):
            return data

        etype = data.get("entry_type")
        facet = data.get("facet")

        if etype is None:
            return data

        # unknown/other check
        name = getattr(etype, "value", getattr(etype, "name", str(etype)))
        if name.lower() in {"unknown", "other"}:
            if facet is None:
                data = {**data, "facet": {}}
            return data

        model = MODEL_BY_ENTRY_TYPE.get(etype)
        if model is None:
            raise ValueError(f"No facet model registered for entry_type={etype!r}")

        if facet is None:
            raise ValueError("`facet` cannot be None.")

        if isinstance(facet, dict):
            data = {**data, "facet": model.model_validate(facet)}
            return data

        if not isinstance(facet, model):
            raise TypeError(
                f"`facet` must be {model.__name__} for entry_type={etype}, "
                f"got {type(facet).__name__}"
            )
        return data


def assemble_matching_core(common: Common, facet: object) -> MatchingCore:
    return MatchingCore(
        entry_type=common.entry_type,
        name=common.name,
        loadbearing=common.loadbearing,
        placement=common.placement,
        manufacturer=common.manufacturer,
        provenance=common.provenance,
        production_location=common.production_location,
        thickness=common.thickness,
        thickness_source=common.thickness_source,
        thermal_conductivity=common.thermal_conductivity,
        u_value=common.u_value,
        fire_retardant=common.fire_retardant,
        water_vapour_resistant=common.water_vapour_resistant,
        facet=facet
    )