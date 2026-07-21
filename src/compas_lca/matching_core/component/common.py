from textwrap import dedent

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from compas_lca.enums import ComponentType


class ComponentCommon(BaseModel):
    """
    Shared fields for all types of construction components (pre-assembled elements with multiple materials)
    note: Rather sparse for now, to be extended in the future
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True, str_strip_whitespace=True)
    component_type: ComponentType = Field(
        ComponentType.unknown,
        description=dedent("""
            The type of component described in the dataset.
            
            IMPORTANT: Only use these categories if the product is already classified as COMPONENT (entry_type).
            Raw materials (single material products) should NOT reach this classification.
            
            COMPONENT TYPE DISAMBIGUATION:
            
            - window: Complete window assembly with frame + glazing + hardware, operating as a functional unit.
              Must include BOTH frame and glazing elements described together.
              keywords: window unit, window system, Fenster, fenêtre, window assembly
              NOT: raw aluminum/PVC profiles (those are materials), not window fittings
            
            - infill: ASSEMBLED glazing products designed for openings - multi-pane/multi-layer glass units.
              ONLY includes assembled glass products:
                • IGU (insulating glass unit) with spacers and gas fill
                • Double/triple glazing assemblies
                • Glass blocks (assembled units)
              DOES NOT INCLUDE (these are MATERIALS, not infill):
                • Single glass panes (float, laminated, toughened, safety glass)
                • Individual glass sheets/panels
              keywords: IGU, insulating glass, double glazing, triple glazing, Isolierglas, vitrage isolant
            
            - insulation_element: Multi-material thermal/acoustic products with DISTINCT material layers.
              MUST combine multiple DIFFERENT material families:
                • Sandwich panels with metal facings + foam/wool core
                • ETICS/WDVS systems (insulation + mesh + render)
                • Masonry units with integrated insulation fill
                • Insulation boards "with aluminium facing" or "with reinforced facing"
              keywords: sandwich panel, ETICS, WDVS, composite insulation, Sandwichpaneel,
                       "with aluminium facing", "with metal facing", "multi-layer"
              NOT: Single-material insulation boards (EPS, XPS, mineral wool, PU foam) - those are materials
            
            - door: Complete door assembly with frame + leaf/panel + hardware.
              keywords: door unit, door system, Tür, porte, door assembly
            
            - curtain_wall: Complete facade system with framing + infill panels as integrated assembly.
              Must be described as a complete facade/curtain wall system.
              keywords: curtain wall, facade system, Vorhangfassade, mur-rideau, Fassadensystem
              NOT: individual facade profiles or panels (those are materials)
            
            - roof: Pre-assembled roof system or module with multiple components.
              keywords: roof system, roofing assembly, Dachsystem
            
            - ceiling: Suspended ceiling system with grid + tiles/panels, OR acoustic ceiling panels.
              keywords: ceiling system, suspended ceiling, Deckenverkleidung, plafond suspendu,
                       acoustic ceiling, Akustikdecke, ceiling tile system
            
            - shading_device: External/internal shading systems.
              keywords: blinds, louvers, shutters, awning, Jalousie, Sonnenschutz, store
            
            - building_service: MEP equipment and systems.
              keywords: HVAC, lighting, solar panel, heat pump, ventilation
            
            - stairs: Pre-fabricated stair system.
            
            - railing: Balustrade or guard rail system.
            
            - conveyor: Elevator or escalator system.
            
            - window_fitting: ONLY hardware and accessories for windows/doors.
              ONLY includes:
                • Handles, hinges, locks, latches
                • Seals, gaskets, weatherstripping
                • Window/door hardware sets
              DOES NOT INCLUDE (these are MATERIALS):
                • Aluminum profiles, extrusions
                • PVC profiles
                • Steel sections
                • Raw metal sheets/tubes
              keywords: handle, hinge, lock, seal, gasket, fitting, hardware, Beschlag, Griff
            
            KEY DISTINCTIONS:
            • infill = ASSEMBLED glazing (IGU, multi-pane) - NOT single glass panes
            • insulation_element = multi-MATERIAL-FAMILY thermal product - NOT single-material insulation
            • window_fitting = HARDWARE ONLY - NOT raw profiles or materials
            • curtain_wall = complete facade SYSTEM - NOT individual facade panels
            • Single glass panes, metal profiles, pure insulation boards → classify as MATERIAL first!
        """).strip(),
    )
