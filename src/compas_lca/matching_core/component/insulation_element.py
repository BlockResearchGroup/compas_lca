from textwrap import dedent

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import InsulationCore
from compas_lca.enums import InsulationElementType
from compas_lca.enums import InsulationFacing


class InsulationElementFacet(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True, str_strip_whitespace=True)

    insulation_element_type: InsulationElementType = Field(
        InsulationElementType.unknown,
        description=dedent("""
            Classify the product as an insulation **element** based on its form as delivered
            (geometry and assembly), not its detailed chemistry.

            DISAMBIGUATION RULES (sandwich_panel vs sandwich_board vs layered_bonded):
            
            • `sandwich_panel` — Factory-made STRUCTURAL panels with rigid facings on BOTH sides
              (typically metal: steel, aluminum) and an insulating core. Self-supporting, used for
              walls, roofs, cold stores. Large format (typically >1m wide).
              Keywords: "sandwich panel", "Sandwichelement", "PIR panel", "PUR panel", 
              "metal-faced panel", "insulated panel system", "IPS".
              
            • `sandwich_board` — NON-STRUCTURAL multilayer boards with facings. Smaller format,
              used for interior finishing, flooring underlays, or non-loadbearing applications.
              Facings may be gypsum board, MDF, cement board, or similar.
              Keywords: "insulation board with facing", "composite board", "laminated board",
              "faced insulation", "thermal board".
              
            • `layered_bonded` — Multiple insulation layers BONDED together without distinct 
              structural facings. Focus is on combining insulation materials, not on panel action.
              Keywords: "laminated insulation", "bonded layers", "multi-layer insulation".
              
            • `masonry_unit_with_infill` — Blocks or bricks with integrated insulating infill
              in cavities or cores.
              Keywords: "insulated block", "filled block", "thermal block".
              
            • `etics` — External Thermal Insulation Composite Systems (insulation + adhesive +
              reinforcement mesh + render). Complete facade system.
              Keywords: "ETICS", "EIFS", "WDVS", "external insulation system".
              
            • `other` — Clearly an insulation element but doesn't fit above categories.
            • `unknown` — Insufficient information to classify.

            DECISION GUIDE:
            - Metal facings + structural use → `sandwich_panel`
            - Non-metal facings + non-structural → `sandwich_board`  
            - Just bonded insulation layers → `layered_bonded`
        """).strip(),
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
