from typing import Optional
from typing import Union
from typing import List

from uuid import UUID
from uuid import uuid4

from compas.datastructures import Mesh
from compas.geometry import Geometry
from compas.geometry import Brep
from compas_model.elements import Element

from compas_lca.component.lca_component import LcaComponent

from .quantity import Quantities
from .metadata import ElementMetadata
from .materialspec import MaterialSpec

class LcaElement(Element):
    """
    LCA element record (one building-model element mapped to LCA inputs).

    Purpose
    -------
    Encapsulates everything needed to match against LCA inventory entries
    (component/material descriptors) and to run quantity take-off (quantities),
    optionally carrying geometry for visualization or geometry-derived quantities.

    Canonical name
    --------------
    The canonical element name is 'LcaElement.name' (inherited from Element).
    If 'name' is not provided, it is derived from 'metadata.name' (when available).
    This class does not mutate 'metadata.name'.

    Invariants (must always hold)
    -----------------------------
    1) XOR: Provide exactly one of:
       - 'component_data: LcaComponent'  (represents an installable assembly, e.g., window unit)
       - 'material_data: List[MaterialSpec]'  (represents the element's material composition
          as an ordered list of specs. Each spec is either a pure material or a composite split)

    2) If 'material_data' is provided:
       - It must be a non-empty 'List[MaterialSpec]'.
       - Each 'MaterialSpec' must contain:
           • Pure spec: exactly one 'LcaMaterial', its 'volumetric_ratio' coerced/validated to 1.0.
           • Composite spec: ≥ 2 'LcaMaterial' items whose 'volumetric_ratio' values sum ≈ 1.0.
         (The ratio rule/validation applies within the 'MaterialSpec' class)

    Attributes
    ----------
    uuid : UUID
        Stable unique identifier for this element. Auto-generated if not provided ('uid').
    name : Optional[str]
        Human-readable name. If omitted, derived from 'metadata.name' when present.
    metadata : Optional[ElementMetadata]
        Descriptive metadata about the source element (authoring app, source IDs, labels,
        manufacturer hints, notes). Not authoritative for quantities.
    component_data : Optional[LcaComponent]
        Component-level descriptor (assembly). Use when the source element represents a
        manufactured/constructed unit or system without a layer/composition breakdown
        (e.g., window unit, curtain-wall module, packaged HVAC, predefined wall/roof assembly).
        Mutually exclusive with 'material_data'.
    material_data : Optional[List[MaterialSpec]]
        Ordered list of material specifications describing the element's material makeup.
        Each 'MaterialSpec' can be:
          • pure (single `LcaMaterial`, ratio=1.0), or
          • disaggregated composite (multiple 'LcaMaterial', ratios sum ≈ 1.0).
        Mutually exclusive with `component_data`.
    quantities : Optional[Quantities]
        Numeric take-offs used for LCA (length, area, volume, piece count, etc.).
        If not provided but 'geometry' is present, compas may compute them downstream.
    geometry : Optional[Union[Brep, Mesh]]
        Optional geometry for visualization and/or fallback quantity derivation.
        Passed through to the 'Element' base class.

    Examples
    --------
    # Component path (assembly)
    LcaElement.from_component(
        component=LcaComponent(...),
        metadata=ElementMetadata(name="South façade window"),
        quantities=Quantities(area=2.1),
    )

    # Material path (pure specs)
    plaster = LcaMaterial(name="Plaster", facet=..., volumetric_ratio=1.0)
    wool    = LcaMaterial(name="Mineral wool", facet=..., volumetric_ratio=1.0)
    spec_plaster = MaterialSpec.from_pure(plaster, name="Plaster")
    spec_wool    = MaterialSpec.from_pure(wool,    name="Insulation")

    # Material path (composite spec: reinforced concrete)
    conc  = LcaMaterial(name="Concrete",    facet=..., volumetric_ratio=0.93)
    rebar = LcaMaterial(name="Steel rebar", facet=..., volumetric_ratio=0.07)
    spec_rc = MaterialSpec.from_split([conc, rebar], name="RC core")

    wall = LcaElement(
        metadata=ElementMetadata(name="South wall"),
        material_data=[spec_plaster, spec_wool, spec_rc],
        quantities=Quantities(area=42.0, thickness=0.35),
    )
    """


    def __init__(
        self,
        *,
        uid: Optional[UUID] = None,
        name: Optional[str] = None,
        metadata: Optional[ElementMetadata] = None,
        component_data: Optional[LcaComponent] = None,     # mutually exclusive with material_data
        material_data: Optional[List[MaterialSpec]] = None, # mutually exclusive with component_data
        quantities: Optional[Quantities] = None,
        geometry: Optional[Union[Brep, Mesh]] = None,
        **kwargs,
    ):
        # name derived from metadata if not provided
        derived_name = name or (metadata.name if (metadata and getattr(metadata, "name", None)) else None)

        super().__init__(geometry=geometry, name=derived_name, **kwargs)
        self.uuid: UUID = uid or uuid4()
        self.metadata = metadata
        self.quantities = quantities

        # XOR check
        if (component_data is None and not material_data) or (component_data is not None and material_data):
            raise ValueError(
                "Provide exactly one of 'component_data' (LcaComponent) OR 'material_data' (List[MaterialSpec])."
            )

        # Material path type checking
        if not isinstance(material_data, list) or not all(isinstance(m, MaterialSpec) for m in material_data):
            raise TypeError("'material_data' must be a non-empty List[MaterialSpec].")

        # Component path
        if component_data is not None:
            if not isinstance(component_data, LcaComponent):
                raise TypeError("'component_data' must be an LcaComponent.")
            self.component_data = component_data
            self.material_data = None

        # Material (layered) path
        else:
            if not isinstance(material_data, list) or not all(isinstance(m, MaterialSpec) for m in material_data):
                raise TypeError("'material_data' must be a List[LcaMaterial].")
            if len(material_data) == 0:
                raise ValueError("'material_data' list cannot be empty.")
            self.material_data = list(material_data)
            self.component_data = None

    # Convenience flags
    @property
    def is_component(self) -> bool:
        return self.component_data is not None

    @property
    def is_material_stack(self) -> bool:
        return self.material_data is not None

    @property
    def __data__(self) -> dict:
        data = super().__data__
        data.update({
            "metadata": self.metadata.__data__ if self.metadata else None,
            "component_data": self.component_data.__data__ if self.component_data else None,
            "material_data": [ms.__data__ for ms in self.material_data] if self.material_data else None,
            "quantities": self.quantities.__data__ if self.quantities else None,
            "geometry": self.geometry.__data__ if self.geometry else None,
        })
        return data

    @classmethod
    def __from_data__(cls, data: dict) -> "LcaElement":
        metadata = ElementMetadata.__from_data__(data["metadata"]) if data.get("metadata") else None
        component_data = LcaComponent.__from_data__(data["component_data"]) if data.get("component_data") else None
        material_data = (
            [MaterialSpec.__from_data__(d) for d in data["material_data"]]
            if data.get("material_data") else None
        )
        quantities = Quantities.__from_data__(data["quantities"]) if data.get("quantities") else None
        geometry = Geometry.__from_data__(data["geometry"]) if data.get("geometry") else None

        kwargs = {}
        for key in ("transformation", "features", "name"):
            if key in data:
                kwargs[key] = data[key]

        return cls(
            metadata=metadata,
            component_data=component_data,
            material_data=material_data,
            quantities=quantities,
            geometry=geometry,
            **kwargs
        )

    def __repr__(self) -> str:
        return (
            f"LcaElement(name={self.name}, "
            f"uuid={self.uuid}, "
            f"component_data={self.component_data}, "
            f"material_data={self.material_data}, "
            f"metadata={self.metadata}, "
            f"quantities={self.quantities}, "
            f"geometry={self.geometry})"
        )

