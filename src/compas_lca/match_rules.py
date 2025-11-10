
"""
--- UNIFIED RULES SCHEMA -----------------------------------------------------

--------------------------
Supported Clause Operators
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


TO DO: If all OBD has been extracted, we should do a test to see which attributes
and fields have the most impact on the emissions. if those fields are not crucial
for functional and semantic accuracy, but have high impact on emissions, we should
weigh them more strongly. If they do not have high impact on emissions, then they
are miscellaneous, and the weights should reflect this.
"""



# =========================
# MATCH RULES (3 hierarchies)
# =========================
# Level 1: common -> always evaluated (unless element is "unknown" → hard fail)
# Level 2: specific_common -> depends on entry_type ("material" or "component"). hard fail if material_type or component_type is unknown
# Level 3: facet -> material facets (metallic/concrete) OR component facets (scaffolded)

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
            "name": "common.manufacturer", 
            "path": "manufacturer", 
            "op": "equals_other", # should be fuzzy matching
            # overspec included such that overspecific products
            # are less prioritized than generic averages in EPDs
            "overspec":{"strength":0.15} 

        },
        {
            "name": "common.production_location", 
            "path": "production_location", 
            "op": "equals_other", # should be fuzzy matching
            # overspec included such that overspecific products
            # are less prioritized than generic averages in EPDs
            "overspec":{"strength":0.15} 

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
            "path": "fire_redardant",
            "op": "equals_other",
            "overspec":{"strength":0.25} 
        },
        {
            "name": "common.water_vapour_resistant",
            "path": "water_vapour_resistant",
            "op": "equals_other",
            "overspec":{"strength":0.25} 
        },
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
            # if element is missing 'facet.material_type', add this clause 2 extra times
            # especially relevant for generic element descriptors like "plaster" or "insulation"
            "boost_if_missing": {"facet.material_type": 2}
        },
        {   "name": "material_common.application_areas", 
            "path": "facet.application_areas", 
            "op": "intersects_other"
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
            "op":"equals_other"
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
            "op":"equals_other",
            "overspec":{"strength":0.25} # comp architecture might be misleading depending on element
        },
    ], 
    "concrete": [
        {
            "name":"concrete.type",     
            "path":"facet.material_facet.concrete_type",  
            "op":"equals_other",
        },
        {
            "name":"concrete.form",  
            "path":"facet.material_facet.concrete_form",                       
            "op":"equals_other", 
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
            "name":"concrete.strength", 
            "path":"facet.material_facet.strength_class", 
            "op":"equals_other", # here there should definitely be some rule that too high strength class for niches should be punished
        },

        {
            "name":"concrete.strength_class",       
            "path":"facet.material_facet.strength_class",             
            "op":"equals_other"
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
            "overspec":{"strength":0.05}
        },
        {
            "name":"concrete.xd",       
            "path":"facet.material_facet.xd",             
            "op":"equals_other",
            "overspec":{"strength":0.05}
        },
        {
            "name":"concrete.xs",       
            "path":"facet.material_facet.xd",             
            "op":"equals_other",
            "overspec":{"strength":0.05}
        },
        {
            "name":"concrete.xf",       
            "path":"facet.material_facet.xf",             
            "op":"equals_other",
            "overspec":{"strength":0.05}
        },
        {
            "name":"concrete.xa",       
            "path":"facet.material_facet.xa",             
            "op":"equals_other",
            "overspec":{"strength":0.05}
        },
    ],
    "ligneous": [
        {
            "name":"ligneous.type",     
            "path":"facet.material_facet.ligneous_type",  
            "op":"equals_other"
        },
        {
            "name":"ligneous.form",     
            "path":"facet.material_facet.ligneous_form",  
            "op":"equals_other"
        },
        {
            "name":"ligneous.strength_class",     
            "path":"facet.material_facet.strength_class_designation",  
            "op":"equals_other"
        },
        {
            "name":"ligneous.base_species",     
            "path":"facet.material_facet.base_species",  
            "op":"equals_other"
        },
        {
            "name":"ligneous.processing",     
            "path":"facet.material_facet.ligneous_processing",  
            "op":"equals_other"
        },
        {
            "name":"ligneous.processing",     
            "path":"facet.material_facet.ligneous_processing",  
            "op":"equals_other"
        },
        {
            "name":"ligneous.adhesive",     
            "path":"facet.material_facet.ligneous_adhesive",  
            "op":"equals_other"
        },
        {
            "name":"ligneous.drying_method",     
            "path":"facet.material_facet.drying_method",  
            "op":"equals_other"
        },
        {
            "name":"ligneous.drying_method",     
            "path":"facet.material_facet.drying_method",  
            "op":"equals_other"
        },
        {
            "name":"ligneous.modification_method",     
            "path":"facet.material_facet.modification_method",  
            "op":"equals_other",
            "overspec":{"strength":0.15}
        },
    ], 
    "metallic": [
        {
            "name":"metallic.type",     
            "path":"facet.material_facet.metallic_type",  
            "op":"equals_other"
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
            "op":"equals_other"
        },
        {
            "name":"metallic.forming",  
            "path":"facet.material_facet.metallic_forming",
            "op":"equals_other"
        },
        {
            "name":"metallic.surface",  
            "path":"facet.material_facet.metallic_surface_treatment",
            "op":"equals_other",
            "overspec":{"strength":0.20}
        },
    ],
    "mineral": [
        {
            "name":"mineral.type",     
            "path":"facet.material_facet.mineral_type",  
            "op":"equals_other"
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
            "op":"equals_other"
        }
    ],
    "ceiling": [
        {
            "name":"ceiling.type",     
            "path":"facet.component_facet.ceiling_type",  
            "op":"equals_other"
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
            "op":"equals_other"
        }
    ],
    "curtain_wall": [
        {
            "name":"curtain_wall.type",     
            "path":"facet.component_facet.curtain_wall_type",  
            "op":"equals_other"
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
            "on_missing":"neutral"
        },
        {
            "name":"door.automatization,",     
            "path":"facet.component_facet.door_automatization",  
            "op":"equals_other",
            "overspec":{"strength":0.25}
        },
        {
            "name":"door.height,",     
            "path":"facet.component_facet.door_height",  
            "op": "approx", 
            "abs_tol": 100, # mm
            "overspec":{"strength":0.20}
        },
        {
            "name":"door.width,",     
            "path":"facet.component_facet.door_width",  
            "op": "approx", 
            "abs_tol": 100, # mm
            "overspec":{"strength":0.20}
        }
    ],
    "railing": [
        {
            "name":"railing.type",     
            "path":"facet.component_facet.railing_type",  
            "op":"equals_other"
        }
    ],
    "roof": [
        {
            "name":"roof.type",     
            "path":"facet.component_facet.roof_type",  
            "op":"equals_other"
        }
    ],
    "shading_device": [
        {
            "name":"shading_device.type",     
            "path":"facet.component_facet.shading_device_type",  
            "op":"equals_other"
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
            "op":"equals_other"
        },
        {
            "name":"window.acoustic_interlayer",     
            "path":"facet.component_facet.acoustic_interlayer",  
            "op":"equals_other",
            "overspec":{"strength":0.25}
        },
        {
            "name":"window.height",     
            "path":"facet.component_facet.window_height",  
            "op": "approx", 
            "abs_tol": 100, # mm
            "overspec":{"strength":0.20}
        },
        {
            "name":"window.width",     
            "path":"facet.component_facet.window_width",  
            "op": "approx", 
            "abs_tol": 100, # mm
            "overspec":{"strength":0.20}
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


# ----------------------------
# IDEA FOR WEIGHTS AND MODES FOR FILTERING (IMPLEMENT LATER)
# ----------------------------
"""
----------------------------
Modes and Weights
----------------------------
You typically choose weights and tolerances per matching *mode*:
    • strict   — verify near-identity: higher weights on identity features
                (e.g., material_type, metallic_type, steel_grade), tight tolerances.
    • balanced — functional equivalence: same core identity, moderate tolerances,
                more even distribution across functional/quantitative cues.
    • broad    — discovery: keep only a few key features non-zero, set others
                to zero weight to avoid over-constraining early candidate search.

In short: weights say where to care; the mode says how much to forgive.
"""

FAMILY = {
    "identity": {
        "keys": {
            "entry_type",
            "facet.material_type",
            "facet.material_facet.*type",
            "facet.material_facet.strength_class",
            "facet.material_facet.steel_grade",
        }
    },
    "function": {
        "keys": {
            "facet.functional_types",
            "facet.application_areas",
            "placement",
            "loadbearing",
        }
    },
    "performance": {
        "keys": {
            "thickness",
            "facet.density",
            "facet.material_facet.yield_strength",
            "u_value",
            "thermal_conductivity",
            "facet.material_facet.sd_value",
        }
    },
    "context": {
        "keys": {
            "manufacturer",
            "provenance",
            "production_location",
            "facet.material_facet.*surface*",
        }
    },
}

FAMILY_CAP = {
    "strict":   {"identity":0.55, "function":0.25, "performance":0.15, "context":0.05},
    "balanced": {"identity":0.45, "function":0.30, "performance":0.20, "context":0.05},
    "broad":    {"identity":0.35, "function":0.55, "performance":0.05, "context":0.05},
}


def assign_mode_weights_from_families(rules_by_group: dict, family_cap: dict, modes=("strict","balanced","broad")):
    """
    Mutates rules_by_group[group][i]["weights"][mode] based on:
      - rule["family"] in {"identity","function","performance","context"}
      - rule["base_weight"] (default=1.0 within family)
      - per-mode FAMILY_CAP (the family totals per mode)
    """
    # Flatten
    all_rules = []
    for group, rules in rules_by_group.items():
        for r in rules:
            r.setdefault("weights", {})
            r.setdefault("base_weight", 1.0)
            all_rules.append(r)

    # Group by family
    fam_to_rules = {}
    for r in all_rules:
        fam = r.get("family", "context")
        fam_to_rules.setdefault(fam, []).append(r)

    # For each mode, distribute the cap across rules in each family
    for mode in modes:
        for fam, cap in family_cap[mode].items():
            lst = fam_to_rules.get(fam, [])
            if not lst or cap <= 0:
                # Zero-out mode weights for this family
                for r in lst:
                    r["weights"][mode] = 0.0
                continue

            total_base = sum(max(0.0, float(r.get("base_weight", 1.0))) for r in lst)
            if total_base <= 0:
                for r in lst:
                    r["weights"][mode] = 0.0
                continue

            for r in lst:
                share = max(0.0, float(r.get("base_weight", 1.0))) / total_base
                r["weights"][mode] = cap * share

    # (Optional) global normalize per mode to sum to 1.0 for readability
    for mode in modes:
        total = sum(max(0.0, float(r["weights"].get(mode, 0.0))) for r in all_rules)
        if total > 0:
            for r in all_rules:
                r["weights"][mode] = float(r["weights"].get(mode, 0.0)) / total

    return rules_by_group


# At startup (after MATCH_RULES is defined):
assign_mode_weights_from_families(MATCH_RULES, FAMILY_CAP)
# From here on, pipeline can read rule["weights"][mode] as before.
