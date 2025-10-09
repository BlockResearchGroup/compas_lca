from __future__ import annotations
from typing import Optional
from typing import List
from typing import Union

from compas.datastructures import Mesh
from compas.geometry import Geometry
from compas.geometry import Brep
from compas_model.elements import Element

from .attributes.materialspec import Material
from .attributes.quantity import Quantities
from .attributes.metadata import Metadata

class LcaElement(Element):
    """Base class for an LCA Element converted from different data formats (IFC, 3dm, etc.).
    Represents data points required for precise LCA inventory matching and LCA calculation.
    compas_model Element subclass. 
    
    Attributes 
    ---------- 
    materials : List[Material] 
        A sequence of materials. 
        Each "Material" can represent: - a single material (pure or mixed) - multiple materials layers (pure and/or mixed) 
    quantity : 
        Quantity Stores length, area, volume, and any other quantities relevant for LCA calculation. 
    metadata : 
        Metadata Matching-relevant metadata (name, description, manufacturer, etc.). 
    geometry : 
        Geometry, optional Geometric specifications, required for visualization and missing quantities. 
        Inherited from Element superclass. 
    """

    def __init__(
        self,
        materials: List[Material],   # n >= 1 for multi-layer
        quantities: Optional[Quantities] = None,
        metadata: Optional[Metadata] = None,
        geometry: Optional[Union[Brep, Mesh]] = None,
        name: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(geometry=geometry, name=name, **kwargs)
        if not materials or len(materials) == 0:
            raise ValueError("LcaElement requires at least one Material.")
        self.materials = list(materials or [])
        self.quantities = quantities
        self.metadata = metadata

    @property
    def material_names(self) -> List[str]:
        return [m.name for m in self.materials if getattr(m, "name", None)]

    @property
    def __data__(self) -> dict:
        data = super().__data__
        data.update({
            "geometry": self.geometry.__data__ if self.geometry else None,
            "materials": [comp.__data__ for comp in self.materials],
            "quantities": self.quantities.__data__ if self.quantities else None,
            "metadata": self.metadata.__data__ if self.metadata else None,
        })
        return data

    @classmethod
    def __from_data__(cls, data: dict) -> "LcaElement":
        materials = [Material.__from_data__(x) for x in data.get("materials", [])]
        quantities = Quantities.__from_data__(data["quantities"]) if data.get("quantities") else None
        metadata = Metadata.__from_data__(data["metadata"]) if data.get("metadata") else None
        geometry = Geometry.__from_data__(data["geometry"]) if data.get("geometry") else None

        kwargs = {}
        for key in ("transformation", "features", "material", "name"):
            if key in data:
                kwargs[key] = data[key]

        return cls(
            materials=materials,
            quantities=quantities,
            metadata=metadata,
            geometry=geometry,
            **kwargs,
        )

    def __repr__(self) -> str:
        return (
            f"LcaElement(name={self.name}, "
            f"materials={self.material_names}, "
            f"thickness={self.total_thickness()}, "
            f"quantity={self.quantities}, "
            f"metadata={self.metadata})"
        )

