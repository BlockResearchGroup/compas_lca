"""
Batch one-shot classification for OBD samples.

Mimics the structure produced by the multi-stage pipeline so that
`scripts/compare_classification.py` can evaluate the results.

Output folder structure:
  <output_dir>/
    material/<material_type>/<uuid>.json
    component/<component_type>/<uuid>.json
    unknown/unknown/<uuid>.json

Each JSON only includes the minimal fields needed by the comparator:
item_core.facet.{material_type|component_type}_type for level-3.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from dotenv import load_dotenv

from compas_lca.llm.claude_client import ClaudeClient
from compas_lca.llm.prompts.one_shot_types import type_prompt
from compas_lca.matching_core.normalization import normalize_level3_value

load_dotenv()


def load_uuid_filter(path: Optional[Path]) -> Optional[set[str]]:
    if path is None:
        return None
    if not path.exists():
        print(f"Warning: filter file not found: {path}")
        return None
    uuids: set[str] = set()
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            uid = row.get("uuid") or row.get("UUID")
            if uid:
                uuids.add(uid)
    return uuids


def iter_csv_rows(csv_path: Path, encoding_preference: str) -> Iterable[Dict[str, str]]:
    """
    Yield rows from the semicolon-separated OBD CSV with a tolerant encoding strategy.
    Tries the preferred encoding first, then falls back to latin-1 to avoid decode errors.
    """
    encodings = [encoding_preference, "latin-1"] if encoding_preference != "latin-1" else ["latin-1"]
    last_error: Optional[Exception] = None
    for enc in encodings:
        try:
            with open(csv_path, newline="", encoding=enc) as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    yield row
            return
        except UnicodeDecodeError as exc:
            last_error = exc
            continue
    if last_error:
        raise last_error


def build_payload(row: Dict[str, str]) -> str:
    # Keep the row content as JSON for the prompt.
    return json.dumps(row, ensure_ascii=False, indent=2)


def classify_text(client: ClaudeClient, text: str) -> Dict[str, Any]:
    prompt = f"{type_prompt()}\n\nInput data:\n{text}\n\nRespond with JSON only."
    raw = client.complete(prompt)
    if not raw or not raw.strip():
        raise ValueError("Empty response from model")
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        # Strip fenced code blocks commonly returned by LLMs
        cleaned = cleaned.strip("`")
        cleaned = cleaned.lstrip("json").strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse LLM JSON: {exc}; raw={raw!r}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"LLM output is not a JSON object. raw={raw!r}")
    return parsed


def postprocess(result: Dict[str, Any]) -> Dict[str, Any]:
    entry_type = (result.get("entry_type") or "unknown").strip().lower().replace(" ", "_")
    material_type = (result.get("material_type") or "unknown").strip().lower().replace(" ", "_")
    component_type = (result.get("component_type") or "unknown").strip().lower().replace(" ", "_")
    raw_level3 = (result.get("level3_value") or "unknown").strip().lower().replace(" ", "_")

    if entry_type == "material":
        component_type = None
        normalized_level3 = normalize_level3_value(material_type, raw_level3) or "unknown"
    elif entry_type == "component":
        material_type = None
        normalized_level3 = normalize_level3_value(component_type, raw_level3) or "unknown"
    else:
        entry_type = "unknown"
        material_type = "unknown"
        component_type = "unknown"
        normalized_level3 = "unknown"

    return {
        "entry_type": entry_type,
        "material_type": material_type,
        "component_type": component_type,
        "level3_value_raw": raw_level3,
        "level3_value_normalized": normalized_level3,
    }


def build_item(uuid: str, name: str, classification: Dict[str, Any], source_row: Dict[str, str]) -> Dict[str, Any]:
    entry_type = classification["entry_type"]
    material_type = classification["material_type"]
    component_type = classification["component_type"]
    level3 = classification["level3_value_normalized"]

    facet: Dict[str, Any] = {}
    if entry_type == "material":
        facet["material_type"] = material_type
        facet["functional_types"] = ["unknown"]
        facet["application_areas"] = ["unknown"]
        facet["insulation_info"] = None
        facet["material_facet"] = {f"{material_type}_type": level3}
    elif entry_type == "component":
        facet["component_type"] = component_type
        facet["component_facet"] = {f"{component_type}_type": level3}
    else:
        facet["material_type"] = "unknown"
        facet["component_type"] = "unknown"

    return {
        "id": uuid,
        "item_core": {
            "core_id": uuid,
            "entry_type": entry_type,
            "name": name,
            "facet": facet,
        },
        "metadata": {
            "dataset_source": "OEKOBAUDAT one-shot",
            "dataset_uuid": uuid,
            "dataset_url": source_row.get("URL"),
            "category_original": source_row.get("Kategorie (original)") or source_row.get("Kategorie (en)"),
        },
    }


def decide_path(output_dir: Path, uuid: str, classification: Dict[str, Any]) -> Path:
    entry_type = classification["entry_type"]
    if entry_type == "material":
        level2 = classification["material_type"] or "unknown"
        return output_dir / "material" / level2 / f"{uuid}.json"
    if entry_type == "component":
        level2 = classification["component_type"] or "unknown"
        return output_dir / "component" / level2 / f"{uuid}.json"
    return output_dir / "unknown" / "unknown" / f"{uuid}.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch one-shot classify OBD samples and write JSONs.")
    parser.add_argument("--csv", default="data/lca_database/OBD_samples.csv", help="Input OBD CSV (semicolon separated).")
    parser.add_argument("--output-dir", default="temp/OBD_samples_one_shot", help="Output directory root.")
    parser.add_argument("--model", default="claude-3.5-sonnet", help="Claude model name.")
    parser.add_argument("--temperature", type=float, default=0.0, help="Sampling temperature.")
    parser.add_argument("--max-tokens", type=int, default=512, help="Max tokens to generate.")
    parser.add_argument("--resume", action="store_true", help="Skip UUIDs with existing JSON.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of UUIDs to process.")
    parser.add_argument("--filter-csv", type=Path, default=None, help="CSV with a 'uuid' column to restrict processing.")
    parser.add_argument("--encoding", default="utf-8-sig", help="Preferred CSV encoding (fallback to latin-1).")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    uuid_filter = load_uuid_filter(args.filter_csv)
    seen: set[str] = set()

    client = ClaudeClient(model=args.model, temperature=args.temperature, max_tokens=args.max_tokens)

    processed = 0
    for row in iter_csv_rows(Path(args.csv), args.encoding):
        uuid = row.get("UUID")
        if not uuid or uuid in seen:
            continue
        seen.add(uuid)
        if uuid_filter is not None and uuid not in uuid_filter:
            continue
        if args.resume:
            existing = list(output_dir.rglob(f"{uuid}.json"))
            if existing:
                continue
        name = row.get("Name (en)") or row.get("Name (de)") or ""
        payload = build_payload(row)
        try:
            raw_result = classify_text(client, payload)
            classification = postprocess(raw_result)
            out_path = decide_path(output_dir, uuid, classification)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            item = build_item(uuid, name, classification, row)
            out_path.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
            entry = classification["entry_type"]
            level2 = classification["material_type"] or classification["component_type"] or "unknown"
            level3 = classification["level3_value_normalized"]
            print(f"[ok] {uuid}: entry={entry}, level2={level2}, level3={level3} -> {out_path}")
            processed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] Failed for {uuid}: {exc}")
        if args.limit and processed >= args.limit:
            break

    print(f"Completed. Wrote {processed} items to {output_dir}")


if __name__ == "__main__":
    main()

