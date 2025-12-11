from typing import Optional

from textwrap import dedent

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import PolymericType
from compas_lca.enums import PolymericForm

class PolymericFacet(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    polymeric_type: PolymericType = Field(
        PolymericType.unknown,
        description=dedent("""
            Dominant polymer or elastomer composition of the material. 
            Identifies the base polymer family used in the product, such as thermoplastics, 
            thermosets, elastomers, or biopolymer composites.
            
            DISAMBIGUATION RULES (always prefer SPECIFIC types over generic):
            
            POLYOLEFINS (check abbreviations carefully):
            • `polyethylene` — PE, HDPE, LDPE, LLDPE, UHMWPE. Includes PE films, pipes, membranes.
              Keywords: "polyethylene", "PE", "HDPE", "LDPE", "Polyethylen".
            • `polypropylene` — PP. Includes PP pipes, geotextiles, fibers.
              Keywords: "polypropylene", "PP", "Polypropylen".
            
            POLYESTERS (different from polyethylene!):
            • `polyester` — PET, polyester fibers, polyester resins for coatings/FRP.
              Keywords: "polyester", "PET", "polyester fiber", "Polyester".
              NOTE: "polyester" ≠ "polyethylene". Check spelling carefully.
            
            VINYLS:
            • `polyvinyl_chloride` — PVC (use exact enum spelling with underscore).
              Keywords: "PVC", "vinyl", "polyvinyl chloride", "Polyvinylchlorid".
            
            FOAMS/INSULATION:
            • `expanded_polystyrene` — EPS (white beaded foam).
            • `extruded_polystyrene` — XPS (colored rigid foam boards).
            • `polyurethane` — PUR/PU foams, coatings, adhesives.
            • `polyisocyanurate` — PIR (improved fire performance vs PUR).
            
            RESINS (use specific type when identifiable):
            • `phenolic` — Phenol-formaldehyde resins/foams. Keywords: "phenolic", "phenol", "Bakelite".
            • `epoxy` — Epoxy resins (adhesives, coatings, FRP matrix).
            • `acrylic` — PMMA, acrylic glass, acrylic coatings.
            • `resin` — Use ONLY as fallback when the specific resin type cannot be determined.
              Prefer specific types (`phenolic`, `epoxy`, `polyester`) when identifiable.
            
            OTHER:
            • `silicone` — Silicone sealants, adhesives, coatings.
            • `rubber` — Natural or synthetic rubber products.
            • `polycarbonate` — PC glazing panels.
            • `polyamide` — PA/Nylon. Keywords: "polyamide", "PA", "nylon", "Polyamid".
            
            Always choose the MOST SPECIFIC type. Use `resin` only when no specific resin type is indicated.
        """).strip(),
    )
    polymeric_form: Optional[PolymericForm] = Field(
        None,
        description=dedent("""
            Physical form or manufactured configuration in which the polymeric material appears. 
            Describes the product geometry or application type.
        """).strip(),
        examples=["sheet_membrane", "profile_rigid", "floor_tile_modular"]
    )
    recycled_content: Optional[bool] = Field(
        None,
        description=dedent("""
            This field describes if the polymeric material is has recycled content (True) or is primary (False)
            Assign a boolean value if this information is explicitly stated in the input dataset,
            or if the value unambiguously clear (common sense).
        """).strip(),
        examples=[True, False]
    )