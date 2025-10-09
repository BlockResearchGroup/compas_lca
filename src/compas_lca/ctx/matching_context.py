from compas_lca.llm.context import Context

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

# ======== MATCHING AGENT ========
# Double-checks semantic and functional matches for a material/component
# after filtering the solution space within the inventory
# note: here we have to figure out what to do if the solution space is huge

MATCHING_CTX = Context(
    instructions=(
        "placeholder"
    ),
    output_type=None
)
