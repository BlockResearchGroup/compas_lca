from typing import Optional

from textwrap import dedent

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import MineralType
from compas_lca.enums import MineralForm

class MineralFacet(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    mineral_type: MineralType = Field(
        MineralType.unknown,
        description=dedent("""
            Dominant material composition or geological origin of the mineral-based product. 
            Classifies the substance according to its raw mineral type or source — such as binders 
            (lime, gypsum, cement), earth- or rock-derived materials (clay, sand, stone), 
            fired ceramics, glass, or industrial minerals. 
            This attribute reflects the material's intrinsic composition, not its geometric form.
            
            DISAMBIGUATION RULES (choose the most specific match):
            
            INSULATION TYPES:
            • `rock_wool` — Mineral fiber insulation made specifically from basalt or volcanic rock.
              Keywords: "rock wool", "stone wool", "basalt wool", "Steinwolle", "ROCKWOOL".
            • `mineral_wool` — Generic mineral fiber insulation when the specific source (rock vs glass) 
              is NOT indicated. Use only as fallback when neither rock nor glass wool is specified.
            • `glass_wool` — Mineral fiber insulation made from recycled glass or silica sand.
              Keywords: "glass wool", "fiberglass", "Glaswolle".
            • `foam_glass` — Cellular/foamed glass with enclosed air pockets. Rigid boards or granules.
              Keywords: "foam glass", "cellular glass", "foamed glass", "Schaumglas".
            • `glass` — Solid glass products (panes, fibers, containers). NOT foamed.
              Use `glass` only for non-cellular glass products.
            
            CERAMICS:
            • `stoneware` — Vitrified/high-fired ceramics (fired >1200°C), dense and impermeable.
              Keywords: "stoneware", "vitrified", "Steinzeug", "klinker".
            • `clay` — Unfired clay or low-fired clay products (<1100°C), porous.
              Keywords: "clay", "brick", "terracotta", "earthenware", "Ziegel", "Ton".
            • `earthenware` — Low-fired porous ceramics.
            • `porcelain` — High-fired fine ceramics (sanitary ware, tiles).
            
            BINDERS (use for raw binder materials, not finished products):
            • `cement` — Portland cement or other hydraulic cements as raw material.
            • `lime` — Calcium oxide/hydroxide products (quicklime, hydrated lime, lime putty).
            • `gypsum` — Calcium sulfate products (gypsum powder, plaster).
            • `lime_cement` — Blended lime-cement binders.
            • `gypsum_lime` — Blended gypsum-lime products.
            
            Use the MOST SPECIFIC type available. Prefer `rock_wool` over `mineral_wool` when basalt/rock 
            origin is indicated. Prefer `foam_glass` over `glass` when cellular structure is mentioned.
        """).strip(),
    )
    mineral_form: Optional[MineralForm] = Field(
        None,
        description=dedent("""
            Physical form or product configuration in which the mineral material appears. 
            Describes how the material is manufactured, shaped, or applied — referring to geometry 
            or product form rather than its chemical composition.

            Values and definitions:
            • `powder` — Dry, fine powder materials (e.g., cement, lime, gypsum, dry premix).
            • `granulate` — Discrete grains or pellets (e.g., expanded perlite or vermiculite, foam-glass granules).
            • `aggregate` — Bulk granular material such as sand, gravel, or crushed stone. Grading is captured elsewhere.
            • `paste_slurry` — Wet paste or slurry forms (e.g., ready-to-use mineral pastes, slurries).
            • `masonry_unit` — Discrete structural units for masonry (e.g., clay bricks, calcium-silicate blocks, AAC units).
            • `paver_unit` — Discrete paving units such as stones, flags, or curbs (stone, fired, or cast products).
            • `tile` — Thin plate-like units for floor, wall, or roof coverings (ceramic, stone, or slate tiles).
            • `board` — Flat sheets or panels (e.g., gypsum board, cement or fiber-cement board, stone panels).
            • `glass_pane` — Monolithic flat glass products (float, patterned, or toughened glass). 
            • `plate` — Thick natural-stone slabs or plates (e.g., dimension stone, countertops, façade plates).
            • `batt` — Semi-rigid mineral wool or glass wool mats (batts).
            • `blanket_roll` — Flexible mineral or glass wool rolls.
            • `loose_fill` — Pourable or blown-in mineral insulation (e.g., perlite, vermiculite, mineral wool flakes).
            • `spray_applied_fiber` — Sprayed or blown mineral-fiber insulation systems.
            • `pipe_section` — Pre-formed insulation shells or half-shells for pipes (mineral wool or foam glass).
            • `mass_cast` — Cast or monolithic mineral product installed in place (e.g., cast stone, grout fills).
            • `other` — For any mineral-based product form not covered above.

            Choose the value that best describes the *physical configuration* of the mineral material as 
            it appears in manufacture or application.
        """).strip(),
        examples=["masonry_unit", "board", "aggregate"]
    )
