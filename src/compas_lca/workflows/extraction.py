
# temporary script demonstrating metadata extraction workflow
# new workflow where only context is imported (and not the entire instantiated agent)

import os
import json
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv, find_dotenv

from compas_lca.llm.agent import BaseAgent
from compas_lca.ctx.extraction_context import METADATA_CTX

INPUT_DIR = Path("data/ifc_samples")
OUTPUT_DIR = Path("temp/samples_metadata")
OVERWRITE = False  # set True to overwrite existing outputs


def to_dict(obj: Any) -> dict:
    """Coerce a pydantic model or other object to a plain dict."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, dict):
        return obj
    return json.loads(json.dumps(obj, default=str))


def run_file(agent: BaseAgent, fp: Path) -> dict:
    """Run the metadata agent on one JSON file (raw text in, dict out)."""
    raw = fp.read_text(encoding="utf-8")
    run = agent.execute_run(raw)
    payload = getattr(run.result, "data", None)
    if payload is None:
        raise RuntimeError(f"No output payload for {fp.name}")
    return to_dict(payload)


def main() -> None:

    load_dotenv(find_dotenv(), override=False)

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set (put it in your environment or .env)")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    metadata_agent = BaseAgent.from_config(context=METADATA_CTX)

    files = sorted(INPUT_DIR.glob("*.json"))
    if not files:
        print(f"No .json files in {INPUT_DIR}")
        return

    ok = err = skipped = 0
    for fp in files:
        out_fp = OUTPUT_DIR / fp.name
        if out_fp.exists() and not OVERWRITE:
            print(f"[SKIP] {fp.name} (exists)")
            skipped += 1
            continue

        try:
            data = run_file(metadata_agent, fp)
            out_fp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"[OK]   {fp.name} → {out_fp.relative_to(OUTPUT_DIR.parent)}")
            ok += 1
        except Exception as e:
            print(f"[ERROR] {fp.name}: {e}")
            err += 1

    print("\n=== Summary ===")
    print(f"Input:     {INPUT_DIR}")
    print(f"Output:    {OUTPUT_DIR}")
    print(f"Processed: {ok} OK, {err} ERROR, {skipped} SKIPPED")


if __name__ == "__main__":
    main()
