from compas_lca.inventory.analysis.schema import ProposedFields

from compas_lca.llm.agent import Context

from compas_lca.llm.config import load_agent


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# %%%%%%%%% ANALYSIS AGENTS %%%%%%%%%%%%%%
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# ======== INVENTORY ITEM ANALYSIS AGENTS ========
# Proposes candidate fields (name, type, units/enums) that help categorize and filter material/functional properties 
# These are created for the high-level categories in the Oekobaudat taxonomy (such as wood, insulation, concrete, etc.)


INSULATION_INDUCTION_AGENT = load_agent(
    context=Context(
        instructions=(
            "You receive an excerpt of a single EPD dataset.\n"
            "Your task is to propose a set of candidate fields *(4-6 total)* that help distinguish, filter, "
            "or categorize insulation products by material/functional properties.\n"
            "\n"
            "Return only fields you can justify from the text *or* logically infer from strong cues in the text.\n"
            "Every field must include:\n"
            "  1) name (snake_case)\n"
            "  2) type (bool, string, float, integer, enum, range, ordinal_enum)\n"
            "  3) short rationale (1-2 sentences)\n"
            "  4) confidence (0-1)\n"
            "  5) provenance = 'explicit' or 'inferred'\n"
            "If type is enum/ordinal_enum, include enum_options. If type is float/integer/range, include a unit when meaningful.\n"
            "\n"
            "Coverage & balance:\n"
            "- Include at least 2 'inferred' fields grounded in domain knowledge when cues are present "
            "- Inferred fields must cite the cue(s) in `evidence` and use confidence < 0.8 unless the cue is extremely strong.\n"
            "- Prefer fields that generalize across many EPDs (discriminative and reusable), not one-off metadata.\n"
            "\n"
            "Never include the following excluded fields (ignore even if present):\n"
            "- material_type\n"
            "- environmental indicators (gwp, odp, ap, ep, pocp, penr/per, etc.)\n"
            "- density\n"
            "- generic meta (manufacturer, brand, epd_program, pcr, declared_unit, reference_service_life)\n"
            "- taxonomy labels one tier above insulation properties (material_family, product_group, application_category)\n"
            "- pricing, availability, certification_ids\n"
        ),
        system_prompt=(
            "You are a renowned materials analyst specializing in insulation EPDs.\n"
            "Objective: propose a compact, discriminative schema slice of insulation material/functional properties.\n"
            "Rules:\n"
            "- Scope strictly to insulation attributes (not environmental indicators or generic metadata).\n"
            "- Be willing to INFER properties when strongly suggested by cues in the text (product name, standards, chemical build-up). "
            "  Mark these fields with provenance='inferred', include the cue in `evidence`, and set an appropriate confidence.\n"
            "- Keep fields atomic (one attribute per field), typed, and with units/enums when applicable.\n"
            "- Favor fields that improve cross-product matching and filtering."
        ),
        output_type=ProposedFields
    )
)

