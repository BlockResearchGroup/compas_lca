from typing import Optional
from typing import List

from uuid import UUID
from uuid import uuid4

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.model.lca_element import LcaElement
from compas_lca.model.metadata import ModelMetadata

class LcaModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)

    metadata: Optional[ModelMetadata]
    single_materials: Optional[List[LcaElement]]    # Elements with one MatchingCore object & "entry_type" = "material"
    layered_elements: Optional[List[LcaElement]]    # Elements with multiple MatchingCore objects & "entry_type" = "material"
    abstract_components: Optional[List[LcaElement]] # Elements with one MatchingCore object % & "entry_type" = "component"
    undefined_elements: Optional[List[LcaElement]]  # Elements with & "entry_type" = "unknown"


# classmethod -> get all elements with same object_type. this is strongly enforced (and partially hardcoded) for IFC, and later 3dm aswell
# question: should we aggregate all elements with the same object type as one LcaElement, and then sum up the quantities? and flag that it has been summed? or should we do this @ BOQ generation?