"""Shared path/argument helper for the Chapter 5 evaluation scripts.

The evaluation datasets, per-model extraction outputs and expert ground truth
are NOT committed to this repository. They ship as a separate downloadable data
package (see thesis/evaluation/README.md for the link / access instructions).

To run any evaluation script you must either:

  1. Download and extract the data package, then point the scripts at it via the
     ``LCA_EVAL_DATA`` environment variable, e.g.::

         export LCA_EVAL_DATA=/path/to/extracted/data      # bash
         $env:LCA_EVAL_DATA = "D:/path/to/extracted/data"  # PowerShell

     The default ground-truth locations (``DATASET_A_GT`` / ``DATASET_B_GT``)
     are then resolved relative to that root.

  2. Or pass explicit paths on the command line: ``--gt``, ``--test`` and
     (where applicable) ``--out``. Explicit flags always win over the defaults.

Dataset A = building-element samples (``*_buildingelement_*`` scripts +
``compare_labels.py``).
Dataset B = ÖKOBAUDAT EPD / inventory-item samples (``*_inventoryitem_*``
scripts + ``compare_classification.py`` + ``compare_labels_original.py``).
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

# Root of the (downloaded, gitignored) data package. Override with LCA_EVAL_DATA.
DATA_ROOT = Path(os.environ.get("LCA_EVAL_DATA", "data"))

# Convenience default ground-truth locations inside the data package.
DATASET_A_GT = DATA_ROOT / "dataset_a_buildingelement" / "ground_truth"
DATASET_B_GT = DATA_ROOT / "dataset_b_inventoryitem" / "ground_truth"


def parse_eval_args(dataset: str, needs_out: bool = True) -> argparse.Namespace:
    """Build and parse the standard evaluation CLI.

    Parameters
    ----------
    dataset : str
        Either ``"A"`` (building elements) or ``"B"`` (inventory items). Selects
        the default ``--gt`` location.
    needs_out : bool
        If True, add an optional ``--out`` flag for the output directory. When
        ``--out`` is omitted the scripts write results next to ``--test``.

    Returns
    -------
    argparse.Namespace
        Parsed arguments with ``.gt``, ``.test`` and (if ``needs_out``) ``.out``.
    """
    dataset = dataset.upper()
    if dataset not in {"A", "B"}:
        raise ValueError(f"dataset must be 'A' or 'B', got {dataset!r}")

    default_gt = DATASET_A_GT if dataset == "A" else DATASET_B_GT

    parser = argparse.ArgumentParser(
        description=(
            "Evaluate one model's extraction output against expert ground truth. "
            "Data is NOT committed to the repo; download the data package and set "
            "LCA_EVAL_DATA, or pass --gt/--test/--out explicitly (see "
            "thesis/evaluation/README.md)."
        )
    )
    parser.add_argument(
        "--gt",
        default=str(default_gt),
        help=f"Ground-truth root directory (default: {default_gt}).",
    )
    parser.add_argument(
        "--test",
        required=True,
        help="Model-output root directory to evaluate (from the data package).",
    )
    if needs_out:
        parser.add_argument(
            "--out",
            default=None,
            help="Output directory for metric files (default: alongside --test).",
        )
    return parser.parse_args()
