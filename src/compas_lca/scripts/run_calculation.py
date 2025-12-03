from pathlib import Path

from compas_lca.model.lca_element import LcaElement

from compas_lca.workflows.calculation import FileInventoryRepository
from compas_lca.workflows.calculation import LcaElementCalculator

# ========== USER INPUT ==========

# Path to inventory directory
inventory_dir = Path("/path/to/inventory_dir")

# Path to LcaElement JSON file
element_json_path = Path("temp/ifc_extracted_matched/1072_HiLo_Model-Architecture/single_materials/0b727db5-38e3-4331-8fbc-e42eb063ef4f.json")

# LCA parameters
indicator_name = "GWPtotal"
include_stages = ["A1-A3", "C3"] # None = all stages
include_stage_D = False
scenario_agg = "mean"

# ================================

# 1) Load an LcaElement (e.g. from JSON)
element = LcaElement.model_validate_json(open("some_element.json").read())

# 2) Create repository + calculator
repo = FileInventoryRepository("/path/to/inventory_dir")
calc = LcaElementCalculator(repo)

# 3) Compute stats for GWPtotal, stages A1-A3 + C3, exclude D, mean across scenarios
stats = calc.element_indicator_stats(
    element,
    indicator_name="GWPtotal",
    include_stages=["A1-A3", "C3"],
    include_stage_D=False,
    scenario_agg="mean",
)

print("min:", stats.min)
print("max:", stats.max)
print("median:", stats.median)
print("sum:", stats.sum)

# 4) Optional: range for multi-layer element
rng = calc.element_indicator_total_range(
    element,
    indicator_name="GWPtotal",
    include_stages=["A1-A3", "C3", "C4"],
    include_stage_D=False,
)

print("min_total:", rng.min_total)
print("max_total:", rng.max_total)
