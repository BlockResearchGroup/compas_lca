"""
Compute hallucination and omission rates for attribute extraction.

Hallucination:
  GT missing/empty, but TEST present/non-empty.

Omission:
  GT present/non-empty, but TEST missing/empty.

Rates are computed over ALL flattened fields (union of keys) for all matched UUID pairs.

Outputs:
  Hallucination rate: X.XXXXXX (A / B)
  Omission rate:      Y.YYYYYY (C / D)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from _eval_paths import parse_eval_args


# -------------------------
# CONFIG (data is not committed; see thesis/evaluation/README.md)
# -------------------------
args = parse_eval_args("A", needs_out=True)
gt_root = Path(args.gt)
test_root = Path(args.test)

output_dir = Path(args.out) if args.out else test_root
output_dir.mkdir(parents=True, exist_ok=True)
output_txt = output_dir / "hallucination_omission_summary.txt"

EXCLUDED_ATTRIBUTES = {
    "core_id",
    "thickness_source",
}
EXCLUDED_SUFFIXES = ("_type",)


# -------------------------
# HELPERS
# -------------------------
def load_json(file_path: Path) -> Optional[dict]:
    """Load JSON with a few fallback encodings."""
    for encoding in ["utf-8", "utf-8-sig", "latin-1"]:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return json.load(f)
        except UnicodeDecodeError:
            continue
        except (json.JSONDecodeError, FileNotFoundError):
            return None
    return None

class Tee:
    def __init__(self, *files):
        self.files = files

    def write(self, data):
        for f in self.files:
            f.write(data)
            f.flush()

    def flush(self):
        for f in self.files:
            f.flush()



def flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict[str, Any]:
    """Recursively flatten a nested dictionary into dot-notation keys."""
    items: dict[str, Any] = {}
    for k, v in d.items():
        if not isinstance(k, str):
            continue
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep))
        else:
            items[new_key] = v
    return items


def is_excluded(attr_key: str) -> bool:
    """Check if an attribute should be excluded from comparison."""
    attr_name = attr_key.split(".")[-1]
    if attr_name in EXCLUDED_ATTRIBUTES:
        return True
    if attr_name.endswith(EXCLUDED_SUFFIXES):
        return True
    return False


def is_missing_or_empty(value: Any) -> bool:
    """
    Define what counts as 'not populated'.

    Missing/empty if:
      - None
      - "" or whitespace-only string
      - empty list/tuple/set
      - empty dict
    """
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def build_uuid_map(root: Path) -> dict[str, Path]:
    """Map UUID (filename stem) -> relative path under root for all JSON files."""
    out: dict[str, Path] = {}
    for p in root.rglob("*.json"):
        out[p.stem] = p.relative_to(root)
    return out


def compute_hallucination_and_omission_rates(
    gt_root: Path,
    test_root: Path,
) -> tuple[float, float, dict[str, int]]:
    """
    Returns:
      hallucination_rate, omission_rate, diagnostics_counts
    """
    if not gt_root.exists():
        raise FileNotFoundError(f"gt_root does not exist: {gt_root}")
    if not test_root.exists():
        raise FileNotFoundError(f"test_root does not exist: {test_root}")

    gt_uuid_to_path = build_uuid_map(gt_root)
    test_uuid_to_path = build_uuid_map(test_root)

    matched_uuids = sorted(set(gt_uuid_to_path) & set(test_uuid_to_path))
    if not matched_uuids:
        return 0.0, 0.0, {
            "matched_uuids": 0,
            "files_used": 0,
            "files_skipped": 0,
            "hallucinated_total": 0,
            "gt_missing_total": 0,
            "omitted_total": 0,
            "gt_present_total": 0,
        }

    gt_missing_total = 0
    hallucinated_total = 0

    gt_present_total = 0
    omitted_total = 0

    files_used = 0
    files_skipped = 0

    for uuid in matched_uuids:
        gt_file = gt_root / gt_uuid_to_path[uuid]
        test_file = test_root / test_uuid_to_path[uuid]

        gt_data = load_json(gt_file)
        test_data = load_json(test_file)

        if not isinstance(gt_data, dict) or not isinstance(test_data, dict):
            files_skipped += 1
            continue

        files_used += 1

        gt_flat = flatten_dict(gt_data)
        test_flat = flatten_dict(test_data)
        all_keys = set(gt_flat.keys()) | set(test_flat.keys())

        for key in all_keys:
            if is_excluded(key):
                continue

            gt_val = gt_flat.get(key, None)
            test_val = test_flat.get(key, None)

            gt_missing = is_missing_or_empty(gt_val)
            test_missing = is_missing_or_empty(test_val)

            if gt_missing:
                gt_missing_total += 1
                if not test_missing:
                    hallucinated_total += 1
            else:
                gt_present_total += 1
                if test_missing:
                    omitted_total += 1

    hallucination_rate = hallucinated_total / gt_missing_total if gt_missing_total else 0.0
    omission_rate = omitted_total / gt_present_total if gt_present_total else 0.0

    diagnostics = {
        "matched_uuids": len(matched_uuids),
        "files_used": files_used,
        "files_skipped": files_skipped,
        "hallucinated_total": hallucinated_total,
        "gt_missing_total": gt_missing_total,
        "omitted_total": omitted_total,
        "gt_present_total": gt_present_total,
    }

    return hallucination_rate, omission_rate, diagnostics


# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    output_dir.mkdir(parents=True, exist_ok=True)

    halluc_rate, omission_rate, diag = compute_hallucination_and_omission_rates(
        gt_root, test_root
    )

    with open(output_txt, "w", encoding="utf-8") as f:
        import sys
        original_stdout = sys.stdout
        sys.stdout = Tee(sys.stdout, f)
        try:
            print("=== Hallucination & Omission Rates ===\n")

            print(f"Ground truth root: {gt_root}")
            print(f"Test root:         {test_root}\n")

            print(f"Matched UUIDs: {diag['matched_uuids']}")
            print(f"Files used:    {diag['files_used']} (skipped {diag['files_skipped']})\n")

            print(
                f"Hallucination rate: {halluc_rate * 100:.2f}% "
                f"({diag['hallucinated_total']} / {diag['gt_missing_total']})"
            )
            print(
                f"Omission rate:      {omission_rate * 100:.2f}% "
                f"({diag['omitted_total']} / {diag['gt_present_total']})"
            )

            print(f"\nResults written to: {output_txt}")

        finally:
            sys.stdout = original_stdout