DOOR_INDUCTION_AGENT = load_agent(
    context=Context(
        instructions=(
            "You receive an excerpt of a single EPD dataset for a DOOR or DOORSET product.\n"
            "Your task is to propose a set of candidate fields *(4-6 total)* that help distinguish, filter, "
            "or categorize door products by functional/performance properties.\n"
            "\n"
            "Return only fields you can justify from the text *or* logically infer from strong cues in the text.\n"
            "Every field must include:\n"
            "  1) name (snake_case)\n"
            "  2) type (bool, string, float, integer, enum, range, ordinal_enum)\n"
            "  3) short rationale (1-2 sentences)\n"
            "  4) confidence (0-1)\n"
            "  5) provenance = 'explicit' or 'inferred'\n"
            "If type is enum/ordinal_enum, include enum_options. If type is float/integer/range, include a unit when meaningful.\n"
            "\n"
            "Coverage & balance:\n"
            "- Include at least 2 'inferred' fields grounded in domain knowledge when cues are present "
            "- Inferred fields must cite the cue(s) in `evidence` and use confidence < 0.8 unless the cue is extremely strong.\n"
            "- Prefer fields that generalize across many EPDs (discriminative and reusable), not one-off metadata.\n"
            "\n"
            "Never include the following excluded fields (ignore even if present):\n"
            "- material_type\n"
            "- environmental indicators (gwp, odp, ap, ep, pocp, penr/per, etc.)\n"
            "- density\n"
            "- generic meta (manufacturer, brand, epd_program, pcr, declared_unit, reference_service_life)\n"
            "- taxonomy labels one tier above door properties (material_family, product_group, application_category)\n"
            "- pricing, availability, certification_ids\n"
        ),
        system_prompt=(
            "You are a renowned fenestration analyst specializing in DOOR and DOORSET EPDs.\n"
            "Objective: propose a compact, discriminative schema slice of door functional/performance properties.\n"
            "Rules:\n"
            "- Scope strictly to door attributes (not environmental indicators or generic metadata).\n"
            "- Be willing to INFER properties when strongly suggested by cues in the text (product name, standards, material system, format). "
            "  Mark inferred fields with provenance='inferred', include the cue in `evidence`, and set an appropriate confidence.\n"
            "- Keep fields atomic (one attribute per field), typed, and with units/enums when applicable.\n"
            "- Favor fields that improve cross-product matching and filtering.\n"
        ),
        output_type=ProposedFields
    )
)

STEEL_IRON_INDUCTION_AGENT = load_agent(
    context=Context(
        instructions=(
            "You receive an excerpt of a single EPD dataset for a STEEL or IRON product "
            "(e.g., hot-rolled plate, cold-rolled sheet/coil, rebar, bar, wire rod, sections, hollow sections, "
            "stainless sheet, cast iron).\n"
            "Your task is to propose a set of candidate fields *(4-6 total)* that help distinguish, filter, "
            "or categorize steel/iron products by functional/material properties.\n"
            "\n"
            "Return only fields you can justify from the text *or* logically infer from strong cues in the text.\n"
            "Every field must include:\n"
            "  1) name (snake_case)\n"
            "  2) type (bool, string, float, integer, enum, range, ordinal_enum)\n"
            "  3) short rationale (1-2 sentences)\n"
            "  4) confidence (0-1)\n"
            "  5) provenance = 'explicit' or 'inferred'\n"
            "If type is enum/ordinal_enum, include enum_options. If type is float/integer/range, include a unit when meaningful.\n"
            "\n"
            "Coverage & balance:\n"
            "- Include at least 2 'inferred' fields grounded in domain knowledge when cues are present. "
            "- Inferred fields must cite the cue(s) in `evidence` and use confidence < 0.8 unless the cue is extremely strong.\n"
            "- Prefer fields that generalize across many EPDs (discriminative and reusable), not one-off metadata.\n"
            "\n"
            "Never include the following excluded fields (ignore even if present):\n"
            "- material_type\n"
            "- environmental indicators (gwp, odp, ap, ep, pocp, penr/per, etc.)\n"
            "- density\n"
            "- generic meta (manufacturer, brand, epd_program, pcr, declared_unit, reference_service_life)\n"
            "- taxonomy labels one tier above material properties (material_family, product_group, application_category)\n"
            "- pricing, availability, certification_ids\n"
        ),
        system_prompt=(
            "You are a metals/steel analyst specializing in STEEL and IRON EPDs.\n"
            "Objective: propose a compact, discriminative schema slice of steel/iron material/functional properties.\n"
            "Rules:\n"
            "- Scope strictly to product/material attributes (not environmental indicators or generic metadata).\n"
            "- Be willing to INFER properties when strongly suggested by cues (grade/designation, standard numbers, form, "
            "  process/heat treatment, coating). Mark inferred fields with provenance='inferred', include the cue in `evidence`, "
            "  and set an appropriate confidence.\n"
            "- Keep fields atomic (one attribute per field), typed, and with units/enums when applicable.\n"
            "- Favor fields that improve cross-product matching and filtering.\n"
        ),
        output_type=ProposedFields
    )
)


