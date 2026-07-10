import json

import yaml

import sys

import time

import threading

from pathlib import Path

from typing import Union
from typing import Any
from typing import Dict



def load_config(config_path: Path | str = "config.yaml") -> dict:
    """
    Load and validate the project configuration from a YAML file.

    Parameters
    ----------
    config_path : Path | str
        Path to the config.yaml file (default: project root).

    Returns
    -------
    dict
        Parsed configuration dictionary.

    Raises
    ------
    FileNotFoundError
        If config.yaml does not exist.
    KeyError
        If required keys are missing.
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path.resolve()}")

    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    # ---- required keys ----
    required_keys = ["project_folder"]

    missing = [key for key in required_keys if key not in config]
    if missing:
        raise KeyError(f"Missing required config keys: {missing}")

    return config



def load_json(input_data: Union[dict, str, Path]) -> dict:
    """Load JSON from dict or file path."""
    if isinstance(input_data, dict):
        return input_data
    if isinstance(input_data, (str, Path)):
        with open(input_data, "r", encoding="utf-8") as f:
            return json.load(f)
    raise TypeError(f"Unsupported type for input_data: {type(input_data).__name__}")

def merge_llm_meta(all_llm_meta: dict, llm_meta: dict | None) -> dict:
    """
    Merge numeric key-value pairs from `llm_meta` into `all_llm_meta`.
    Returns the updated `all_llm_meta` dictionary.
    """
    if not llm_meta:
        return all_llm_meta

    for key, value in llm_meta.items():
        if isinstance(value, (int, float)):
            all_llm_meta[key] = all_llm_meta.get(key, 0) + value
        else:
            all_llm_meta[key] = value

    return all_llm_meta

def coerce_to_dict(obj: Any) -> Dict[str, Any]:
    """Coerce dict / Pydantic BaseModel / dataclass-ish objects to a dict."""
    if obj is None:
        return {}
    if hasattr(obj, "model_dump"):
        return obj.model_dump(exclude_none=False)
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__dict__"):
        return vars(obj)
    return {}

class Spinner:
    def __init__(self, message: str = "Calculating impacts"):
        self._message = message
        self._running = False
        self._thread = None
        self._frames = ["/      ", "-       ", "\\      ", "|       "]

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def _spin(self):
        i = 0
        while self._running:
            frame = self._frames[i % len(self._frames)]
            sys.stdout.write(f"\r{self._message} {frame}")
            sys.stdout.flush()
            time.sleep(0.2)
            i += 1

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()
        # Clear spinner line and print final message
        sys.stdout.write("\rCreating impact reports...\n")
        sys.stdout.flush()