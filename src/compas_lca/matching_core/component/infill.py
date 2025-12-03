from typing import Optional

from textwrap import dedent

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import InfillType
from compas_lca.enums import InfillMaterialFamily
from compas_lca.enums import InfillConstruction
from compas_lca.enums import InfillSafetyType
from compas_lca.enums import InfillCoating

class InfillFacet(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    infill_type: InfillType = Field(
        InfillType.unknown,
        description=dedent("""
            High-level classification of the infill as transparent, opaque, or translucent.
            This describes the optical behaviour of the built-up infill element in normal use.
            If the optical behaviour cannot be determined from the dataset, set to `"unknown"`.
        """).strip(),
        examples=["transparent", "opaque", "translucent", "unknown"],
    )

    infill_material_family: InfillMaterialFamily = Field(
        InfillMaterialFamily.unknown,
        description=dedent("""
            The primary material family of the infill element.
            Use `float_glass` for standard soda-lime flat glass products,
            `glass_ceramic` for glass-ceramic sheets (e.g. MAGNA Glaskeramik),
            `plastic_glazing` for PMMA, polycarbonate or similar, and `other_glass`
            for special glass types that are not clearly float glass or glass-ceramic.
            If the material family cannot be inferred, set to `"unknown"`.
        """).strip(),
        examples=["float_glass", "glass_ceramic", "plastic_glazing", "unknown"],
    )

    infill_construction: Optional[InfillConstruction] = Field(
        None,
        description=dedent("""
            The construction type of the infill element.
            `monolithic` covers single sheets or plates,
            `insulating_glass_unit` covers sealed double or triple glazing units,
            `laminated` covers laminated glass where multiple panes are bonded with an interlayer,
            and `laminated_insulating_unit` covers IGUs that include at least one laminated pane.
            If the construction type is not stated or cannot be inferred, leave empty.
        """).strip(),
        examples=["monolithic", "insulating_glass_unit", "laminated", "laminated_insulating_unit"],
    )

    infill_safety_type: Optional[InfillSafetyType] = Field(
        None,
        description=dedent("""
            Describes whether the infill is explicitly a safety glass product and, if so, of which type.
            Use `thermally_toughened` for thermally toughened or tempered safety glass,
            `laminated_safety` for laminated safety glass, and `combined` where both toughened
            and laminated panes are present in the same infill.
            If no safety function is declared, leave empty.
        """).strip(),
        examples=["none", "thermally_toughened", "laminated_safety", "combined"],
    )

    infill_coating: Optional[InfillCoating] = Field(
        None,
        description=dedent("""
            The presence and basic type of functional coating on the infill.
            Use `uncoated` if the product is explicitly stated as uncoated,
            `coated_generic` if it is coated but the coating type is not specified,
            and `low_e` or `solar_control` where this is clearly identified in the dataset.
            If the coating information is not given, leave empty.
        """).strip(),
        examples=["uncoated", "coated_generic", "low_e", "solar_control"],
    )
