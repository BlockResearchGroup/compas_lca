
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from compas_lca.llm.extraction_agents import (
    METADATA_AGENT,
    PARSE_MATERIAL_AGENT,
    DECOMPOSE_MATERIAL_AGENT,
)

load_dotenv()

# =================== USER CONFIG ===================
# Pick one: "metadata", "parse", "decompose"
AGENT_NAME = "metadata"

# Folders (relative to this file)
INPUT_DIR = Path("data/ifc_samples")
OUTPUT_DIRS = {
    "metadata": Path("data/extraction/element/metadata"),
    "parse": Path("data/extraction/element/material_parsed"),
    "decompose": Path("data/extraction/element/material_decomposed"),
}
DEBUG_DIR = Path("data/test_extraction_agent_element/.__debug__")   # set to None to disable
OVERWRITE = False                  # True = always overwrite outputs
# ===================================================

AGENTS = {
    "metadata": METADATA_AGENT,
    "parse": PARSE_MATERIAL_AGENT,
    "decompose": DECOMPOSE_MATERIAL_AGENT,
}

def to_dict(obj: Any) -> dict:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    if isinstance(obj, dict):
        return obj
    return json.loads(json.dumps(obj, default=str))

def run_on_file(agent, fp: Path, debug_dir: Path | None = None) -> dict:
    raw = fp.read_text(encoding="utf-8")
    res = agent.run_sync(raw)

    output = getattr(res, "output", None)
    if output is None and hasattr(res, "result"):
        output = getattr(res.result, "output", None)
    if output is None:
        if debug_dir:
            debug_dir.mkdir(parents=True, exist_ok=True)
            (debug_dir / (fp.stem + ".__no_output__.txt")).write_text(
                f"No output field on result: {type(res)}\n", encoding="utf-8"
            )
        raise RuntimeError("Agent returned no output payload")

    try:
        return to_dict(output)
    except Exception as e:
        if debug_dir:
            debug_dir.mkdir(parents=True, exist_ok=True)
            (debug_dir / (fp.stem + ".__coerce_fail__.txt")).write_text(
                f"Coercion error: {repr(e)}\nRaw output repr:\n{repr(output)}\n",
                encoding="utf-8",
            )
        raise

def main():
    if AGENT_NAME not in AGENTS:
        raise ValueError(f"Unknown AGENT_NAME '{AGENT_NAME}'. Choose one of {list(AGENTS)}")

    agent = AGENTS[AGENT_NAME]
    input_path = Path(INPUT_DIR)
    output_path = OUTPUT_DIRS[AGENT_NAME]
    debug_path = DEBUG_DIR

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set. Put it in your env or .env file.")

    if not input_path.exists():
        raise FileNotFoundError(f"Input dir not found: {input_path}")

    output_path.mkdir(parents=True, exist_ok=True)

    files = sorted(input_path.glob("*.json"))
    if not files:
        print(f"No .json files in {input_path}")
        return

    ok = err = skipped = 0
    for fp in files:
        out_fp = output_path / fp.name
        if out_fp.exists() and not OVERWRITE:
            print(f"[SKIP] {fp.name} (exists)")
            skipped += 1
            continue
        try:
            payload = run_on_file(agent, fp, debug_dir=debug_path)
            out_fp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"[OK]   {fp.name} → {out_fp.relative_to(output_path.parent)}")
            ok += 1
        except Exception as e:
            print(f"[ERROR] {fp.name}: {e}")
            err += 1

    print("\n=== Summary ===")
    print(f"Agent:     {AGENT_NAME}")
    print(f"Input:     {input_path}")
    print(f"Output:    {output_path}")
    print(f"Processed: {ok} OK, {err} ERROR, {skipped} SKIPPED")
    if debug_path and err:
        print(f"Debug:     {debug_path} (see __*.txt files)")

if __name__ == "__main__":
    main()
