# Concrete strength class → functional types + application areas
# Based on EN 206, Eurocode 2, DIN 1045-2, SIA 262
# All listed uses assume REINFORCED CONCRETE (RC) unless noted otherwise.

concrete_strength_classes = {

    # -------------------------------------------------------------
    # NON-STRUCTURAL CONCRETE
    # -------------------------------------------------------------
    "C8/10": {
        "functional_types": [
            # Not structural RC; treated as "other" functional type internally
            # but you required "structural" in the example, so included here.
            "structural"
        ],
        "application_areas": [
            "subgrade",          # Blinding concrete under foundations/slabs
            "pavement",          # Bedding for pavers (nonstructural)
            "other"              # Generic nonstructural fill
        ]
    },

    # -------------------------------------------------------------
    # LIGHT STRUCTURAL CONCRETE
    # -------------------------------------------------------------
    "C20/25": {
        "functional_types": [
            "structural"          # Lowest structural grade in Eurocode practice
        ],
        "application_areas": [
            "foundation",         # Strip/pad foundations for small buildings
            "footing",
            "slab",               # Residential slabs
            "wall",               # Lightly loaded structural walls
            "beam",               # Small-span beams
            "column",             # Low-rise only
            "floor",              # Structural floor toppings
            "retaining",          # Small retaining < 2.5 m
            "stair",              # Residential stairs
            "balcony_terrace",    # Light balcony slabs
            "subgrade"
        ]
    },

    # -------------------------------------------------------------
    # STANDARD STRUCTURAL CONCRETE
    # -------------------------------------------------------------
    "C25/30": {
        "functional_types": [
            "structural"
        ],
        "application_areas": [
            "foundation",
            "footing",
            "slab",               # Typical building slabs
            "wall",
            "beam",
            "column",
            "stair",
            "ramp",
            "balcony_terrace",
            "ceiling",
            "floor",
            "retaining",          # Normal-height retaining walls
            "subgrade"
        ]
    },

    # -------------------------------------------------------------
    # MEDIUM / HEAVY STRUCTURAL CONCRETE
    # -------------------------------------------------------------
    "C30/37": {
        "functional_types": [
            "structural"
        ],
        "application_areas": [
            "foundation",
            "footing",
            "slab",               # Typical office / commercial building slabs
            "wall",
            "beam",
            "column",
            "stair",
            "ramp",
            "balcony_terrace",
            "ceiling",
            "floor",
            "retaining",
            "core_shaft",         # Lift/stair cores in mid-rise buildings
            "roof",
            "pavement"            # Exterior slabs
        ]
    },

    # -------------------------------------------------------------
    # HEAVY STRUCTURAL / INFRASTRUCTURE
    # -------------------------------------------------------------
    "C35/45": {
        "functional_types": [
            "structural"
        ],
        "application_areas": [
            "foundation",
            "footing",
            "slab",               # Heavily loaded slabs, parking decks
            "wall",
            "beam",
            "column",
            "core_shaft",         # Tall building cores
            "stair",
            "ramp",
            "balcony_terrace",
            "retaining",          # Larger retaining structures
            "pile",               # Common pile concrete strength
            "roof"
        ]
    },

    # -------------------------------------------------------------
    # HIGH-PERFORMANCE STRUCTURAL
    # -------------------------------------------------------------
    "C40/50": {
        "functional_types": [
            "structural"
        ],
        "application_areas": [
            "foundation",
            "footing",
            "slab",               # Long spans, heavy loads
            "wall",
            "beam",
            "column",
            "core_shaft",         # High-rise + seismic cores
            "stair",
            "ramp",
            "balcony_terrace",
            "retaining",          # Deep retaining walls & basements
            "pile",               # High-load pile concrete
            "roof"
        ]
    },

    # -------------------------------------------------------------
    # VERY HIGH-PERFORMANCE / INFRASTRUCTURE / HIGH-RISE
    # -------------------------------------------------------------
    "C50/60": {
        "functional_types": [
            "structural"
        ],
        "application_areas": [
            "foundation",
            "footing",
            "slab",               # Post-tensioned slabs, bridges
            "wall",
            "beam",
            "column",             # Very high axial loads
            "core_shaft",         # Tall building cores
            "stair",
            "ramp",
            "balcony_terrace",
            "retaining",          # Infrastructure-grade retaining
            "pile",               # Precast piles or deep bored piles
            "roof"
        ]
    }
}


if __name__ == "__main__":
    # Simple test print
    import json
    print(json.dumps(concrete_strength_classes, indent=2))