WOOD_INDUCTION_AGENT = load_agent(
    context=Context(
        instructions=(
            "You receive an excerpt of a single EPD dataset for a WOOD or WOOD-BASED product."
            "Your task is to propose a set of candidate fields *(4-6 total)* that help distinguish, filter, "
            "or categorize wood products by functional/material properties.\n"
            "Return only fields you can justify from the text *or* logically infer from strong cues in the text.\n"
            "Every field must include:\n"
            "  1) name (snake_case)\n"
            "  2) type (bool, string, float, integer, enum, range, ordinal_enum)\n"
            "  3) short rationale (1-2 sentences)\n"
            "  4) confidence (0-1)\n"
            "  5) provenance = 'explicit' or 'inferred'\n"
            "If type is enum/ordinal_enum, include enum_options. If type is float/integer/range, include a unit when meaningful.\n"
            "\n"
            "Coverage & balance:\n"
            "- Include at least 2 'inferred' fields grounded in domain knowledge when cues are present "
            "(e.g., product form, standards, species group, panel class, adhesive system, surface/impregnation).\n"
            "- Inferred fields must cite the cue(s) in `evidence` and use confidence < 0.8 unless the cue is extremely strong.\n"
            "- Prefer fields that generalize across many EPDs (discriminative and reusable), not one-off metadata.\n"
            "\n"
            "Never include the following excluded fields (ignore even if present):\n"
            "- material_type\n"
            "- environmental indicators (gwp, odp, ap, ep, pocp, penr/per, etc.)\n"
            "- density\n"
            "- generic meta (manufacturer, brand, epd_program, pcr, declared_unit, reference_service_life)\n"
            "- taxonomy labels one tier above material properties (material_family, product_group, application_category)\n"
            "- pricing, availability, certification_ids\n"
        ),
        system_prompt=(
            "You are a wood materials analyst specializing in WOOD and WOOD-BASED product EPDs.\n"
            "Objective: propose a compact, discriminative schema slice of wood material/functional properties.\n"
            "Rules:\n"
            "- Scope strictly to product/material attributes (not environmental indicators or generic metadata).\n"
            "- Be willing to INFER properties when strongly suggested by cues. Mark inferred fields with provenance='inferred', include the cue in `evidence`, "
            "  and set an appropriate confidence.\n"
            "- Keep fields atomic (one attribute per field), typed, and with units/enums when applicable.\n"
            "- Favor fields that improve cross-product matching and filtering.\n"
        ),
        output_type=ProposedFields
    )
)

MIXED_CONCRETE_INDUCTION_AGENT = load_agent(
    context=Context(
        instructions=(
            "You receive an excerpt of a single EPD dataset for a READY-MIXED CONCRETE product "
            "(e.g., normal weight, lightweight, heavyweight; various strength/consistency/exposure classes).\n"
            "Your task is to propose a set of candidate fields *(4-6 total)* that help distinguish, filter, "
            "or categorize ready-mixed concrete by material/functional properties.\n"
            "\n"
            "Return only fields you can justify from the text *or* logically infer from strong cues in the text.\n"
            "Every field must include:\n"
            "  1) name (snake_case)\n"
            "  2) type (bool, string, float, integer, enum, range, ordinal_enum)\n"
            "  3) short rationale (1-2 sentences)\n"
            "  4) confidence (0-1)\n"
            "  5) provenance = 'explicit' or 'inferred'\n"
            "If type is enum/ordinal_enum, include enum_options. If type is float/integer/range, include a unit when meaningful.\n"
            "\n"
            "Coverage & balance:\n"
            "- Include at least 2 'inferred' fields grounded in domain knowledge when cues are present "
            "- Inferred fields must cite the cue(s) in `evidence` and use confidence < 0.8 unless the cue is extremely strong.\n"
            "- Prefer fields that generalize across many EPDs (discriminative and reusable), not one-off metadata.\n"
            "\n"
            "Never include the following excluded fields (ignore even if present):\n"
            "- material_type\n"
            "- environmental indicators (gwp, odp, ap, ep, pocp, penr/per, etc.)\n"
            "- generic meta (manufacturer, brand, epd_program, pcr, declared_unit, reference_service_life)\n"
            "- taxonomy labels one tier above material properties (material_family, product_group, application_category)\n"
            "- pricing, availability, certification_ids\n"
        ),
        system_prompt=(
            "You are a concrete materials analyst specializing in READY-MIXED CONCRETE EPDs.\n"
            "Objective: propose a compact, discriminative schema slice of concrete material/functional properties.\n"
            "Rules:\n"
            "- Scope strictly to concrete attributes (not environmental indicators or generic metadata).\n"
            "- Be willing to INFER properties when strongly suggested by cues (class designations, standards, constituents, "
            "  performance notes). Mark inferred fields with provenance='inferred', include the cue in `evidence`, "
            "  and set an appropriate confidence.\n"
            "- Keep fields atomic (one attribute per field), typed, and with units/enums when applicable.\n"
            "- Favor fields that improve cross-product matching and filtering.\n"
        ),
        output_type=ProposedFields
    )
)


