from typing import Optional
from typing import List

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator

from compas_lca.maps import MODEL_BY_MAT_TYPE

from compas_lca.enums import MaterialType
from compas_lca.enums import ApplicationAreas
from compas_lca.enums import FunctionalTypes
from compas_lca.enums import InsulationInfo

from compas_lca.matching_core.material.common import MaterialCommon

class MaterialCore(BaseModel):
    """
    Container for material semantics (type + common fields) and its type-specific facet.
    """
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )
    material_type: MaterialType
    functional_types: list[FunctionalTypes] = Field(
        default_factory=lambda: [FunctionalTypes.unknown]
    )
    application_areas: list[ApplicationAreas] = Field(
        default_factory=lambda: [ApplicationAreas.unknown]
    )
    insulation_info: Optional[List[InsulationInfo]] = Field(default_factory=list)
    material_facet: object

    @model_validator(mode="before")
    @classmethod
    def _route_facet(cls, data: dict):
        if not isinstance(data, dict):
            return data

        mtype = data.get("material_type")
        facet = data.get("material_facet")

        if mtype is None:
            return data

        # unknown/other check
        name = getattr(mtype, "value", getattr(mtype, "name", str(mtype)))
        if name.lower() in {"unknown", "other"}:
            if facet is None:
                data = {**data, "material_facet": {}}
            return data

        model = MODEL_BY_MAT_TYPE.get(mtype)
        if model is None:
            raise ValueError(f"No facet model registered for material_type={mtype!r}")

        if facet is None:
            raise ValueError("`material_facet` cannot be None.")

        if isinstance(facet, dict):
            data = {**data, "material_facet": model.model_validate(facet)}
            return data

        if not isinstance(facet, model):
            raise TypeError(
                f"`material_facet` must be {model.__name__} for material_type={mtype}, "
                f"got {type(facet).__name__}"
            )
        return data


def assemble_material_core(common: MaterialCommon, material_facet: object) -> MaterialCore:
    """
    Assemble a MaterialCore from MaterialCommon and a facet (dict or model instance).
    The correct facet model will be enforced based on `common.material_type`.
    """
    return MaterialCore(
        material_type=common.material_type,
        functional_types=common.functional_types,
        application_areas=common.application_areas,
        insulation_info=common.insulation_info,
        material_facet=material_facet,
    )