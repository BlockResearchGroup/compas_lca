from textwrap import dedent

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import RailingType


class RailingFacet(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True, str_strip_whitespace=True)
    railing_type: RailingType = Field(
        RailingType.unknown,
        description=dedent("""
            Classification of the railing type based on its construction and infill system.
            Mappings:
              • "balustrade" — traditional vertical posts (balusters) with a handrail.
              • "glass_panel" — framed or frameless glass infill panels.
              • "cable" — horizontal or vertical tensioned cable infill systems.
              • "perforated_panel" — metal sheet or mesh infill (perforated, expanded, or wire mesh).
              • "guard_wall" — solid, monolithic parapet or low protective wall functioning as a guardrail.
              • "other" — any railing type not captured by the above categories.
              • "unknown" — used when the dataset does not provide enough information.
        """).strip(),
        examples=["balustrade", "cable", "other"],
    )
