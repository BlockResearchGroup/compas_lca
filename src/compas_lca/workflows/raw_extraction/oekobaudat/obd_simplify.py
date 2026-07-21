"""
This script simplifies the database such that EPD compliance is always the latest
EN15804/+A2 version. The initial CSV file mixed EN15804+A1/+A2 (EF 3.0/3.1), but
only a small handful of entries were within the outdated EN15804+A1/ and newer versions
of the OBD will completely discard them. Therefore this current hybrid version is reduced
to only EN15804/+A2 (a small set of entries are discarded, either with +A1 values or
empty indicator values).

CSV hyper link descriptor is called:
"ÖKOBAUDAT 2024-I as a CSV file with a period as the decimal separator"

Raw file is called:
"OBD_2024_I_2025-10-28T13_44_07.csv"

Raw file can be found in:
https://www.oekobaudat.de/en/service/downloads.html

Last accessed: 28.10.2025
"""

import pandas as pd

# config
in_path = "data/lca_database/OBD_2024_I_2025-10-28T13_44_07.csv"
out_path = "data/lca_database/OBD_2024_I_A2.csv"

# columns to check for data presence
check_cols = [
    "AP (A2)",
    "GWPtotal (A2)",
    "GWPbiogenic (A2)",
    "GWPfossil (A2)",
    "GWPluluc (A2)",
    "ETPfw (A2)",
    "PM (A2)",
    "EPmarine (A2)",
    "EPfreshwater (A2)",
    "EPterrestrial (A2)",
    "HTPc (A2)",
    "HTPnc (A2)",
    "IRP (A2)",
    "SOP (A2)",
    "ODP (A2)",
    "POCP (A2)",
    "ADPF (A2)",
    "ADPE (A2)",
    "WDP (A2)",
]

# columns to delete entirely (since they reference EN15804+A1)
drop_cols = ["GWP", "ODP", "POCP", "AP", "EP", "ADPE", "ADPF"]

# --- main ---
df = pd.read_csv(in_path, sep=";", dtype=str, keep_default_na=False, encoding="latin1")  # read as strings
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)  # trim whitespace

# Keep only rows that have at least one A2 indicator filled
cols = [c for c in check_cols if c in df.columns]
df[cols] = df[cols].replace(r"^\s*$", "", regex=True)
mask = (df[cols] != "").any(axis=1)
filtered = df[mask].copy()

# Drop empty indicator columns (if present)
filtered.drop(columns=[c for c in drop_cols if c in filtered.columns], inplace=True)

# Save cleaned version
filtered.to_csv(out_path, sep=";", index=False, encoding="latin1")

print(f"Rows in: {len(df)}, rows kept: {len(filtered)}, rows removed: {len(df) - len(filtered)}")
print(f"Columns removed: {[c for c in drop_cols if c not in filtered.columns]}")
