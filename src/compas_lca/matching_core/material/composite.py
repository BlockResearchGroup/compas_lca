from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import CompositeType
from compas_lca.enums import CompositeMatrix
from compas_lca.enums import CompositeForm
from compas_lca.enums import CompositeArchitecture
from compas_lca.enums import CompositeReinforcement

class CompositeFacet(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    composite_type: CompositeType = Field(
        CompositeType.unknown,
        description="""
        High-level category of composite material/product, reflecting typical building use 
        Describes what 'kind' of composite material/product this is.
        """,
        examples=[
            "reinforced_concrete",
            "fiber_reinforced_concrete",
            "polymer_modified_cementitious",
            "polymer_concrete",
            "fiber_cement_composite",
            "wood_plastic_composite",
            "fiber_reinforced_polymer",
            "sandwich_panel"
        ]
    )
    composite_matrix: Optional[CompositeMatrix] = Field(
        None,
        description="""
        The **continuous phase or binder material** that forms the main body of the composite.  
        It surrounds and holds together the reinforcement or filler, transferring stresses and defining 
        most of the composite's physical and chemical behavior.  
        If the matrix material cannot be determined, leave empty.
        """,
        examples=["cementitious", "bituminous", "ceramic"]
    )
    composite_reinforcement: Optional[CompositeReinforcement] = Field(
        None,
        description="""
        The **dispersed or embedded phase** within the composite that provides mechanical strength, stiffness, 
        or toughness to the matrix.  
        Reinforcements can appear as **fibers, particles, fabrics, meshes, or bars**, depending on the composite type.  
        Only specify this attribute for **reinforced composites**, otherwise leave empty.
        """,
        examples=[
            "steel_rebar",
            "steel_fibers",
            "glass_fibers",
            "carbon_fibers",
            "cellulose_fibers",
            "wood_particles",
            "mineral_aggregate"
        ]
    )
    composite_form: Optional[CompositeForm] = Field(
        None,
        description="""
        Physical product form/geometry for the composite in construction applications.
        """,
        examples=[
            "board", "panel", "sandwich_panel", "profile", "tube",
            "rebar", "block", "precast_element", "wrap", "laminate"
        ]
    )
    composite_architecture: Optional[CompositeArchitecture] = Field(
        None,
        description="""
        Structural/architectural arrangement of the composite.
        For example, use 'sandwich_core' for panels/boards with a core, or use
        'block_with_insert' for masonry/shuttering units with integrated insulation.
        """
    )