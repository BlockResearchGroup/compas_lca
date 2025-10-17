from typing import Optional
from typing import Union

from uuid import UUID
from uuid import uuid4

from compas.datastructures import Mesh
from compas.geometry import Geometry
from compas.geometry import Brep
from compas_model.elements import Element

from compas_lca.material.lca_material import LcaMaterial

from .quantity import Quantities
from .metadata import ElementMetadata

class LcaElement(Element):
    """Base class for an LCA Element converted from different data formats (IFC, 3dm, etc.).
    Represents data points required for precise LCA inventory filtering (LcaMaterial) and LCA calculation (Quantities)
    compas_model Element subclass (does this make sense though?)
    -> uuid is automatically created

    Attributes 
    ---------- 
    uuid : UUID
        Unique identifier for this LCA element. Automatically generated if not provided.
    metadata : 
        Metadata of the element (name, description, manufacturer, etc.). 
    material : LcaMaterial
        A dense list of attributes and values related to the LcaMaterial in terms of a material/product/composite
        This serves as the "matching core" between data from a building model element and inventory data
        perhaps naming convention should be reconsidered
        ALSO -> What if dissectable composite? Or Multi-Layer Element? This should for sure be a List,
        which stores an LcaComposite (and if it is a "pure" material then it is an LcaComposite with 1 LcaMaterial an 100% ratio)
    quantity : 
        Quantity Stores length, area, volume, and any other quantities relevant for LCA calculation. 
        Note -> Would the quantities also be extracted by an LLM? Or should they always be calculated
        by the COMPAS geometry operations?? This would be computationally expensive (especially if IFC quantities already there.)
    geometry : 
        Geometry, optional Geometric specifications, required for visualization and missing quantities. 
        Inherited from Element superclass. 
    """

    def __init__(
        self,
        uuid,
        metadata: ElementMetadata = None,
        material: Optional[LcaMaterial] = None,   # Can be optional (i.e. IfcWindow does not have material descriptors often). Also need to consider if this is LcaMaterial or LcaComposite by default, to make sure it can include more.
        quantities: Optional[Quantities] = None,
        geometry: Optional[Union[Brep, Mesh]] = None,
        name: Optional[str] = None,         # This is very awkward, as it needs to be extracted (and is part of the Metadata)
        **kwargs,
    ):
        super().__init__(geometry=geometry, name=name, **kwargs) # Not sure how the Element name gets passed down to the compas_model Element class though...
        self._uuid: UUID = uuid4() # maybe redundant to have LcaMaterial with an UUID and LcaElement?
        self.metadata = metadata
        self.material = material # probably will have to be "list(material or [])" at some point.
        self.quantities = quantities
        

    @property
    def __data__(self) -> dict:
        data = super().__data__
        data.update({
            "metadata": self.metadata.__data__ if self.metadata else None,
            "materials": self.material.__data__ if self.material else None,
            "quantities": self.quantities.__data__ if self.quantities else None,
            "geometry": self.geometry.__data__ if self.geometry else None
        })
        return data

    @classmethod
    def __from_data__(cls, data: dict) -> "LcaElement":
        metadata = ElementMetadata.__from_data__(data["metadata"]) if data.get("metadata") else None
        material = LcaMaterial.__from_data__(data["material"]) if data.get("material") else None
        quantities = Quantities.__from_data__(data["quantities"]) if data.get("quantities") else None
        geometry = Geometry.__from_data__(data["geometry"]) if data.get("geometry") else None

        kwargs = {}
        for key in ("transformation", "features", "material", "name"):
            if key in data:
                kwargs[key] = data[key]

        return cls(
            metadata=metadata,
            material=material,
            quantities=quantities,
            geometry=geometry,
            **kwargs
        )

    def __repr__(self) -> str:
        return (
            f"LcaElement(name={self.name}, "
            f"material={self.material_names}, "
            f"metadata={self.metadata}), "
            f"thickness={self.total_thickness()}, "
            f"quantity={self.quantities}"
        )

