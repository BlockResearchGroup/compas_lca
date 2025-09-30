"""
- Make sure to create OBD_sample.csv first with scripts/oekobaudat_sample.py
- For each row:
  * Fetch the URL with trafilatura.
  * Extract the main plain-text content.
  * Save to <UUID>.txt in the output folder.
"""

import os
import pandas as pd
import trafilatura
from pathlib import Path

# =======================
# USER SETTINGS
# =======================
INPUT_CSV = Path("temp/inventory_data/dissected/precast_concrete/OBD_precast_concrete_sample.csv")
OUTPUT_DIR = Path("temp/inventory_data/dissected/precast_concrete/raw/01_scrapes_txt")

ENCODING = "cp1252"    # or "utf-8-sig" depending on CSV
DELIMITER = ";"        # "," or ";" or "\t"
UUID_COL = "UUID"
URL_COL = "URL"
# =======================


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = pd.read_csv(INPUT_CSV, encoding=ENCODING, delimiter=DELIMITER)

    if UUID_COL not in df.columns or URL_COL not in df.columns:
        raise ValueError(f"CSV must contain columns '{UUID_COL}' and '{URL_COL}'")

    for i, row in df.iterrows():
        uuid = str(row[UUID_COL]).strip()
        url = str(row[URL_COL]).strip()

        if not uuid or not url or url.lower() == "nan":
            print(f"Skipping row {i}: missing UUID or URL")
            continue

        print(f" Fetching {url} (UUID={uuid})...")

        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            print(f"Could not fetch {url}")
            continue

        text = trafilatura.extract(
            downloaded,
            output_format="txt",
            include_links=False,
            include_images=False,
        )

        if not text:
            print(f"Could not extract text from {url}")
            continue

        out_path = os.path.join(OUTPUT_DIR, f"{uuid}.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
