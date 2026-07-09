"""
Note:
Should perhaps convert to WOOD-BASED facet instead of LIGNEOUS
"""

from typing import Optional

from textwrap import dedent

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import WoodType
from compas_lca.enums import WoodForm
from compas_lca.enums import WoodSurface
from compas_lca.enums import BaseSpecies
from compas_lca.enums import WoodProcessing
from compas_lca.enums import WoodAdhesive
from compas_lca.enums import DryingMethod
from compas_lca.enums import ModificationMethod


class WoodFacet(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    wood_type: WoodType = Field(
        WoodType.unknown,
        description=dedent("""
            Classification of the wood-based material according to its primary composition and manufacturing type. 
            Distinguishes between natural solid wood, engineered wood products, and chemically or thermally modified wood. 
            This field represents the dominant product family or structural form of the wood material.
            
            DISAMBIGUATION RULES FOR ENGINEERED WOOD:
            
            LAMINATED STRUCTURAL TIMBER (distinguish carefully):
            • `glue_laminated_timber` — Glulam: multiple timber laminations bonded IN THE THICKNESS direction
              to create larger cross-sections (beams, columns, arches). Laminations typically 20-45mm thick.
              Keywords: "glulam", "Brettschichtholz", "BSH", "GL24", "GL28", "GL32", "laminated beam".
              
            • `finger_jointed_structural_timber` — Solid timber pieces joined END-TO-END with finger joints
              to extend LENGTH. The cross-section remains similar to solid timber. Used for studs, joists.
              Keywords: "finger jointed", "finger-jointed", "KVH", "Keilgezinktes Vollholz", 
              "length-jointed", "end-jointed timber".
              
            • `cross_laminated_timber` — CLT: layers of timber boards stacked with alternating grain directions
              (crosswise), forming large panels. Used for walls, floors, roofs.
              Keywords: "CLT", "cross-laminated", "Brettsperrholz", "BSP", "X-Lam", 
              "3-Schicht-Platte", "5-Schicht-Platte", "Massivholzplatte".
            
            • `laminated_veneer_lumber` — LVL: thin veneers (2-4mm) glued with parallel grain. Structural.
              Keywords: "LVL", "laminated veneer", "Furnierschichtholz".
            
            PANEL PRODUCTS:
            • `plywood` — Cross-laminated veneers (alternating grain like CLT but from thin veneers).
            • `oriented_strand_board` — OSB: oriented wood strands bonded with resin.
            • `particleboard` — Wood particles bonded with resin.
            • `medium_density_fiberboard` — MDF: fine wood fibers.
            • `high_density_fiberboard` — HDF: denser than MDF.
            
            INSULATION:
            • `wood_fibre` — Rigid or flexible wood fiber insulation boards.
            • `wood_wool` — Mineral-bonded wood wool boards (Heraklith-type).
            • `cellulose` — Loose-fill or blown cellulose insulation.
            
            NATURAL WOOD:
            • `natural_softwood` — Solid softwood (spruce, pine, fir, larch).
            • `natural_hardwood` — Solid hardwood (oak, beech, ash, birch).
            • `modified_wood` — Thermally or chemically modified wood (Accoya, Thermowood).
        """).strip(),
    )
    wood_form: WoodForm = Field(
        WoodForm.unknown,
        description=dedent("""
            Physical form or geometric configuration of the wood-based product. 
            Describes how the wood material appears in its final product state
        """).strip(),
        examples=["panel", "beam", "flooring"]
    )
    strength_class_designation: Optional[str] = Field(
        None,
        description=dedent("""
            Strength class designation per European standards.
            Typical values include EN 338 solid timber classes (softwood 'C' and hardwood 'D'),
            e.g. 'C24', 'D40', and EN 14080 glulam classes with suffix 'c' (combined) or 'h' (homogeneous),
            e.g. 'GL28c', 'GL32h'. Use None when not clearly stated or not applicable (e.g. panels like OSB/MDF).
        """).strip(),
        examples=["C24", "D40", "GL28c", "GL32h"]
    )
    base_species: Optional[BaseSpecies] = Field(
        None,
        description=dedent("""
            Dominant wood species or species group used as the raw material basis for the product. 
            Refers to the primary botanical source of the lignocellulosic material.
        """).strip(),
        examples=["spruce", "larch", "oak", "other"]
    )
    wood_processing: Optional[WoodProcessing] = Field(
        None,
        description=dedent("""
            Primary processing state or manufacturing treatment applied to the wood material. 
            Refers to how the wood has been converted or finished from its raw form.
        """).strip(),
        examples=["rough_sawn", "planed_surfaced", "machine_graded"]
    )
    wood_adhesive: Optional[WoodAdhesive] = Field(
        None,
        description=dedent("""
            Adhesive system (primarily used in engineered wood products). 
            Adhesives determine moisture resistance and durability of the product.
            Only if the material explicitly has an adhesive system, otherwise None.
        """).strip(),
        examples=["MUF", "pMDI", "PF"]
    )
    drying_method: Optional[DryingMethod] = Field(
        None,
        description="The method used to reduce the moisture content of the wood prior to use or further processing.",
        examples=["fresh_green", "air_dried", "vacuum_dried"]
    )
    wood_surface: Optional[WoodSurface] = Field(
        None,
        description=dedent("""
            Describes the surface coating or finishing treatment applied to the wood-based product. 
            Indicates whether the surface is treated for aesthetic appearance or protective performance. 
            This field captures the final visible and tactile surface condition of the wood material.
        """).strip(),
        examples=["oiled", "glazed", "untreated"]
    )
    modification_method: Optional[ModificationMethod] = Field(
        None,
        description="The chemical, thermal, or physical process used to alter the properties of the wood material.",
        examples=["thermally_modified", "acetylated", "other"]
    )