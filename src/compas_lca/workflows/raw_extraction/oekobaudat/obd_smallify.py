from pathlib import Path

import yaml


def _first_field(line: str) -> str:
    """
    Extract the first field (UUID) without parsing the rest, to preserve the line verbatim.
    Assumes the UUID is the first field and fields are delimited by ';'.
    """
    idx = line.find(";")
    if idx == -1:
        return line.strip("\r\n")
    return line[:idx]


def _load_manual_uuids_from_yaml(yaml_path: Path) -> set[str]:
    with yaml_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return {str(u).strip() for u in data.get("selected_UUIDs", []) if str(u).strip()}


def filter_obd(
    epd_parser_path: Path | str,
    input_csv_path: Path | str,
    output_csv_path: Path | str,
) -> None:
    """
    Keep ONLY the UUIDs listed under `selected_UUIDs` in the YAML.

    Reads and writes lines verbatim (encoding latin1; newline="") to preserve original formatting.
    Assumes UUID is the first ';'-delimited field.
    """
    epd_parser_path = Path(epd_parser_path)
    input_csv_path = Path(input_csv_path)
    output_csv_path = Path(output_csv_path)

    selected_set = _load_manual_uuids_from_yaml(epd_parser_path)
    if not selected_set:
        raise RuntimeError(f"No UUIDs found in YAML key 'selected_UUIDs': {epd_parser_path}")

    with input_csv_path.open("r", encoding="latin1", newline="") as f:
        header = f.readline()
        if header == "":
            raise RuntimeError(f"Input file is empty: {input_csv_path}")

        kept = [header]
        kept_count = 0
        seen: set[str] = set()

        for line in f:
            if not line.strip():
                continue
            u = _first_field(line)
            if u:
                seen.add(u)
            if u in selected_set:
                kept.append(line)
                kept_count += 1

    # Warn for any YAML UUIDs not present
    missing = [u for u in selected_set if u not in seen]
    if missing:
        print("WARNING: These selected UUIDs were not found in the input CSV:")
        for u in missing:
            print(f"  {u}")

    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    with output_csv_path.open("w", encoding="latin1", newline="") as f:
        f.writelines(kept)

    print(f"Keeping {len(selected_set)} selected UUID(s).")
    print(f"Wrote {kept_count} row(s) (+ header) to: {output_csv_path.resolve()}")