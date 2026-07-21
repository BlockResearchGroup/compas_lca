import hashlib
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from compas_lca.workflows.raw_extraction.url.url_extraction import extract_url
from compas_lca.workflows.raw_extraction.url.url_keys import ILCD_EPD_KEYS

# =======================
# USER SETTINGS
# =======================
URL: str = "https://www.oekobaudat.de/OEKOBAU.DAT/resource/processes/cf3905b1-bc71-4e8d-9596-d1089b0e6f63?version=00.02.100"
RETRIES: int = 2
BACKOFF_S: float = 1.0
RETURN_JSON: bool = False
SELECT_KEYS: bool = True
OUTPUT_DIR: Path = Path("temp/url")
FILENAME_BASENAME: Optional[str] = None
# =======================


def _slugify_url(url: str, max_len: int = 80) -> str:
    parsed = urlparse(url)
    candidate = f"{parsed.netloc}{parsed.path}".strip("/")
    candidate = re.sub(r"[^A-Za-z0-9]+", "_", candidate).strip("_")
    if not candidate:
        candidate = "download"
    if len(candidate) > max_len:
        candidate = candidate[:max_len].rstrip("_")
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    return f"{candidate}_{h}"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    content: str = extract_url(
        URL,
        retries=RETRIES,
        backoff_s=BACKOFF_S,
        return_json=RETURN_JSON,
        select_keys=SELECT_KEYS,
        keep_keys=ILCD_EPD_KEYS,
    )

    # Decide extension and filename
    ext = ".json" if RETURN_JSON else ".txt"
    base = FILENAME_BASENAME or _slugify_url(URL)
    out_path = OUTPUT_DIR / f"{base}{ext}"

    # Write
    out_path.write_text(content, encoding="utf-8")
    print(f"Saved: {out_path.resolve()}")


if __name__ == "__main__":
    main()
