from __future__ import annotations
from typing import Dict
from typing import Optional
from typing import Literal
from compas.data import Data

# Life cycle stages defined by EN 15804
StageName = Literal["A1-A3", "A4", "A5", "C1", "C2", "C3", "C4", "D"]

# Indicators defined by ILCD+EPD dataformat
IndicatorName = Literal[
    # Core environmental indicators
    "GWPtotal",
    "GWPbiogenic",
    "GWPfossil",
    "GWPluluc", # land use and land use change
    "ODP", # ozone depletion potential
    "AP", # acidification potential
    "EPfw", # eutrophication potential freshwater
    "EPmarine", # eutrophication potential marine
    "EPterrestrial", # eutrophication potential terrestrial
    "POCP", # photochemical ozone creation potential
    "ADPM", # abiotic depletion potential for non-fossil resources
    "ADPF", # abiotic depletion potential for fossil resources
    "WDP", # water depletion potential

    # Additional Environmental Indicators
    "PM", # potential incidence of disease due to PM emissions
    "IRP", # potential human exposure efficiency relative to U235
    "ETPfw", # potential comparative toxic unit for ecosystems
    "HTPc", # potential comparative toxic unit for humans, cancer effects
    "HTPnc", # potential comparative toxic unit for humans, non-cancer effects
    "SQP", # potential soil quality index

    # Indicators describing resource use
    "PERE", # use of renewable primary energy excluding renewable primary energy resources used as raw materials
    "PERM", # use of renewable primary energy resources used as raw materials
    "PERT", # total use of renewable primary energy resources
    "PENRE", # use of non-renewable primary energy excluding non-renewable primary energy resources used as raw materials
    "PENRM", # use of non-renewable primary energy resources used as raw materials
    "PENRT", # total use of non-renewable primary energy resources
    "SM", # use of secondary materials
    "RSF", # use of renewable secondary fuels
    "NRSF", # use of non-renewable secondary fuels
    "FW", # net use of fresh water

    # Environmental information describing waste categories
    "HWD", # hazardous waste disposed
    "NHWD", # non-hazardous waste disposed
    "RWD", # radioactive waste disposed

    # Environmental information describing output flows
    "CRU", # components for reuse
    "MFR", # materials for recycling
    "MER", # materials for energy recovery
    "EEE", # exported electrical energy
    "EET", # exported thermal energy
]

# Canonical mapping from indicator name → unit
INDICATOR_UNITS: dict[IndicatorName, str] = {
    # Core environmental indicators
    "GWPtotal": "kg CO2 eq",
    "GWPbiogenic": "kg CO2 eq",
    "GWPfossil": "kg CO2 eq",
    "GWPluluc": "kg CO2 eq",
    "ODP": "kg CFC-11 eq",
    "AP": "mol H+ eq",
    "EPfw": "kg P eq",
    "EPmarine": "kg N eq",
    "EPterrestrial": "mol N eq",
    "POCP": "kg NMVOC eq",
    "ADPM": "kg Sb eq",
    "ADPF": "MJ",
    "WDP": "m3 world eq. deprived",

    # Additional Environmental Indicators
    "PM": "disease incidence",
    "IRP": "kBq U235 eq",
    "ETPfw": "CTUe",  # Comparative Toxic Unit for ecosystems
    "HTPc": "CTUh",  # Comparative Toxic Unit for humans, cancer
    "HTPnc": "CTUh", # Comparative Toxic Unit for humans, non-cancer
    "SQP": "dimensionless",

    # Indicators describing resource use
    "PERE": "MJ",
    "PERM": "MJ",
    "PERT": "MJ",
    "PENRE": "MJ",
    "PENRM": "MJ",
    "PENRT": "MJ",
    "SM": "kg",
    "RSF": "MJ",
    "NRSF": "MJ",
    "FW": "m3",

    # Environmental information describing waste categories
    "HWD": "kg",
    "NHWD": "kg",
    "RWD": "kg",

    # Environmental information describing output flows
    "CRU": "kg",
    "MFR": "kg",
    "MER": "kg",
    "EEE": "MJ",
    "EET": "MJ",
}




class Indicator(Data):
    """An environmental indicator for one material, across life cycle stages."""

    def __init__(
        self,
        name: IndicatorName,
        stages: dict[StageName, float],  # mapping: stage -> indicator value
        source: Optional[str] = None,
    ):
        super().__init__(name=name)
        self.name = name
        self.unit = INDICATOR_UNITS[name]

    @property
    def total(self) -> float:
        """Sum of all stage values."""
        return sum(self.stages.values())

    @property
    def stage_names(self) -> list[StageName]:
        return list(self.stages.keys())

    @property
    def __data__(self) -> dict:
        return {
            "name": self.name,
            "unit": self.unit,
            "stages": self.stages,
            "source": self.source,
        }

    @classmethod
    def __from_data__(cls, data: dict) -> "Indicator":
        return cls(
            name=data["name"],
            stages=data["stages"],
            source=data.get("source"),
        )

    def __repr__(self) -> str:
        return f"Indicator(name={self.name}, unit={self.unit}, total={self.total})"

