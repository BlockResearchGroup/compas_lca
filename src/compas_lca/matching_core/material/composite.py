from textwrap import dedent
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from compas_lca.enums import CompositeArchitecture
from compas_lca.enums import CompositeForm
from compas_lca.enums import CompositeMatrix
from compas_lca.enums import CompositeReinforcement
from compas_lca.enums import CompositeType
from compas_lca.matching_core.normalization import normalize_composite_type


class CompositeFacet(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True, str_strip_whitespace=True)
    composite_type: CompositeType = Field(
        CompositeType.unknown,
        description=dedent("""
            High-level category of composite material/product, reflecting typical building use. 
            Describes what 'kind' of composite material/product this is.
            
            DISAMBIGUATION RULES:
            
            CEMENTITIOUS COMPOSITES:
            • `reinforced_concrete` — Conventional concrete with steel reinforcement (rebar, mesh).
            • `fiber_reinforced_concrete` — Concrete with dispersed fibers (steel, glass, PP, basalt).
            • `polymer_modified_cementitious` — Cement-based with polymer additives (PMC/PCC).
            • `fiber_cement_composite` — Fiber-cement boards/sheets (Eternit-type). Cement matrix + cellulose/synthetic fibers.
              Keywords: "fiber cement", "fibre cement", "Faserzement", "Eternit".
            • `wood_cement_composite` — Wood particles/fibers bonded with cement (CBPB, wood wool cement boards).
              Keywords: "wood cement", "Holzwolle-Zement", "CBPB", "cement-bonded particleboard".
            
            POLYMER-MATRIX COMPOSITES (distinguish carefully):
            • `polymer_concrete` — Polymer resin as the BINDER/MATRIX with mineral AGGREGATES (sand, gravel).
              The polymer replaces cement. Used for repair mortars, drainage channels, manholes.
              Keywords: "polymer concrete", "resin concrete", "PC", "epoxy concrete".
              
            • `particulate_filled_polymer` — Polymer with mineral FILLERS (calcium carbonate, silica, ATH).
              Fillers modify properties but polymer is the continuous phase. No coarse aggregates.
              Keywords: "filled polymer", "mineral-filled", "filler", "compound".
              
            • `fiber_reinforced_polymer` — FRP: Polymer matrix reinforced with continuous fibers (GFRP, CFRP, BFRP).
              Keywords: "FRP", "GFRP", "CFRP", "glass fiber reinforced", "carbon fiber reinforced",
              "fiberglass", "pultruded", "composite rebar".
            
            WOOD-POLYMER:
            • `wood_plastic_composite` — WPC: Wood particles in thermoplastic matrix (PE, PP, PVC).
              Keywords: "WPC", "wood-plastic", "composite decking".
            
            METAL COMPOSITES:
            • `metal_polymer_composite` — Metal-filled polymers or metal/polymer hybrids.
            
            If uncertain between `polymer_concrete` and `particulate_filled_polymer`:
            - If aggregates (sand, gravel) are bound by resin → `polymer_concrete`
            - If polymer contains fine mineral fillers → `particulate_filled_polymer`
        """).strip(),
    )

    @field_validator("composite_type", mode="before")
    @classmethod
    def _normalize_composite_type(cls, value):
        return normalize_composite_type(value)

    composite_matrix: Optional[CompositeMatrix] = Field(
        None,
        description=dedent("""
            The **continuous phase or binder material** that forms the main body of the composite.  
            It surrounds and holds together the reinforcement or filler, transferring stresses and defining 
            most of the composite's physical and chemical behavior.  
            If the matrix material cannot be determined, leave empty.
        """).strip(),
        examples=["cementitious", "bituminous", "ceramic"],
    )
    composite_reinforcement: Optional[CompositeReinforcement] = Field(
        None,
        description=dedent("""
            The **dispersed or embedded phase** within the composite that provides mechanical strength, stiffness, 
            or toughness to the matrix.  
            Reinforcements can appear as **fibers, particles, fabrics, meshes, or bars**, depending on the composite type.  
            Only specify this attribute for **reinforced composites**, otherwise leave empty.
        """).strip(),
        examples=["steel_rebar", "steel_fibers", "glass_fibers", "carbon_fibers", "cellulose_fibers", "wood_particles", "mineral_aggregate"],
    )
    composite_form: Optional[CompositeForm] = Field(
        None,
        description="Physical product form/geometry for the composite in construction applications.",
        examples=["board", "panel", "sandwich_panel", "profile", "tube", "rebar", "block", "precast_element", "wrap", "laminate"],
    )
    composite_architecture: Optional[CompositeArchitecture] = Field(
        None,
        description=dedent("""
            Structural/architectural arrangement of the composite.
            For example, use 'sandwich_core' for panels/boards with a core, or use
            'block_with_insert' for masonry/shuttering units with integrated insulation.
        """).strip(),
        examples=["monolithic", "particulate_filled", "other"],
    )
