from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from textwrap import dedent

from compas_lca.enums import EntryType

from compas_lca.validators import DensityFloat
from compas_lca.validators import ArealDensityFloat
from compas_lca.validators import ThicknessFloat
from compas_lca.validators import UValueFloat
from compas_lca.validators import LambdaFloat
from compas_lca.validators import LoadbearingType
from compas_lca.validators import InteriorExteriorType

class Common(BaseModel):
    """Shared fields for all types for all materials or components"""
    model_config = ConfigDict(
        extra = "forbid",
        validate_assignment=True,
        str_strip_whitespace=True
    )
    entry_type: EntryType = Field(
        ...,
        description=dedent("""
        Classify the dataset as MATERIAL, COMPONENT, or UNKNOWN.
        
        DEFINITIONS:
        • MATERIAL: A single homogeneous substance or uniform layer defined by physical/chemical nature.
          Includes monolithic integrated composites (reinforced concrete, fiber-cement, WPC) that are
          NOT installed as functional units by themselves.
          Single glass panes = MATERIAL (unless multi-pane IGU with spacers/gas fill).
          
        • COMPONENT: A manufactured assembly or device installed as a functional building element.
          Must involve MULTIPLE distinct materials or separable parts.
          Examples: window units (frame+glass+seals), door assemblies, ceiling systems (tiles+grid),
          sandwich panels (metal facing+insulation core), ETICS systems, HVAC devices.
        
        DECISION ORDER (apply top-to-bottom):
        1) Single material or uniform layer (even if pre-formed as sheet/panel/block/profile) → `material`
        2) Functional element with MULTIPLE distinct material families combined → `component`
        3) Insufficient or contradictory information → `unknown`
        
        KEY SIGNALS FOR COMPONENT (multi-material assembly):
        • Product name mentions "with ... facing/cladding/core" (e.g., "PU boards with aluminium facing")
        • Contains terms like "sandwich", "composite panel", "ETICS", "WDVS", "IGU", "insulating glass"
        • Multiple distinct material families listed together (e.g., metal + foam, glass + spacer + gas)
        • Complete assembled units: window system, door system, ceiling system, curtain wall
        
        KEY SIGNALS FOR MATERIAL (single/homogeneous):
        • Only ONE material family mentioned even if product form varies (sheet, panel, board, profile)
        • Raw material profiles, sheets, boards from one substance
        • Individual glass panes (float, laminated, toughened, safety glass) - NOT multi-pane assemblies
        • Pure insulation products from one material (PU foam, EPS, XPS, mineral wool, hemp, etc.)
        • Metal profiles, sheets, tubes (aluminum, steel) even if shaped/formed
        
        CLASSIFY AS MATERIAL (not component):
        • Steel beams, columns, profiles (single material, even if "structural element")
        • Aluminum profiles, sheets, extrusions (single metal - NOT window fittings unless hardware)
        • Concrete panels, blocks, precast elements (unless with DIFFERENT insulation core)
        • Single glass panes (monolithic, laminated, toughened, safety glass - NOT multi-pane IGU)
        • Metal roofing sheets, cladding panels (single material)
        • Insulation boards from ONE material (EPS, XPS, PU, PIR, mineral wool, wood fiber, hemp)
        • Precast concrete (reinforcement is integral, not a separate material layer)
        • PVC profiles, pipes, sheets (single polymer)
        
        CLASSIFY AS COMPONENT:
        • Window/door units with frame + glazing + hardware
        • Sandwich panels with metal facings + foam/wool core (DIFFERENT materials)
        • Insulation boards "with aluminium/metal facing" or "with reinforced facing"
        • Ceiling systems with tiles + suspension grid
        • ETICS/WDVS systems (insulation + adhesive + mesh + render)
        • IGUs (multi-pane glazing with spacers and gas fill)
        • Masonry units with integrated insulation fill
        
        NAMING TRAPS - these words ALONE do NOT make it a component:
        "unit", "system", "module", "device", "structure", "block", "frame", "element", "panel"
        Always check if multiple DISTINCT material families are combined.
        """).strip(),
    )
    name: str = Field(
        ...,
        description=dedent("""
        Exact material OR component name as found in the raw dataset.
        Depending on if the dataset describes materials or components,
        extract the material or component/element name VERBATIM.
        """).strip(),
    )
    loadbearing: LoadbearingType = Field(   # enforce a value, important indicator (unless this is too risky)
        LoadbearingType.non_loadbearing,
        description=dedent("""
        Classify whether the product/material is intended for structural loadbearing use.

        Decision order (apply the first rule that matches):
        1) If the dataset explicitly states "non-structural", "non-loadbearing", or the product is a category that is never structural
        (e.g., plasters, insulation, windows, doors, paints/coatings, floor finishes, screeds, sealants, membranes), set 'non_loadbearing'.
        2) If the dataset explicitly states structural intent (e.g., mentions strength classes/grades or structural use
        per a standard), set 'loadbearing'.
        3) If the document explicitly says the product/material is suitable for both structural and non-structural applications
        (e.g., a family with both variants), set 'either'.
        4) If the dataset does not explicitly state structural intent, but the generic material class is one that is routinely used in 
        structural applications (e.g., ready-mixed concrete, structural-grade timber), classify as "either".
        """).strip(),
    )
    placement: Optional[InteriorExteriorType] = Field(      # should a value be enforced?
        None,
        description=dedent("""
        Classify whether the product, material, or building element is explicitly intended for
        **interior** or **exterior** use, or if it can be **either**.

        Decision order (apply the first rule that matches):
        1) If the dataset explicitly states "interior use", "for indoor applications", or similar wording → set 'interior'.
        2) If the dataset explicitly states "exterior use", "outdoor application", or refers to weather, UV, or moisture exposure classes → set 'exterior'.
        3) If the dataset explicitly says the product/material is suitable for both indoor and outdoor use → set 'either'.
        4) If placement can be reliably inferred from the product type or context (implicit cues), apply:
        - **Exterior (implicit)**: façade systems, roof membranes, exterior paints/coatings, cladding, sealants, external insulation (ETICS),
            drainage layers, exterior-grade timber, concrete exposed to weather, roofing sheets, paving materials, exterior windows and doors.
        - **Interior (implicit)**: interior paints/coatings, gypsum boards, plasters, screeds, interior flooring, carpets, wallpapers, ceiling panels,
            furniture materials, MEP components located inside conditioned spaces.
        5) If none of the above apply and placement cannot be confidently inferred → leave empty.
        """).strip(),
    )
    density: Optional[DensityFloat] = Field(
        None,
        ge=0,
        description=dedent("""
            The volumetric density of the material/component, expressed in kilograms per cubic metre (kg/m³).
            If the source dataset specifies a range, compute and assign the average value.
        """).strip(),
        examples=[24.0, 350.8, 2850.0]
    )
    areal_density: Optional[ArealDensityFloat] = Field(
        None,
        ge=0,
        description=dedent("""
            The numeric value of the areal (surface) density of the material/component, expressed in kilograms per square metre (kg/m²).
            Use this for materials where mass is reported per area.
            If the source dataset specifies a range, compute and assign the average value.
        """).strip(),
        examples=[0.85, 12.0]
    )
    thickness: Optional[ThicknessFloat] = Field( # removed "thickness source", speculated values are traced in enrichment module logs
        None,
        ge=0,
        description=dedent("""
        The numeric value of the thickness (in milimeters) of the material or component dataset.
        If the source dataset specifies a range, compute and assign the average value.
        """).strip(),
        examples=[0.5, 5.0, 18.0]
    )
    thermal_conductivity: Optional[LambdaFloat] = Field(
        None,
        ge=0,
        description=dedent("""
        The float value of the thermal conductivity (lambda) of the material or component in W/mk.
        If the source dataset specifies a range, compute and assign the average value.
        """).strip(),
        examples=[0.3, 1.4, 2.0]
    )
    u_value: Optional[UValueFloat] = Field(
        None,
        ge=0,
        description=dedent("""
        The float value of the U-Value of the component in W/m^2K.
        If the source dataset specifies a range, compute and assign the average value.
        """).strip(),
        examples=[0.5, 1.1, 1.4]
    )
    fire_retardant: Optional[bool] = Field(
        None,
        description=dedent("""
        This boolean value describes if the material or component is fire retardant (True) or inflammable (False)
        Assign a boolean value if this information is explicitly stated in the input dataset,
        or if the value is unambiguously clear (common sense).
        """).strip(),
        examples=[True, False]
    )
    water_vapour_resistant: Optional[bool] = Field(
        None,
        description=dedent("""
        This field describes if the material or component is resistant against water vapour (True) or very permeable (False).
        Assign a boolean value if this information is explicitly stated in the input dataset,
        or if the value is unambiguously clear (common sense).
        """).strip(),
        examples=[True, False]
    )
    manufacturer: Optional[str] = Field(
        None,
        description=dedent("""
        The manufacturer or brand name, taken verbatim from the source dataset if available.
        If no manufacturer is specified, leave this field as null (None).
        Careful: do not mistake the "owner of the dataset" with the manufacturer, they are not always the same.
        """).strip(),
        examples=["Knauf", "Holcim", "EcoWorx"]
    )
    provenance: Optional[str] = Field(
        None,
        description=dedent("""
        A regional or country code indicating the geographic provenance or data scope of the material/component.
        Examples include ISO country codes (e.g., "DE" for Germany, "CH" for Switzerland)
        or broader regional groupings (e.g., "EU-27", "GLO" for global).
        If no provenance is specified in the dataset, leave this field as null (None).
        """).strip(),
        examples=["GB", "TW", "GLO", "DE", "CH", "EU-27"]
    )
    production_location: Optional[str] = Field(
        None,
        description=dedent("""
        The exact place/city/area of the plant or factory where the material or component was produced.
        If this is not explicitly stated in the dataset, leave this field as null (None).
        """).strip(),
        examples=["Rüdersdorf", "Jerez de la Frontera", "Bulacan"]
    )