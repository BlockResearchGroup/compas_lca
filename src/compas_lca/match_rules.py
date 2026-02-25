
"""
--- UNIFIED RULES SCHEMA -----------------------------------------------------

--------------------------
Supported Clause Operators ("op)
--------------------------

equals_other:
    Compare one item field directly to a corresponding element field.
    used for entry_type, component_type, material_type.

intersects_other:
    Compare list-type fields (e.g. `application_areas`, `functional_types`) and return 1.0
    if there is *any* overlap between the two sets.

approx:
    Numeric comparison with absolute or relative tolerance. Returns a *partial match* if
    the values are close but not identical.

satisfies:
    Directional categorical comparison for Enum-like fields such as `loadbearing` or `placement`.
    Accepts “either” as a wildcard.

--------------------------
Hard fail
--------------------------
"hard_fail": True signifies that if the operator is not satisfied, the entire item should receive a score of 0.0, 
regardless of other clauses. This is intended for critical fields where a mismatch would be unacceptable (e.g., `entry_type`, `material_type`, `component_type`).

"""


# =========================
# MATCH RULES (3 hierarchies)
# =========================
# Level 1: common -> always evaluated (unless element is "unknown" → hard fail)
# Level 2: specific_common -> depends on entry_type ("material" or "component"). hard fail if material_type or component_type is unknown
# Level 3: facet -> material facets (e.g., metallic/concrete) OR component facets (e.g., door/window)

MATCH_RULES = {
    "common": [
        {
            "name": "common.entry_type",
            "path": "entry_type", 
            "op": "equals_other",
        },
        {
            "name": "common.loadbearing", 
            "path": "loadbearing", 
            "op": "satisfies",
        },
        {
            "name": "common.placement", 
            "path": "placement", 
            "op": "satisfies",
        },
        {
            "name": "material_common.density", 
            "path": "facet.density", 
            "op": "approx", 
            "rel_tol": 0.10
        },
        {
            "name": "material_common.areal_density", 
            "path": "facet.areal_density", 
            "op": "approx", 
            "rel_tol": 0.10
        },
        {
            "name": "common.thickness", 
            "path": "thickness", 
            "op": "approx", 
            "rel_tol": 0.10,
        },
        {
            "name": "common.thermal_conductivity", 
            "path": "thermal_conductivity", 
            "op": "approx", 
            "rel_tol": 0.10,
        },
        {
            "name": "common.u_value", 
            "path": "u_value", 
            "op": "approx", 
            "rel_tol": 0.10,
        },
        {
            "name": "common.fire_retardant",
            "path": "fire_retardant",
            "op": "equals_other",
            "overspec": {"strength": 0.7},
        },
        {
            "name": "common.water_vapour_resistant",
            "path": "water_vapour_resistant",
            "op": "equals_other",
            "overspec": {"strength": 0.7},
        },
        {
            "name": "common.manufacturer", 
            "path": "manufacturer", 
            "op": "equals_other",
            "ignore": True,
        },
        {
            "name": "common.production_location", 
            "path": "production_location", 
            "op": "equals_other",
            "ignore": True,
        }
    ],

    # ----------------------------
    # specific_common: MATERIAL
    # ----------------------------
    "material_common": [
        {
            "name": "material_common.material_type", 
            "path": "facet.material_type", 
            "op": "equals_other"
        },
        {
            "name": "material_common.functional_types", 
            "path": "facet.functional_types", 
            "op": "intersects_other",
            "hard_fail": True
        },
        {   "name": "material_common.application_areas", 
            "path": "facet.application_areas", 
            "op": "intersects_other"
        },
        {   "name": "material_common.insulation_info", 
            "path": "facet.insulation_info", 
            "op": "intersects_other"
        }
    ],


    # ----------------------------
    # specific_common: COMPONENT
    # ----------------------------
    "component_common": [
        {
            "name": "component_common.component_type", 
            "path": "facet.component_type", 
            "op": "equals_other"
        }
    ],
}

