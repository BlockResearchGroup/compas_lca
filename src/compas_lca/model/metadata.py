from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict


class ModelMetadata(BaseModel):
    """
    Pydantic BaseModel that captures provenance and metadata for building model element
    datasets (e.g., 3dm, IFC, RVGT, etc.). Use this to record where a dataset came from,
    so downstream calculations and audits can trace sources.

    Parameters
    ----------
    dataset_source : str
        The origin software/dataformat of the dataset.
        Examples: "IFC", "RVT", "OBJ"

    source_version : Optional[str]
        The version (if available) of the dataset's model
        Examples: "IFC2X3", "IFC4"

    dataset_filename : Optional[str]
        The filename of the source building model
        Example: "1072_HiLo_Model-Architecture.ifc"

    dataset_uuid : Optional[str]
        A stable UUID associated with the dataset, if one exists.
        Example: IfcBuildingElement GlobalId

    location_data : Optional[Any]
        The geographic coverage/representativeness of the dataset, as a code.
        Prefer ISO 3166 country/region codes (e.g., "CH", "DE", "EU", "US-CA")
        or another clearly documented regional code system.

    reference_date : Optional[str]
        The creation date of the file from which the element was sourced (if obtainable)

    dataset_owner : Optional[str]
        The person or organization that owns the dataset (“contact data set” owner).
        Examples: Architect office name / BIM model owner.
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    dataset_source: Optional[str] = None
    source_version: Optional[str] = None
    dataset_filename: Optional[str] = None
    dataset_uuid: Optional[str] = None
    location_data: Optional[Any] = None
    reference_date: Optional[str] = None
    dataset_owner: Optional[str] = None
