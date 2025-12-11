"""
One-shot classifier that calls Claude directly (no pydantic-ai pipeline).

Focus: type-only classification
- entry_type: material | component | unknown
- material_type or component_type (one of the enum values)
- optional level3_value (normalized when possible)

Example:
    python scripts/one_shot_classify.py --file temp/example.txt \\
        --model claude-3.5-sonnet --output temp/example_out.json

    echo "EPS insulation board for façade" | python scripts/one_shot_classify.py \\
        --file - --model claude-3.5-sonnet
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict, Optional

from compas_lca.enums import ComponentType, MaterialType
from compas_lca.llm.claude_client import ClaudeClient
from compas_lca.llm.prompts.one_shot_types import type_prompt
from compas_lca.matching_core.normalization import normalize_level3_value


def _coerce_choice(value: Any, allowed: set[str], *, default: str = "unknown") -> str:
    if value is None:
        return default
    if hasattr(value, "value"):
        value = value.value
    if not isinstance(value, str):
        return default
    v = value.strip().lower().replace(" ", "_")
    return v if v in allowed else default


def _load_text(args: argparse.Namespace) -> str:
    if args.text:
        return args.text
    if args.file:
        if args.file == "-":
            return sys.stdin.read()
        return Path(args.file).read_text(encoding="utf-8")
    raise SystemExit("Provide --file <path> or --text \"...\"")


def _build_prompt(payload: str) -> str:
    return f"{type_prompt()}\n\nInput data:\n{payload}\n\nRespond with JSON only."


def _postprocess(result: Dict[str, Any]) -> Dict[str, Any]:
    entry_type = _coerce_choice(result.get("entry_type"), {"material", "component", "unknown"})
    material_type = _coerce_choice(result.get("material_type"), {m.value for m in MaterialType})
    component_type = _coerce_choice(result.get("component_type"), {c.value for c in ComponentType})
    raw_level3 = result.get("level3_value") or "unknown"

    if entry_type == "material":
        component_type = None
    elif entry_type == "component":
        material_type = None
    else:
        material_type = "unknown"
        component_type = "unknown"

    if entry_type == "material":
        normalized_level3: Optional[str] = normalize_level3_value(material_type, raw_level3) or "unknown"
    else:
        normalized_level3 = normalize_level3_value(component_type, raw_level3) or "unknown"

    return {
        "entry_type": entry_type,
        "material_type": material_type,
        "component_type": component_type,
        "level3_value_raw": raw_level3,
        "level3_value_normalized": normalized_level3,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="One-shot Claude classifier for type-only outputs.")
    parser.add_argument("--file", help="Path to input text/JSON file. Use - for stdin.", default=None)
    parser.add_argument("--text", help="Raw text payload. Ignored if --file is set.", default=None)
    parser.add_argument("--model", default="claude-haiku-4-5", help="Claude model name.")
    parser.add_argument("--temperature", type=float, default=0.0, help="Sampling temperature.")
    parser.add_argument("--max-tokens", type=int, default=512, help="Max tokens to generate.")
    parser.add_argument("--output", help="Optional output path to write JSON result.", default=None)

    args = parser.parse_args()
    payload = _load_text(args)
    prompt = _build_prompt(payload)

    client = ClaudeClient(
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )
    raw = client.complete(prompt)

    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("LLM output is not a JSON object.")
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"Failed to parse LLM JSON: {exc}\nRaw output:\n{raw}") from exc

    final = _postprocess(parsed)
    out_text = json.dumps(final, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(out_text, encoding="utf-8")
    print(out_text)


if __name__ == "__main__":
    main()

