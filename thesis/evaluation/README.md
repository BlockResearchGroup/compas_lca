# Chapter 5 §5.6 — Multi-LLM Extraction Benchmark

This directory reproduces the multi-LLM extraction benchmark reported in
Chapter 5, Section 5.6 of the thesis (Figures 5.9–5.15). Each script reads
**pre-extracted** JSON (expert ground truth + one model's output) and computes
accuracy metrics. **No LLM or API calls are made** — extraction was run
offline; these scripts only score the results.

## Models (7 models, 3 tiers)

| Tier      | Models                                             |
|-----------|----------------------------------------------------|
| Flagship  | `claude-opus-4-5`, `gemini-3-pro-preview`, `gpt-5.2` |
| Mid       | `claude-sonnet-4-5`, `gemini-3-flash-preview`      |
| Small     | `claude-haiku-4-5`, `gpt-5-mini`                   |

## Datasets

- **Dataset A — building elements**: 205 samples, IFC-derived building elements,
  with expert ground truth. Scored by the `evaluation_buildingelement_*.py`
  scripts (and `compare_labels.py`).
- **Dataset B — inventory items**: 252 ÖKOBAUDAT EPD samples, with expert
  ground truth. Scored by the `evaluation_inventoryitem_*.py` scripts (and
  `compare_classification.py` / `compare_labels_original.py`).

## Metrics and scripts

| Metric                                | Script                                  |
|---------------------------------------|-----------------------------------------|
| Classification accuracy (L1/L2/L3)    | `*_classification.py`                   |
| Attribution / label accuracy          | `*_labels.py`                           |
| Hallucination + omission rate         | `*_hallucinations.py`                   |

`*` is `evaluation_buildingelement` for Dataset A and `evaluation_inventoryitem`
for Dataset B. The `compare_*.py` scripts are earlier standalone variants kept
for reference (Dataset B).

## Data availability

The datasets, per-model extraction outputs, and the figure-generation code are
**not** stored in this repository. They are distributed as a separate data
package:

```
Data package (request access from the author):
https://drive.google.com/file/d/1W_qiDYm2ctd-1DAUxMurRsfdXOdEKELE/view?usp=drive_link
```

Download and extract the package, then either set the environment variable:

```bash
export LCA_EVAL_DATA=/path/to/extracted/data      # bash / zsh
```
```powershell
$env:LCA_EVAL_DATA = "D:/path/to/extracted/data"  # PowerShell
```

or pass paths explicitly on each script via `--gt` / `--test` / `--out`.

Expected package layout:

```
<data-root>/
  dataset_a_buildingelement/ground_truth/...
  dataset_a_buildingelement/outputs/<model>/...
  dataset_b_inventoryitem/ground_truth/...
  dataset_b_inventoryitem/outputs/<model>/...
```

## Running

`compas_lca` must be importable (the scripts import
`compas_lca.matching_core.normalization`). If it is not installed, add the repo
`src/` to `PYTHONPATH`.

Score a single model on one metric:

```bash
PYTHONPATH=src python thesis/evaluation/scripts/evaluation_inventoryitem_classification.py \
    --gt   "$LCA_EVAL_DATA/dataset_b_inventoryitem/ground_truth" \
    --test "$LCA_EVAL_DATA/dataset_b_inventoryitem/outputs/claude_haiku_4_5" \
    --out  outputs/B/claude_haiku_4_5/classification
```

Run the whole benchmark (all models × both datasets × all three metrics):

```bash
PYTHONPATH=src LCA_EVAL_DATA=/path/to/extracted/data \
    python thesis/evaluation/scripts/run_all.py
```

Outputs land under `thesis/evaluation/outputs/<dataset>/<model>/<metric>/`.

## Reproducibility caveat

`normalize_level3_value` validates level-3 classification values against the
**current** `compas_lca` `enums.py`. A few enum values have drifted since the
paper run:

- `MineralType`: `earthenware` / `stoneware` / `porcelain` consolidated to `ceramic`
- `RailingType.other` removed
- `ConcreteStrength` added
- `RoofType.glass_roof` added

As a result, level-3 classification numbers for a few mineral/railing samples
may differ slightly from the published figures. This is expected: the benchmark
is **procedurally** reproducible, not bit-exactly reproducible.