# ----------------------------
# MATERIAL FACET RULES
# ----------------------------
MATERIAL_FACETS = {
    "bituminous": [
        {
            "name":"bituminous.type",     
            "path":"facet.material_facet.bituminous_type",  
            "op":"equals_other"
        },
        {
            "name":"bituminous.form",     
            "path":"facet.material_facet.bituminous_form",  
            "op":"equals_other"
        },
        {
            "name":"bituminous.sd_value",  
            "path":"facet.material_facet.sd_value",                       
            "op":"approx", 
            "rel_tol": 0.10
        },
    ],  
    "composite": [
        {
            "name":"composite.type",     
            "path":"facet.material_facet.composite_type",  
            "op":"equals_other",
            "hard_fail": True
        },
        {
            "name":"composite.matrix",     
            "path":"facet.material_facet.composite_matrix",  
            "op":"equals_other"
        },
        {
            "name":"composite.reinforcement",     
            "path":"facet.material_facet.composite_reinforcement",  
            "op":"equals_other"
        },
        {
            "name":"composite.form",     
            "path":"facet.material_facet.composite_form",  
            "op":"equals_other"
        },
        {
            "name":"composite.architecture",     
            "path":"facet.material_facet.composite_architecture",  
            "op":"equals_other"
        },
    ], 
    "concrete": [
        {
            "name":"concrete.type",     
            "path":"facet.material_facet.concrete_type",  
            "op":"equals_other",
            "hard_fail": True
        },
        {
            "name":"concrete.form",  
            "path":"facet.material_facet.concrete_form",                       
            "op":"equals_other", 
        },
        {
            "name":"concrete.prestressed",  
            "path":"facet.material_facet.pre_stressed",                       
            "op":"equals_other"
        },
        {
            "name":"concrete.binder_type",  
            "path":"facet.material_facet.cement_type",                       
            "op":"equals_other"
        },
        {
            "name":"concrete.cement_type",  
            "path":"facet.material_facet.cement_type",                       
            "op":"equals_other"
        },
        {
            "name":"concrete.strength_class",       
            "path":"facet.material_facet.strength_class",             
            "op":"equals_other",
            "hard_fail": True
        },
        {
            "name":"concrete.slump_class",       
            "path":"facet.material_facet.slump_class",             
            "op":"equals_other"
        },
        {
            "name":"concrete.flow_class",       
            "path":"facet.material_facet.flow_class",             
            "op":"equals_other"
        },
        {
            "name":"concrete.xc",       
            "path":"facet.material_facet.xc",             
            "op":"equals_other",
            "overspec": {"strength": 0.2},
        },
        {
            "name":"concrete.xd",       
            "path":"facet.material_facet.xd",             
            "op":"equals_other",
            "overspec": {"strength": 0.2},
        },
        {
            "name":"concrete.xs",       
            "path":"facet.material_facet.xd",             
            "op":"equals_other",
            "overspec": {"strength": 0.2},
        },
        {
            "name":"concrete.xf",       
            "path":"facet.material_facet.xf",             
            "op":"equals_other",
            "overspec": {"strength": 0.2},
        },
        {
            "name":"concrete.xa",       
            "path":"facet.material_facet.xa",             
            "op":"equals_other",
            "overspec": {"strength": 0.2},
        },
    ],
    "wood": [
        {
            "name":"wood.type",     
            "path":"facet.material_facet.wood_type",  
            "op":"equals_other",
            "hard_fail": True
        },
        {
            "name":"wood.form",     
            "path":"facet.material_facet.wood_form",  
            "op":"equals_other"
        },
        {
            "name":"wood.strength_class",     
            "path":"facet.material_facet.strength_class_designation",  
            "op":"equals_other"
        },
        {
            "name":"wood.base_species",     
            "path":"facet.material_facet.base_species",  
            "op":"equals_other"
        },
        {
            "name":"wood.processing",     
            "path":"facet.material_facet.wood_processing",  
            "op":"equals_other",
            "ignore": True,
        },
        {
            "name":"wood.adhesive",     
            "path":"facet.material_facet.wood_adhesive",  
            "op":"equals_other",
            "ignore": True,
        },
        {
            "name":"wood.drying_method",     
            "path":"facet.material_facet.drying_method",  
            "op":"equals_other",
            "ignore": True,
        },
        {
            "name":"wood.modification_method",     
            "path":"facet.material_facet.modification_method",  
            "op":"equals_other"
        },
    ], 
    "metallic": [
        {
            "name":"metallic.type",     
            "path":"facet.material_facet.metallic_type",  
            "op":"equals_other",
            "hard_fail": True
        },
        {
            "name":"metallic.form",     
            "path":"facet.material_facet.metallic_form",  
            "op":"equals_other"
        },
        {
            "name":"metallic.grade",    
            "path":"facet.material_facet.steel_grade",    
            "op":"equals_other"
        },
        {
            "name":"metallic.yield",    
            "path":"facet.material_facet.yield_strength", 
            "op":"approx", 
            "rel_tol":0.10
        },
        {
            "name":"metallic.production",
            "path":"facet.material_facet.metallic_production",
            "op":"equals_other",
            "ignore": True,
        },
        {
            "name":"metallic.forming",  
            "path":"facet.material_facet.metallic_forming",
            "op":"equals_other",
            "ignore": True,
        },
        {
            "name":"metallic.surface",  
            "path":"facet.material_facet.metallic_surface_treatment",
            "op":"equals_other",
            "overspec": {"strength": 0.7},
        },
    ],
    "mineral": [
        {
            "name":"mineral.type",     
            "path":"facet.material_facet.mineral_type",  
            "op":"equals_other",
            "hard_fail": True
        },
        {
            "name":"mineral.form",     
            "path":"facet.material_facet.mineral_form",  
            "op":"equals_other"
        },
    ], 
    "polymeric": [
        {
            "name":"polymeric.type",     
            "path":"facet.material_facet.polymeric_type",  
            "op":"equals_other"
        },
        {
            "name":"polymeric.form",     
            "path":"facet.material_facet.polymeric_form",  
            "op":"equals_other"
        },
    ]
}

