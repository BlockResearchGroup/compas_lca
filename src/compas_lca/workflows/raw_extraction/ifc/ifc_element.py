from typing import Optional
from typing import Literal
from typing import List
from typing import Annotated
from typing import Union

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

# ------------------------
# Metadata
# ------------------------
class IfcElementMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    global_id: str
    type: str
    object_type: Optional[str] = None
    description: Optional[str] = None
    classification: Optional[Union[List[dict], str]] = None
    decomposes: Optional[dict] = None
    is_decomposed_by: Optional[List[dict]] = None

# ------------------------
# Material associations
# ------------------------
class IfcMaterial(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    entity: Literal["IfcMaterial"]
    material_name: str
    material_description: Optional[str] = None
    material_category: Optional[str] = None
    material_properties: Optional[dict] = None 

class IfcMaterialLayer(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    material_name: str
    material_description: Optional[str] = None
    thickness: Optional[float] = Field(None, ge=0)
    thickness_unit: Optional[str] = None
    material_properties: Optional[dict] = None
    is_ventilated: Optional[bool] = None

class IfcMaterialLayerSet(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    entity: Literal["IfcMaterialLayerSet"]
    layer_set_name: str
    layer_set_description: Optional[str] = None
    material_layers: List[IfcMaterialLayer]

class IfcMaterialLayerSetUsage(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    entity: Literal["IfcMaterialLayerSetUsage"]
    layer_set_name: str
    layer_set_description: Optional[str] = None
    material_layers: List[IfcMaterialLayer]
    layer_set_direction: Optional[str] = None
    direction_sense: Optional[str] = None

# Discriminated union over the "entity"
MaterialAssociation = Annotated[
    Union[IfcMaterialLayerSetUsage, IfcMaterialLayerSet, IfcMaterial],
    Field(discriminator="entity"),
]

# ------------------------
# Element properties
# ------------------------
class IfcElementProperties(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    psets_element: Optional[dict] = None
    psets_type: Optional[dict] = None

# ------------------------
# Quantities
# ------------------------
class IfcElementQuantities(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    units: Literal["meter, square_meter, cubic_meter"]
    width: Optional[float] = Field(None, ge=0)
    length: Optional[float] = Field(None, ge=0)
    height: Optional[float] = Field(None, ge=0)
    depth: Optional[float] = Field(None, ge=0)
    gross_area: Optional[float] = Field(None, ge=0)
    net_area: Optional[float] = Field(None, ge=0)
    gross_side_area: Optional[float] = Field(None, ge=0)
    net_side_area: Optional[float] = Field(None, ge=0)
    gross_footprint_area: Optional[float] = Field(None, ge=0)
    net_footprint_area: Optional[float] = Field(None, ge=0)
    cross_section_area: Optional[float] = Field(None, ge=0)
    gross_volume: Optional[float] = Field(None, ge=0)
    net_volume: Optional[float] = Field(None, ge=0)

# ------------------------
# Element data container
# ------------------------
class IfcElementData(BaseModel):
    """Container for raw extracted IFC element data."""
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    metadata: IfcElementMetadata
    material_data: Optional[MaterialAssociation] = None
    properties: Optional[IfcElementProperties] = None
    quantities: Optional[IfcElementQuantities] = None
