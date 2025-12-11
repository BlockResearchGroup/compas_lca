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
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    component_type: ComponentType = Field(
        ComponentType.unknown,
        description=dedent("""
            The type of component described in the dataset.
            
            COMPONENT TYPE DISAMBIGUATION:
            
            - window: Complete window assembly with frame + glazing + hardware, operating as a functional unit.
              Must include BOTH frame and glazing elements described together.
              keywords: window unit, window system, Fenster, fenêtre
            
            - infill: Transparent/translucent panels designed for openings - the GLAZING PRODUCT itself.
              Includes: IGU (insulating glass unit), glass blocks, polycarbonate sheets for glazing.
              Does NOT include single glass panes (those are materials).
              Must be multi-pane or multi-layer glazing product.
              keywords: IGU, insulating glass, double glazing, triple glazing, Isolierglas, vitrage isolant
            
            - insulation_element: Multi-material thermal/acoustic products with distinct layers.
              Includes: sandwich panels (metal-faced), ETICS systems, masonry units with insulation infill,
              layered-bonded insulation boards with different facing materials.
              Must combine multiple DIFFERENT material types for thermal function.
              keywords: sandwich panel, ETICS, WDVS, composite insulation, Sandwichpaneel
            
            - door: Complete door assembly with frame + leaf/panel + hardware.
              keywords: door unit, door system, Tür, porte
            
            - curtain_wall: Facade system with framing + infill panels.
              keywords: curtain wall, facade system, Vorhangfassade, mur-rideau
            
            - roof: Pre-assembled roof system or module with multiple components.
              keywords: roof system, roofing assembly, Dachsystem
            
            - ceiling: Suspended ceiling system with grid + tiles/panels.
              keywords: ceiling system, suspended ceiling, Deckenverkleidung, plafond suspendu
            
            - shading_device: External/internal shading systems.
              keywords: blinds, louvers, shutters, awning, Jalousie, Sonnenschutz, store
            
            - building_service: MEP equipment and systems.
              keywords: HVAC, lighting, solar panel, heat pump, ventilation
            
            - stairs: Pre-fabricated stair system.
            
            - railing: Balustrade or guard rail system.
            
            - conveyor: Elevator or escalator system.
            
            - window_fitting: Hardware and fittings for windows (handles, hinges).
            
            KEY DISTINCTIONS:
            • infill = glazing product (IGU, multi-pane glass assembly)
            • insulation_element = thermal product with multiple distinct material layers
            • window = complete window unit (frame + glazing + seals + hardware)
            • Single glass panes are MATERIALS, not components!
        """).strip(),
    )