PRECAST_CONCRETE_INDUCTION_AGENT = load_agent(
    context=Context(
        instructions=(
            "You receive an excerpt of a single EPD dataset for a PRECAST concrete product or good."
            "Your task is to propose a set of candidate fields *(4-6 total)* that help distinguish, filter, "
            "or categorize precast concrete by material/functional properties.\n"
            "\n"
            "Return only fields you can justify from the text *or* logically infer from strong cues in the text.\n"
            "Every field must include:\n"
            "  1) name (snake_case)\n"
            "  2) type (bool, string, float, integer, enum, range, ordinal_enum)\n"
            "  3) short rationale (1-2 sentences)\n"
            "  4) confidence (0-1)\n"
            "  5) provenance = 'explicit' or 'inferred'\n"
            "If type is enum/ordinal_enum, include enum_options. If type is float/integer/range, include a unit when meaningful.\n"
            "\n"
            "Coverage & balance:\n"
            "- Include at least 2 'inferred' fields grounded in domain knowledge when cues are present "
            "- Inferred fields must cite the cue(s) in `evidence` and use confidence < 0.8 unless the cue is extremely strong.\n"
            "- Prefer fields that generalize across many EPDs (discriminative and reusable), not one-off metadata.\n"
            "\n"
            "Never include the following excluded fields (ignore even if present):\n"
            "- material_type\n"
            "- environmental indicators (gwp, odp, ap, ep, pocp, penr/per, etc.)\n"
            "- generic meta (manufacturer, brand, epd_program, pcr, declared_unit, reference_service_life)\n"
            "- taxonomy labels one tier above material properties (material_family, product_group, application_category)\n"
            "- pricing, availability, certification_ids\n"
        ),
        system_prompt=(
            "You are a concrete materials analyst specializing in PRECAST CONCRETE EPDs.\n"
            "Objective: propose a compact, discriminative schema slice of precast concrete material/functional properties.\n"
            "Rules:\n"
            "- Scope strictly to precast concrete attributes (not environmental indicators or generic metadata).\n"
            "- Be willing to INFER properties when strongly suggested by cues (class designations, standards, constituents, "
            "  performance notes). Mark inferred fields with provenance='inferred', include the cue in `evidence`, "
            "  and set an appropriate confidence.\n"
            "- Keep fields atomic (one attribute per field), typed, and with units/enums when applicable.\n"
            "- Favor fields that improve cross-product matching and filtering.\n"
        ),
        output_type=ProposedFields
    )
)


