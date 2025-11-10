import time

import re

import json

import trafilatura

from typing import Dict
from typing import Any
from typing import Iterable
from typing import Optional

def extract_url(
    url: str,
    *,
    return_json: bool = True,
    select_keys: bool = True,
    keep_keys: Optional[Iterable[str]] = None,
) -> str:
    """
    Fetch a url page, optionally parse its 2-col pipe table, and return either JSON or TXT.

    Constants
    ----------
    retries : int = 2
        Number of retry attempts on failure (total tries = retries + 1).
    backoff_s : float = 1.0
        Initial backoff (seconds); doubles each retry.

    Parameters
    ----------
    url : str
        Page URL to fetch.

    return_json : bool
        If True, return a JSON string (dict of parsed fields).
        If False, return the raw extracted TXT (no parsing).
    select_keys : bool
        Only relevant when return_json=True.
        If True and keep_keys is provided, keep only those keys.
        If True but keep_keys is empty/None, no filtering is applied.
    keep_keys : Iterable[str] | None
        Keys to keep when select_keys=True.
        If None or empty, all parsed keys are kept.

    Returns
    -------
    str
        JSON string (when return_json=True) or raw TXT (when return_json=False).
        On failure: "{}" (JSON mode) or "" (TXT mode).
    """

    # Precompile regex once per call
    TABLE_ROW_RE = re.compile(r"^\|\s*(.*?)\s*\|\s*(.*?)\s*\|?$")

    # Fetch + extract text with light retries
    text: Optional[str] = None
    for attempt in range(3): # 2 retries
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                raise RuntimeError("fetch_url returned empty")
            extracted = trafilatura.extract(
                downloaded,
                output_format="txt",
                include_links=False,
                include_images=False,
            )
            if extracted and extracted.strip():
                text = extracted
                break
            raise RuntimeError("extract returned empty")
        except Exception:
            if attempt < 2:
                time.sleep(1.0 * (2 ** attempt)) # backoff_s: float = 1.0,
            else:
                return "{}" if return_json else ""

    # Return raw TXT if requested
    if not return_json:
        return text or ""

    # Parse the 2-col pipe table into a dict
    data: Dict[str, Any] = {}
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    current_key = None
    current_value = []

    for line in lines:
        m = TABLE_ROW_RE.match(line)
        if m:
            key, value = m.groups()
            if current_key:
                data[current_key] = " ".join(current_value).strip() or None
            current_key = key
            current_value = [value] if value else []
        else:
            if current_key:
                current_value.append(line)
    if current_key:
        data[current_key] = " ".join(current_value).strip() or None

    # Optionally filter keys
    if select_keys and keep_keys:
        keep_set = set(keep_keys)
        data = {k: v for k, v in data.items() if k in keep_set}

    # JSON-encode and return
    return json.dumps(data, ensure_ascii=False, indent=2)
