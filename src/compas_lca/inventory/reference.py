from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


from compas_lca.validators import RefUnitType

class ReferenceInfo(BaseModel):
    """
    Reference information for an EPD / LCA intentory entry's declared unit.

    This model represents the declared reference size and unit used to express
    environmental impacts in EPD datasets.  
    It ensures that declared units follow the standardized set of allowed values
    defined in :class:`RefUnitType`.

    Parameters
    ----------
    size : int
        The declared reference size (must be a positive integer, typically ``1``).
        Represents the quantitative basis for the environmental indicators
        (e.g., "1 m² of product", "1 kg of material").
    unit : RefUnitType
        The declared reference unit (validated against the :class:`RefUnit` enum).
        Current values include "kg", "m", "m2", "m3", or "pcs".

    Usage notes
    -----------
    Is a separate class as this is absoulutely crucial to get right. For hardcoded
    extraction perhaps overkill, but for agent-based extraction it deserves it's
    own output schema
    """


    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    size: int = Field(1, gt=0)
    unit: RefUnitType