from typing import Optional
from typing import Union
from typing import List

from uuid import UUID
from uuid import uuid4

from compas.datastructures import Mesh
from compas.geometry import Geometry
from compas.geometry import Brep
from compas_model.elements import Element

from compas_lca.matching_core.core import MatchingCore

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
       - 'component_core: MatchingCore'  (represents an installable assembly, e.g., window unit)
       - 'material_core: List[MaterialSpec]'  (represents the element's material composition
          as an ordered list of material specifications. Multiple MaterialSpec implies layering.)

    2) If 'material_data' is provided:
       - It must be a non-empty 'List[MaterialSpec]'.
       - Each 'MaterialSpec' must contain:
           • Pure spec: exactly one 'MatchingCore', its 'volumetric_ratio' coerced/validated to 1.0.
           • Composite spec: ≥ 2 'MatchingCore' items whose 'volumetric_ratio' values sum ≈ 1.0.
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
    component_core : Optional[MatchingCore]
        Component-level descriptor (assembly). Use when the source element represents a
        manufactured/constructed unit or system without a layer/composition breakdown
        (e.g., window unit, curtain-wall module, packaged HVAC, predefined wall/roof assembly).
        Mutually exclusive with 'material_data'.
    material_core : Optional[List[MaterialSpec]]
        Ordered list of material specifications describing the element's material makeup.
        Each 'MaterialSpec' can be:
          • pure (single `MatchingCore`, ratio=1.0), or
          • disaggregated composite (multiple 'MatchingCore' items, ratios sum ≈ 1.0).
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
    plaster = MatchingCore(name="Plaster", facet=..., volumetric_ratio=1.0)
    wool    = MatchingCore(name="Mineral wool", facet=..., volumetric_ratio=1.0)
    spec_plaster = MaterialSpec.from_pure(plaster, name="Plaster")
    spec_wool    = MaterialSpec.from_pure(wool,    name="Insulation")

    # Material path (composite spec: reinforced concrete)
    conc  = MatchingCore(name="Concrete",    facet=..., volumetric_ratio=0.93)
    rebar = MatchingCore(name="Steel rebar", facet=..., volumetric_ratio=0.07)
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
        component_core: Optional[MatchingCore] = None,     # mutually exclusive with material_data
        material_core: Optional[List[MaterialSpec]] = None, # mutually exclusive with component_data
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
        if (component_core is None and not material_core) or (component_core is not None and material_core):
            raise ValueError(
                "Provide exactly one of 'component_core' (MatchingCore) OR 'material_core' (List[MaterialSpec])."
            )

        # Material path type checking
        if not isinstance(material_core, list) or not all(isinstance(m, MaterialSpec) for m in material_core):
            raise TypeError("'material_core' must be a non-empty List[MaterialSpec].")

        # Component path
        if component_core is not None:
            if not isinstance(component_core, MatchingCore):
                raise TypeError("'component_core' must be a 'MatchingCore'.")
            self.component_core = component_core
            self.material_core = None

        # Material (layered) path
        else:
            if not isinstance(material_core, list) or not all(isinstance(m, MaterialSpec) for m in material_core):
                raise TypeError("'material_core' must be a List[MatchingCore].")
            if len(material_core) == 0:
                raise ValueError("'material_core' list cannot be empty.")
            self.material_core = list(material_core)
            self.component_core = None

    # Convenience flags
    @property
    def is_component(self) -> bool:
        return self.component_core is not None

    @property
    def is_material_stack(self) -> bool:
        return self.material_core is not None

    @property
    def __data__(self) -> dict:
        data = super().__data__
        data.update({
            "metadata": self.metadata.__data__ if self.metadata else None,
            "component_core": self.component_core.__data__ if self.component_core else None,
            "material_core": [ms.__data__ for ms in self.material_core] if self.material_core else None,
            "quantities": self.quantities.__data__ if self.quantities else None,
            "geometry": self.geometry.__data__ if self.geometry else None,
        })
        return data

    @classmethod
    def __from_data__(cls, data: dict) -> "LcaElement":
        metadata = ElementMetadata.__from_data__(data["metadata"]) if data.get("metadata") else None
        component_core = MatchingCore.__from_data__(data["component_core"]) if data.get("component_core") else None
        material_core = (
            [MaterialSpec.__from_data__(d) for d in data["material_core"]]
            if data.get("material_core") else None
        )
        quantities = Quantities.__from_data__(data["quantities"]) if data.get("quantities") else None
        geometry = Geometry.__from_data__(data["geometry"]) if data.get("geometry") else None

        kwargs = {}
        for key in ("transformation", "features", "name"):
            if key in data:
                kwargs[key] = data[key]

        return cls(
            metadata=metadata,
            component_core=component_core,
            material_core=material_core,
            quantities=quantities,
            geometry=geometry,
            **kwargs
        )

    def __repr__(self) -> str:
        return (
            f"LcaElement(name={self.name}, "
            f"uuid={self.uuid}, "
            f"component_core={self.component_core}, "
            f"material_core={self.material_core}, "
            f"metadata={self.metadata}, "
            f"quantities={self.quantities}, "
            f"geometry={self.geometry})"
        )