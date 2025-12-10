from textwrap import dedent

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import InsulationElementType
from compas_lca.enums import InsulationCore
from compas_lca.enums import InsulationFacing


class InsulationElementFacet(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )

    insulation_element_type: InsulationElementType = Field(
        InsulationElementType.unknown,
        description=dedent("""
            Classify the product as an insulation **element** based on its form as delivered
            (geometry and assembly), not its detailed chemistry.

            • Use 'sandwich_panel' for factory-made panels with a structural or semi-structural 
              core and two outer facings, intended as wall/roof elements or similar.
            • Use 'sandwich_board' for non-structural multilayer boards or floor/wall elements
              where the main function is insulation or finishing, not load-bearing panel action.
            • Use 'masonry_unit_with_infill' for blocks or bricks that integrate an insulating
              infill into cavities or cores of the masonry unit.
            • Use 'layered_bonded' for products built from multiple bonded layers of boards,
              mats or sheets (e.g. laminated insulation/finishing products).
            • Use 'profile' for linear or shaped insulating elements (e.g. strips, L/U profiles,
              thermal breaks, perimeter or edge profiles).
            • Use 'etics' for external thermal insulation composite systems (insulation + render/
              adhesive layers designed as a facade system).
            • Use 'other' if the element is clearly an insulation product but does not fit any
              of the above types.
            • Use 'unknown' if there is not enough information to infer the element type.

            When several categories seem possible, choose the one that best describes the
            intended use and overall product configuration. If uncertainty remains high,
            prefer 'unknown' over guessing.
        """).strip(),
        examples=[
            "sandwich_panel",
            "sandwich_board",
            "masonry_unit_with_infill",
            "etics",
        ],
    )

    insulation_core: InsulationCore = Field(
        InsulationCore.unknown,
        description=dedent("""
            Classify the dominant insulating **core material** inside the element. This refers
            to the main volume of insulation, not thin facings, coatings or adhesives.

            • Choose the value that best represents the primary insulating substance that fills
              the interior of the element (e.g. foam, fibre, bio-based mat).
            • Focus on the material that occupies the largest share of the thickness or volume
              of the insulation layer, even if other materials are present.
            • Use 'other' if the core is clearly an insulation material but does not match any
              specific enum value.
            • Use 'unknown' if the information on the core material is missing, ambiguous or
              cannot be reliably inferred.

            Do not set a specific core value purely based on product marketing names; there
            should be a reasonable indication of the actual material type. If in doubt, use
            'other' or 'unknown' rather than guessing.
        """).strip(),
        examples=[
            "polyurethane",
            "polystyrene",
            "mineral_wool",
            "wood_fibre",
            "biofibre",
        ],
    )

    insulation_facing: InsulationFacing = Field(
        InsulationFacing.unknown,
        description=dedent("""
            Classify the material of the **outer facing or bounding layers** of the insulation
            element. This refers to sheets, boards or films that enclose or cover the core, not
            to internal fillers or small accessories.

            • Choose the value that best describes the main outer surfaces in contact with the
              environment or adjacent construction layers (e.g. steel sheet, plywood board,
              gypsum board, polymer film).
            • If the element has different materials on the two sides, select the one that is
              most characteristic for the product or most relevant for its application.
            • Use 'other' if the facing is clearly present but made from a material that does
              not match any specific enum value.
            • Use 'unknown' if it is unclear whether the product even has a distinct facing
              layer or if the facing material cannot be identified.

            If the product is a simple board or batt without any distinct facing or skin,
            and only the core material is present, keep 'insulation_facing' as 'unknown'.
        """).strip(),
        examples=[
            "steel",
            "aluminium",
            "plywood",
            "gypsum_board",
            "polymer_film",
        ],
    )
