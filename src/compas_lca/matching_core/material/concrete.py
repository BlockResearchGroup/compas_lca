from typing import Literal
from typing import Optional

from textwrap import dedent

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import ConcreteType
from compas_lca.enums import ConcreteForm
from compas_lca.enums import BinderType


class ConcreteFacet(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    concrete_type: ConcreteType = Field(
        ConcreteType.unknown,
        description="fundamental property of concrete or cementitious binder product",
        examples=["ready_mixed", "self_compacting"]
    )
    concrete_form: Optional[ConcreteForm] = Field(
        None,
        description="Physical form or geometric configuration of the concrete/cementitious-based product.",
        examples=["cast-in-place","block", "printed"]
    )
    binder_type: Optional[BinderType] = Field(
        None,
        description="Type of binder used for concrete product",
        examples=["portland_cement", "lime", "other"]
    )
    cement_type: Optional[str] = Field(
        None,
        description=dedent("""
            According to European standard EN 197-1
            I, II, III, IV, V = The main cement type category
            Subclasses (A, B, C) = The proportion of clinker and other constituents
            Only applies if binder = cement, and a CEM type is specified
        """).strip(),
        examples=["CEM III/A", "CEM II"]
    )
    strength_class: Optional[str] = Field(
        None,
        description=dedent("""
            Standardized in (EN 206, EN 1992-1-1), written as: C f_ck,cyl / f_ck,cube
            C = Concrete (normal/high strength concrete classes)
            LC = Lightweight concrete
            f_ck,cyl = characteristic cylinder strength (MPa), tested on a 150x300 mm cylinder at 28 days
            f_ck,cube = characteristic cube strength (MPa), tested on a 150 mm cube at 28 days
        """).strip(),
        examples=["C20/25", "C30/37", "LC12/13"]
    )
    slump_class: Optional[Literal["S1", "S2", "S3", "S4", "S5"]] = Field(
        None,
        description="Consistency class determined by slump test (cone test, EN 12350-2)",
        examples=["S1", "S3", "unknown"]
    )
    flow_class: Optional[Literal["F1", "F2", "F3", "F4", "F5", "F6", "unknown"]] = Field(
        None,
        description="Consistency class determined by flow table test (EN 206)",
        examples=["F2", "F5", "unknown"]
    )
    xc: Optional[Literal["XC1", "XC2", "XC3", "XC4"]] = Field(
        None,
        description=dedent("""
            Exposure class (EN 206-1)
            For carbonation induced corrosion (C)
            Severity digits 1-4
        """).strip()
    )
    xd: Optional[Literal["XD1", "XD2", "XD3"]] = Field(
        None,
        description=dedent("""
        Exposure class (EN 206-1)
        For chloride induced corrosion (from de-icing salts)
        Severity digits 1-3
        """).strip()
    )
    xs: Optional[Literal["XS1", "XS2", "XS3"]] = Field(
        None,
        description=dedent("""
        Exposure class (EN 206-1)
        For chloride induced corrosion (from seawater)
        Severity digits 1-3
        """).strip()
    )
    xf: Optional[Literal["XF1", "XF2", "XF3", "XF4"]] = Field(
        None,
        description=dedent("""
        Exposure class (EN 206-1)
        For the impact of freezing/melting
        Severity digits 1-4
        """).strip()
    )
    xa: Optional[Literal["XA1", "XA2", "XA3", "XA4"]] = Field(
        None,
        description=dedent("""
        Exposure class (EN 206-1)
        For alkali-silica reaction (chemical agent)
        Severity digits 1-4
        """).strip()
    )