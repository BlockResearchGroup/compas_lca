from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import model_validator

from compas_lca.maps import MODEL_BY_COMP_TYPE

from compas_lca.enums import ComponentType

from compas_lca.matching_core.component.common import ComponentCommon

class ComponentCore(BaseModel):
    """
    Container for component semantics (type) and its type-specific facet.
      - 'component_type' determines which facet model to use.
      - 'component_facet' can be either a dict (raw payload) or an already
        constructed facet instance; it will be validated/coerced accordingly.
    """
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )
    component_type: ComponentType
    component_facet: object

    @model_validator(mode="before")
    @classmethod
    def _route_facet(cls, data: dict):
        if not isinstance(data, dict):
            return data

        ctype = data.get("component_type")
        facet = data.get("component_facet")

        if ctype is None:
            return data

        # unknown/other check
        name = getattr(ctype, "value", getattr(ctype, "name", str(ctype)))
        if name.lower() in {"unknown", "other"}:
            if facet is None:
                data = {**data, "component_facet": {}}
            return data

        model = MODEL_BY_COMP_TYPE.get(ctype)
        if model is None:
            raise ValueError(f"No facet model registered for component_type={ctype!r}")

        if facet is None:
            raise ValueError("`component_facet` cannot be None.")

        if isinstance(facet, dict):
            data = {**data, "component_facet": model.model_validate(facet)}
            return data

        if not isinstance(facet, model):
            raise TypeError(
                f"`component_facet` must be {model.__name__} for component_type={ctype}, "
                f"got {type(facet).__name__}"
            )
        return data


def assemble_component_core(common: ComponentCommon, component_facet: object) -> ComponentCore:
    """
    Assemble a ComponentCore from a ComponentCommon and a facet (dict or model instance).
    The correct facet model will be enforced based on `common.component_type`.
    """
    return ComponentCore(
        component_type=common.component_type,
        component_facet=component_facet,
    )