"""
Keep only rows for selected UUIDs from a semicolon CSV (preserving rows verbatim).
Configure everything in the CONFIG section below (no argparse, no terminal input).

This script is for testing, or if you want to extract only a speicific UUID
(in case the OBD gets updated, you would not have to extract all entries, and only
the new entries/UUIDs).

Make sure to simplify the OBD first with obd_simplify.py
"""

from pathlib import Path
import random

# =========================
# CONFIG — edit these only
# =========================
INPUT_PATH  = Path("data/lca_database/OBD_2024_I_A2.csv")      # path to your big OBD CSV
OUTPUT_PATH = Path("data/lca_database/OBD_show.csv") # path to write the reduced OBD CSV

"""
Choose how UUIDs are selected:
   - "manual" : only MANUAL_UUIDS
   - "random" : only RANDOM_COUNT randomly sampled UUIDs (seeded with RANDOM_SEED), for testing
"""
SELECT_MODE = "manual"  # "manual" | "random"

"""
When SELECT_MODE == "manual", choose whether to keep only MANUAL_UUIDS,
or subtract them (i.e., keep everything except MANUAL_UUIDS).
"""
MANUAL_POLICY = "keep"      # "keep" | "subtract"

# Manually chosen UUIDs to keep (optional)
MANUAL_UUIDS = [
    'b49b3145-9b55-46db-9a28-2359355f398e',
    'b7b7c6be-122f-48d9-b1c2-9b81a6b7e95c',
    '52d4092b-b220-4850-9179-4f11094da94e',
    'c269589f-1224-487b-8280-b0a6407edae7',
    'efe61c5a-ff60-4c5c-ba33-8b2dc2a4523a',
    'ba632d37-312b-447c-92cf-e86ee73d753e',
]

# When SELECT_MODE uses random
RANDOM_COUNT = 2
RANDOM_SEED  = 6  # set to None for unseeded randomness
# =========================


def first_field(line: str) -> str:
    """
    Extract the first field (UUID) without parsing the rest, to preserve the line verbatim.
    Assumes the UUID is the first field and fields are delimited by ';'.
    """
    idx = line.find(";")
    if idx == -1:
        # No delimiter found; return the entire (stripped) line as the UUID candidate
        return line.strip("\r\n")
    return line[:idx]


def main() -> None:
    # Read all lines as-is. newline="" prevents Python from altering line endings.
    with INPUT_PATH.open("r", encoding="latin1", newline="") as f:
        lines = f.readlines()

    if not lines:
        print("Input file is empty.")
        return

    header = lines[0]
    data_lines = lines[1:]

    # Collect distinct UUIDs in file order
    uuids = []
    seen = set()
    for line in data_lines:
        if not line.strip():
            continue
        u = first_field(line)
        if u and u not in seen:
            seen.add(u)
            uuids.append(u)

    # Build selection
    selected = set()

    if SELECT_MODE == "manual":
        manual_set = set(MANUAL_UUIDS)

        if MANUAL_POLICY == "keep":
            selected.update(manual_set)
        elif MANUAL_POLICY == "subtract":
            # In subtract mode, we keep everything EXCEPT the manual UUIDs.
            # We construct 'selected' as the complement relative to UUIDs present in the file.
            selected.update(u for u in uuids if u not in manual_set)
        else:
            raise ValueError(
                f"Invalid MANUAL_POLICY: {MANUAL_POLICY!r}. Must be 'keep' or 'subtract'."
            )

    elif SELECT_MODE == "random":
        pool = uuids
        if RANDOM_SEED is not None:
            random.seed(RANDOM_SEED)
        if RANDOM_COUNT > len(pool):
            raise RuntimeError(
                f"RANDOM_COUNT={RANDOM_COUNT} exceeds available pool size {len(pool)}."
            )
        selected.update(random.sample(pool, RANDOM_COUNT))

    else:
        raise ValueError(f"Invalid SELECT_MODE: {SELECT_MODE!r}. Must be 'manual' or 'random'.")


    # Final sanity checks
    if not selected:
        raise RuntimeError(
            "No UUIDs selected. Adjust SELECT_MODE / MANUAL_UUIDS / RANDOM_COUNT."
        )

    # Warn for any manual UUIDs not present
    if SELECT_MODE == "manual":
        missing = [u for u in MANUAL_UUIDS if u not in seen]
        if missing:
            print("WARNING: These manual UUIDs were not found in the input CSV:")
            for u in missing:
                print(f"  {u}")


    print(f"Keeping {len(selected)} UUID(s):")
    for u in selected:
        print(f"  {u}")

    # Filter lines: keep header + any data line whose first field (UUID) is selected
    kept = [header]
    kept_count = 0
    for line in data_lines:
        if not line.strip():
            continue
        u = first_field(line)
        if u in selected:
            kept.append(line)  # append original line verbatim
            kept_count += 1

    # Write output (verbatim lines)
    with OUTPUT_PATH.open("w", encoding="latin1", newline="") as f:
        for line in kept:
            f.write(line.replace(";", ","))

    print(f"Wrote {kept_count} row(s) (+ header) to: {OUTPUT_PATH.resolve()}")


if __name__ == "__main__":
    main()