from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict


class ItemMetadata(BaseModel):
    """
    Pydantic BaseModel that captures provenance and metadata for environmental
    datasets (e.g., EPDs, national databases like KBOB/Oekobaudat, standards-based
    datasets). Use this to record where a dataset came from, and how/when it is valid,
    so downstream calculations and audits can trace sources.

    Parameters
    ----------
    dataset_source : str
        The origin identifier or descriptor of the dataset. Examples:
        "KBOB 2022", "Ökobaudat 2024", "EPD: Manufacturer X v1.3".
        Use this to quickly recognize the database, publisher, or EPD source/version.
        If adding data from an LCA database, check the existing compas_lca entries for
        preexisting entries and naming conventions for dataset_source str values.

    dataset_uuid : Optional[str]
        A stable UUID associated with the dataset, if one exists. For example,
        an official UUID from a registry or database entry.

    dataset_url : Optional[str]
        A public hyperlink to the dataset or its landing page (e.g., an EPD PDF
        page or database record webpage).

    registration_number : Optional[str]
        The EPD/projcet registration or identification number issued by the publisher
        or program operator. Prioritize any EPD registration, if available.

    location_code : Optional[str]
        The geographic coverage/representativeness of the dataset, as a code.
        Prefer ISO 3166 country/region codes (e.g., "CH", "DE", "EU", "US-CA")
        or another clearly documented regional code system.

    reference_year : Optional[int]
        The first year of the time period for which the dataset is valid
        or represents measured/reference data. Example: 2022.

    valid_until : Optional[int]
        The final year through which the dataset is considered valid. This typically
        marks when a revision is required or expected. Example: 2027.

    dataset_owner : Optional[str]
        The person or organization that owns the dataset (“contact data set” owner).
        Note; this is usually not the publisher or program operator.

    compliance_system_name : Optional[List[str]]
        The standards and/or compliance systems declared as met by the dataset.
        Examples: ["EN 15804", "EN 16485"]. Since this is a list, consider
        renaming to `compliance_system_names`.

    Usage notes
    -----------
    - Check for any preexisting `dataset_source` and `compliance_system_name` entries
      as to not create duplicates or inconsistent naming.
    - Keep any new `dataset_source` value concise but specific enough to disambiguate
      among databases and EPD versions.
    - Use `location_code`, `reference_year`, and `valid_until` together to clarify
      representativeness in space and time.
    - Prefer stable identifiers: fill `dataset_uuid`, `registration_number` and
      `dataset_url` whenever available to support reproducibility and auditing.
    - For multiple compliance systems, include all relevant standards in
      `compliance_system_name`.
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    dataset_source: str
    dataset_uuid: Optional[str] = None
    dataset_url: Optional[str] = None
    registration_number: Optional[str] = None
    location_code: Optional[str] = None
    reference_year: Optional[int] = None
    valid_until: Optional[int] = None
    dataset_owner: Optional[str] = None
    compliance_system_name: Optional[List[str]] = None
