from typing import Literal
from typing import Optional

from textwrap import dedent

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from compas_lca.enums import ConcreteType
from compas_lca.enums import ConcreteStrength
from compas_lca.enums import ConcreteForm
from compas_lca.enums import BinderType
from compas_lca.matching_core.normalization import normalize_concrete_type


class ConcreteFacet(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    concrete_type: ConcreteType = Field(
        ConcreteType.unknown,
        description=dedent("""
            Fundamental property of concrete or cementitious binder product.
            
            DISAMBIGUATION RULES (choose the most specific match):
            • `ready_mixed` — Wet/fresh concrete delivered to site, or processed into an building element on site.
              Keywords: "ready-mix", "cast-in-place", "in-situ concrete", "Ortbeton".
            • `precast` — Factory-manufactured concrete elements, cured before delivery.
              Keywords: "precast", "prefabricated", "factory-made", "pre-fabricated element", "Fertigteil.
            • `cementitious_screed` — screed product applied predominantly for flooring.
              Keywords: "screed", "Beton - CT", "Estrich"
            • `lightweight` — Concrete with lightweight aggregates (expanded clay, pumice, perlite, etc.).
              Air voids are in the aggregates, not the paste. Density typically 800-2000 kg/m³.
            • `aerated` — Autoclave-cured cellular concrete. Low density (~400-800 kg/m³).
            • `binder` — Pure cementite binder materials WITHOUT aggregates (cement powder, cement paste).
              Keywords: "cement", "binder", "Portland cement".
            • `calcium_sulfate` — Gypsum-based binders/screeds (chemically CaSO₄).
            • `calcium_silicate` — Calcium silicate products.
            • `self_compacting` — Self-compacting/self-leveling concrete (flows without vibration).
            • `foamed_concrete` — Foamed by mechanical foaming.
            
            If no clear match is found, assign `unknown`.
        """).strip(),
    )
    @field_validator("concrete_type", mode="before")
    @classmethod
    def _normalize_concrete_type(cls, value):
        return normalize_concrete_type(value)
    concrete_form: Optional[ConcreteForm] = Field(
        None,
        description=dedent("""
        Physical form or geometric configuration of the concrete/cementitious-based product.
        Note: Ready-mix, or cast-in-situ concrete is ALWAYS 'amorphous'.
        """).strip(),
        examples=["cast-in-place", "masonry_unit", "amorphous"]
    )
    pre_stressed: Optional[bool] = Field(
        None,
        description=dedent("""
        Indicates whether the concrete element or product is **prestressed**—that is, produced or installed
        with pre-applied tensile forces (typically via steel tendons or cables) to improve its structural performance.
        """).strip(),
        examples=[True, False]
    )
    binder_type: Optional[BinderType] = Field(
        None,
        description=dedent("""
            Type of binder used for concrete product. Only assign a binder if 
            it is explicitly stated inside of the raw data!
        """).strip(),
        examples=["portland_cement", "lime", "other"]
    )
    cement_type: Optional[str] = Field(
        None,
        description=dedent("""
            According to European standard EN 197-1
            I, II, III, IV, V = The main cement type category
            Subclasses (A, B, C) = The proportion of clinker and other constituents
            Only applies if binder = cement, and a CEM type is explicitly specified in the input data.
        """).strip(),
        examples=["CEM III/A", "CEM II"]
    )
    strength_class: Optional[ConcreteStrength] = Field(
        None,
        description=dedent("""
            Concrete compressive strength class according to EN 206 / EN 1992-1-1.

            Only normal-weight concrete classes ("C") are allowed.
            Lightweight concrete classes ("LC") are NOT supported.

            The value must exactly match one of the following:
            C8/10, C12/15, C16/20, C20/25, C25/30,
            C30/37, C35/45, C40/50, C45/55,
            C50/60, C55/67, C60/75, C80/95.

            Format:
            C f_ck,cyl / f_ck,cube

            Example:
            C30/37

            If the strength class is not explicitly stated or does not match
            one of the allowed values, return null.
        """).strip(),
        examples=["C20/25", "C30/37"]
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
        """).strip()
    )
    xs: Optional[Literal["XS1", "XS2", "XS3"]] = Field(
        None,
        description=dedent("""
        Exposure class (EN 206-1)
        For chloride induced corrosion (from seawater)
        """).strip()
    )
    xf: Optional[Literal["XF1", "XF2", "XF3", "XF4"]] = Field(
        None,
        description=dedent("""
        Exposure class (EN 206-1)
        For the impact of freezing/melting
        """).strip()
    )
    xa: Optional[Literal["XA1", "XA2", "XA3", "XA4"]] = Field(
        None,
        description=dedent("""
        Exposure class (EN 206-1)
        For alkali-silica reaction (chemical agent)
        """).strip()
    )