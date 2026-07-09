from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional

from uuid import UUID
from uuid import uuid4

from pydantic import Field
from pydantic import BaseModel
from pydantic import ConfigDict

from compas_lca.model.lca_element import LcaElement
from compas_lca.model.metadata import ModelMetadata

class LcaModel(BaseModel):
    """
    High-level container for all ElementLike records (`LcaElement` and `AggregatedLcaElement`) 
    within a building-model context. Represents the full LCA data model after parsing, 
    classification, and matching, organized into logical element groups. Each element type 
    shares the same data structure (`LcaElement` or `AggregatedLcaElement`) but differs in 
    how its material composition or function is defined.

    Attributes
    ----------
    id : UUID
        Unique identifier for this LCA model instance. Auto-generated if not provided.

    metadata : ModelMetadata, optional
        Global project or model-level metadata (e.g., name, author, software source,
        creation date, version, etc.).

    single_materials : list[LcaElement], optional
        Elements composed of a single material core (`MatchingCore`), where
        `entry_type="material"`. Represents simple, homogeneous building elements
        such as slabs, columns, or beams with one dominant material.

    layered_elements : list[LcaElement], optional
        Elements composed of multiple `MatchingCore` objects (multi-layered materials),
        still with `entry_type="material"`. Represents composite assemblies such as
        walls, floors, or roofs with several material layers.

    abstract_components : list[LcaElement], optional
        Elements whose `entry_type="component"`, typically representing pre-assembled
        systems or products (e.g., window units, door units, HVAC modules).

    undefined_elements : list[LcaElement], optional
        Elements with incomplete or unrecognized classification (`entry_type="unknown"`),
        kept in this group to ensure the model remains lossless and can be inspected
        or rematched later. 
        Perhaps also include elements that failed matching (would require updating LcaModel post-matching).
    """
    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)

    metadata: Optional[ModelMetadata]
    single_materials: Optional[List[LcaElement]]
    layered_elements: Optional[List[LcaElement]]
    abstract_components: Optional[List[LcaElement]]
    undefined_elements: Optional[List[LcaElement]]


    # ----------------------------
    # Internals
    # ----------------------------
    def _bucket_to_dict(
        self,
        bucket: Optional[Iterable[LcaElement]],
        *,
        aggregated: Optional[bool],  # True | False | None (all)
    ) -> Dict[UUID, str]:
        out: Dict[UUID, str] = {}
        for e in bucket or []:
            is_agg = bool(getattr(e, "is_aggregated", False))
            if aggregated is None or is_agg == aggregated:
                name = getattr(getattr(e, "descriptor", None), "element_name", "")
                out[e.id] = name
        return out

    # ----------------------------
    # Project-level GWP (placeholder)
    # ----------------------------
    """
    could reference indicator_stats of each LcaElemet to calculate project-level min/max/mean GWP
    """


    def min_total_gwp():
        pass

    def max_total_gwp():
        pass