# ----------------------------
# Level 3: COMPONENT FACETS (scaffold)
# ----------------------------
COMPONENT_FACETS = {
    "building_services": [
        {
            "name":"building_service.type",     
            "path":"facet.component_facet.building_service_type",  
            "op":"equals_other",
            "hard_fail": True
        }
    ],
    "ceiling": [
        {
            "name":"ceiling.type",     
            "path":"facet.component_facet.ceiling_type",  
            "op":"equals_other",
            "hard_fail": True
        },
        {
            "name":"ceiling.form,",     
            "path":"facet.component_facet.ceiling_form",  
            "op":"equals_other"
        }
    ],
    "conveyor": [
        {
            "name":"conveyor.type",     
            "path":"facet.component_facet.conveyor_type",  
            "op":"equals_other",
            "hard_fail": True
        }
    ],
    "curtain_wall": [
        {
            "name":"curtain_wall.type",     
            "path":"facet.component_facet.curtain_wall_type",  
            "op":"equals_other",
            "hard_fail": True
        },
        {
            "name":"curtain_wall.form,",     
            "path":"facet.component_facet.curtain_wall_form",  
            "op":"equals_other"
        }
    ],
    "door": [
        {
            "name":"door.type",     
            "path":"facet.component_facet.door_type",  
            "op":"equals_other"
        },
        {
            "name":"door.operation,",     
            "path":"facet.component_facet.door_operation",  
            "op":"equals_other"
        },
        {
            "name":"door.safety_function,",     
            "path":"facet.component_facet.safety_function",  
            "op":"equals_other",
            "overspec": {"strength": 0.7},
        },
        {
            "name":"door.automatization,",     
            "path":"facet.component_facet.door_automatization",  
            "op":"equals_other",
            "overspec": {"strength": 0.7},
        },
        {
            "name":"door.height,",     
            "path":"facet.component_facet.door_height",  
            "op": "approx", 
            "abs_tol": 200, # mm
        },
        {
            "name":"door.width,",     
            "path":"facet.component_facet.door_width",  
            "op": "approx", 
            "abs_tol": 200, # mm
        }
    ],
    "railing": [
        {
            "name":"railing.type",     
            "path":"facet.component_facet.railing_type",  
            "op":"equals_other",
            "hard_fail": True
        }
    ],
    "roof": [
        {
            "name":"roof.type",     
            "path":"facet.component_facet.roof_type",  
            "op":"equals_other",
            "hard_fail": True
        }
    ],
    "shading_device": [
        {
            "name":"shading_device.type",     
            "path":"facet.component_facet.shading_device_type",  
            "op":"equals_other",
            "hard_fail": True
        },
        {
            "name":"shading_device.material",     
            "path":"facet.component_facet.shading_device_material",  
            "op":"equals_other"
        }
    ],
    "stairs": [
        {
            "name":"stair.type",     
            "path":"facet.component_facet.stair_type",  
            "op":"equals_other"
        }
    ],
    "window": [
        {
            "name":"window.frame_type",     
            "path":"facet.component_facet.frame_type",  
            "op":"equals_other"
        },
        {
            "name":"window.glazing_count",     
            "path":"facet.component_facet.glazing_count",  
            "op":"equals_other"
        },
        {
            "name":"window.operation",     
            "path":"facet.component_facet.window_operation",  
            "op":"intersects_other"
        },
        {
            "name":"window.acoustic_interlayer",     
            "path":"facet.component_facet.acoustic_interlayer",  
            "op":"equals_other",
            "overspec": {"strength": 0.7},
        },
        {
            "name":"window.roof_window",     
            "path":"facet.component_facet.roof_window",  
            "op":"equals_other",
            "overspec": {"strength": 0.7},
        },
        {
            "name":"window.height",     
            "path":"facet.component_facet.window_height",  
            "op": "approx", 
            "abs_tol": 100, # mm
        },
        {
            "name":"window.width",     
            "path":"facet.component_facet.window_width",  
            "op": "approx", 
            "abs_tol": 100, # mm
        },
    ],
    "window_fitting": [
        {
            "name":"window_fitting.type",     
            "path":"facet.component_facet.window_fitting_type",  
            "op":"equals_other",
            "on_missing":"penalty"
        }
    ]
}