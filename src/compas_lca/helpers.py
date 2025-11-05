import json

from pathlib import Path

from typing import Union

def load_json(input_data: Union[dict, str, Path]) -> dict:
    """Load JSON from dict or file path."""
    if isinstance(input_data, dict):
        return input_data
    if isinstance(input_data, (str, Path)):
        with open(input_data, "r", encoding="utf-8") as f:
            return json.load(f)
    raise TypeError(f"Unsupported type for input_data: {type(input_data).__name__}")

def merge_llm_meta(all_llm_meta: dict, llm_meta: dict) -> dict:
    """
    Merge numeric key-value pairs from `llm_meta` into `all_llm_meta`.
    Returns the updated `all_llm_meta` dictionary.
    """
    for key, value in llm_meta.items():
        if isinstance(value, (int, float)):
            all_llm_meta[key] = all_llm_meta.get(key, 0) + value
        else:
            all_llm_meta[key] = value
    return all_llm_meta