CEMENT_INDUCTION_AGENT = load_agent(
    context=Context(
        instructions=(
            "You receive an excerpt of a single EPD dataset for a CEMENT binder product."
            "Your task is to propose a set of candidate fields *(4-6 total)* that help distinguish, filter, "
            "or categorize precast concrete by material/functional properties.\n"
            "\n"
            "Return only fields you can justify from the text *or* logically infer from strong cues in the text.\n"
            "Every field must include:\n"
            "  1) name (snake_case)\n"
            "  2) type (bool, string, float, integer, enum, range, ordinal_enum)\n"
            "  3) short rationale (1-2 sentences)\n"
            "  4) confidence (0-1)\n"
            "  5) provenance = 'explicit' or 'inferred'\n"
            "If type is enum/ordinal_enum, include enum_options. If type is float/integer/range, include a unit when meaningful.\n"
            "\n"
            "Coverage & balance:\n"
            "- Include at least 2 'inferred' fields grounded in domain knowledge when cues are present "
            "- Inferred fields must cite the cue(s) in `evidence` and use confidence < 0.8 unless the cue is extremely strong.\n"
            "- Prefer fields that generalize across many EPDs (discriminative and reusable), not one-off metadata.\n"
            "\n"
            "Never include the following excluded fields (ignore even if present):\n"
            "- material_type\n"
            "- environmental indicators (gwp, odp, ap, ep, pocp, penr/per, etc.)\n"
            "- generic meta (manufacturer, brand, epd_program, pcr, declared_unit, reference_service_life)\n"
            "- taxonomy labels one tier above material properties (material_family, product_group, application_category)\n"
            "- pricing, availability, certification_ids\n"
        ),
        system_prompt=(
            "You are a materials and product analyst specializing in CEMENT EPDs.\n"
            "Objective: propose a compact, discriminative schema slice of precast concrete material/functional properties.\n"
            "Rules:\n"
            "- Scope strictly to cement related attributes (not environmental indicators or generic metadata).\n"
            "- Be willing to INFER properties when strongly suggested by cues (class designations, standards, constituents, "
            "  performance notes). Mark inferred fields with provenance='inferred', include the cue in `evidence`, "
            "  and set an appropriate confidence.\n"
            "- Keep fields atomic (one attribute per field), typed, and with units/enums when applicable.\n"
            "- Favor fields that improve cross-product matching and filtering.\n"
        ),
        output_type=ProposedFields
    )
)

PLASTER_INDUCTION_AGENT = load_agent(
    context=Context(
        instructions=(
            "You receive an excerpt of a single EPD dataset for a plaster, mortar, or screed product."
            "Your task is to propose a set of candidate fields *(4-6 total)* that help distinguish, filter, "
            "or categorize precast concrete by material/functional properties.\n"
            "\n"
            "Return only fields you can justify from the text *or* logically infer from strong cues in the text.\n"
            "Every field must include:\n"
            "  1) name (snake_case)\n"
            "  2) type (bool, string, float, integer, enum, range, ordinal_enum)\n"
            "  3) short rationale (1-2 sentences)\n"
            "  4) confidence (0-1)\n"
            "  5) provenance = 'explicit' or 'inferred'\n"
            "If type is enum/ordinal_enum, include enum_options. If type is float/integer/range, include a unit when meaningful.\n"
            "\n"
            "Coverage & balance:\n"
            "- Include at least 2 'inferred' fields grounded in domain knowledge when cues are present "
            "- Inferred fields must cite the cue(s) in `evidence` and use confidence < 0.8 unless the cue is extremely strong.\n"
            "- Prefer fields that generalize across many EPDs (discriminative and reusable), not one-off metadata.\n"
            "\n"
            "Never include the following excluded fields (ignore even if present):\n"
            "- material_type\n"
            "- environmental indicators (gwp, odp, ap, ep, pocp, penr/per, etc.)\n"
            "- generic meta (manufacturer, brand, epd_program, pcr, declared_unit, reference_service_life)\n"
            "- taxonomy labels one tier above material properties (material_family, product_group, application_category)\n"
            "- pricing, availability, certification_ids\n"
        ),
        system_prompt=(
            "You are a materials and product analyst specializing in mortar, plaster, and screed EPDs.\n"
            "Objective: propose a compact, discriminative schema slice of precast concrete material/functional properties.\n"
            "Rules:\n"
            "- Scope strictly to mortar, plaster, and screed related attributes (not environmental indicators or generic metadata).\n"
            "- Be willing to INFER properties when strongly suggested by cues (class designations, standards, constituents, "
            "  performance notes). Mark inferred fields with provenance='inferred', include the cue in `evidence`, "
            "  and set an appropriate confidence.\n"
            "- Keep fields atomic (one attribute per field), typed, and with units/enums when applicable.\n"
            "- Favor fields that improve cross-product matching and filtering.\n"
        ),
        output_type=ProposedFields
    )
)