"""Orchestrate the Chapter 5 (Section 5.6) multi-LLM extraction benchmark.

For each dataset (A = building elements, B = inventory items / EPDs) this runs
the three metric scripts (classification, labels, hallucinations) for every
canonical model, writing each model's metric files under
``outputs/<dataset>/<model>/``.

The datasets and per-model extraction outputs are NOT committed to this repo;
they ship in a separate data package (see thesis/evaluation/README.md). Point
this script at the extracted package with ``--data-root`` or the ``LCA_EVAL_DATA``
environment variable.

Expected data-package layout (per dataset)::

    <data-root>/dataset_a_buildingelement/ground_truth/...
    <data-root>/dataset_a_buildingelement/outputs/<model_dir>/...   # model output
    <data-root>/dataset_b_inventoryitem/ground_truth/...
    <data-root>/dataset_b_inventoryitem/outputs/<model_dir>/...

This file is documentation-as-code: it records exactly which models and scripts
produced the published figures. No LLM/API calls are made here.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent

# The 7 canonical models (3 capability tiers) evaluated in the benchmark.
MODELS = [
    # flagship tier
    "claude-opus-4-5",
    "gemini-3-pro-preview",
    "gpt-5.2",
    # mid tier
    "claude-sonnet-4-5",
    "gemini-3-flash-preview",
    # small tier
    "claude-haiku-4-5",
    "gpt-5-mini",
]


def model_dir(model: str) -> str:
    """Filesystem-safe subdirectory name for a model (dots/hyphens -> underscores).

    The per-model output directories inside the data package follow this
    convention, e.g. ``claude-opus-4-5`` -> ``claude_opus_4_5``.
    """
    return model.replace("-", "_").replace(".", "_")


# dataset key -> (package subdir, script filename prefix)
DATASETS = {
    "A": ("dataset_a_buildingelement", "evaluation_buildingelement"),
    "B": ("dataset_b_inventoryitem", "evaluation_inventoryitem"),
}

# metric -> script suffix
METRICS = ["classification", "labels", "hallucinations"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-root",
        default=os.environ.get("LCA_EVAL_DATA", "data"),
        help="Root of the extracted data package (default: $LCA_EVAL_DATA or 'data').",
    )
    parser.add_argument(
        "--out-root",
        default=str(SCRIPTS_DIR.parent / "outputs"),
        help="Where to write per-model metric files (default: thesis/evaluation/outputs).",
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        choices=sorted(DATASETS),
        default=sorted(DATASETS),
        help="Which datasets to run (default: both).",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=MODELS,
        help="Which models to run (default: all 7 canonical models).",
    )
    args = parser.parse_args()

    data_root = Path(args.data_root)
    out_root = Path(args.out_root)

    failures = 0
    for ds in args.datasets:
        pkg_subdir, script_prefix = DATASETS[ds]
        gt = data_root / pkg_subdir / "ground_truth"
        for model in args.models:
            # Model-output dirs come from the data package (not the repo).
            test = data_root / pkg_subdir / "outputs" / model_dir(model)
            for metric in METRICS:
                script = SCRIPTS_DIR / f"{script_prefix}_{metric}.py"
                out = out_root / ds / model_dir(model) / metric
                cmd = [
                    sys.executable,
                    str(script),
                    "--gt", str(gt),
                    "--test", str(test),
                    "--out", str(out),
                ]
                print(f"\n>>> dataset {ds} | {model} | {metric}")
                print("    " + " ".join(cmd))
                result = subprocess.run(cmd)
                if result.returncode != 0:
                    failures += 1
                    print(f"    FAILED (exit {result.returncode})")

    if failures:
        print(f"\n{failures} run(s) failed.")
        return 1
    print("\nAll runs completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
