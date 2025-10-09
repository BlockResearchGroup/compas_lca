from __future__ import annotations
import csv
from typing import List
from typing import Set

# =======================
# USER SETTINGS
# =======================
INPUT_CSV: str = r"data/lca_database/OBD_indicators.csv"
OUTPUT_CSV: str = r"data/lca_database/OBD_items.csv"

UUID_COL: str = "UUID"
DROP_COLUMNS: List[str] = [
    "Version",
    "Name (de)",
    "Kategorie (original)",
    "Konformitaet",
    "Hintergrunddatenbank(en)",
    "Referenzjahr",
    "Gueltig bis",
    "Veroeffentlicht am",
    "Registrierungsnummer",
    "Registrierungsstelle",
    "UUID des Vorgaengers",
    "Version des Vorgaengers",
    "URL des Vorgaengers",
    "Bezugsgroesse",
    "Bezugseinheit",
    "Referenzfluss-UUID",
    "Referenzfluss-Name",
    "Schuettdichte (kg/m3)",
    "Flaechengewicht (kg/m2)",
    "Ergiebigkeit (m2)",
    "Laengengewicht (kg/m)",
    "Stueckgewicht (kg)",
    "Umrechungsfaktor auf 1kg",
    "biogener Kohlenstoffgehalt in kg",
    "biogener Kohlenstoffgehalt (Verpackung) in kg",
    "Modul",
    "Szenario",
    "Szenariobeschreibung",
    "GWP", "ODP", "POCP", "AP", "EP", "ADPE", "ADPF", "PERE", "PERM", "PERT", "PENRE", "PENRM", "PENRT", "SM", "RSF", "NRSF", "FW", "HWD", "NHWD", "RWD", "CRU", "MFR", "MER", "EEE", "EET",
    "GWPtotal (A2)",
    "AP (A2)",
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
    ""
]

ENCODING: str = "cp1252"
DELIMITER: str = ";"

DROP_ROWS_WITH_EMPTY_UUID: bool = False 
SHOW_SUMMARY: bool = True
# =======================

def clean_csv() -> None:
    with open(INPUT_CSV, "r", encoding=ENCODING, newline="") as fin:
        reader = csv.DictReader(fin, delimiter=DELIMITER)
        if reader.fieldnames is None:
            raise ValueError("No header row detected.")
        fieldnames_in = reader.fieldnames

        if UUID_COL not in fieldnames_in:
            raise ValueError(f"UUID column '{UUID_COL}' not found. Available: {fieldnames_in}")

        drop_set: Set[str] = set(DROP_COLUMNS or [])
        out_fieldnames = [c for c in fieldnames_in if c not in drop_set]

        with open(OUTPUT_CSV, "w", encoding=ENCODING, newline="") as fout:
            writer = csv.DictWriter(
                fout,
                fieldnames=out_fieldnames,
                delimiter=DELIMITER,
                lineterminator="\n",
                quoting=csv.QUOTE_MINIMAL,
            )
            writer.writeheader()

            seen = set()
            total_rows = 0
            written_rows = 0
            dup_count = 0
            empty_seen = False
            empty_dropped = 0

            for row in reader:
                total_rows += 1
                key = (row.get(UUID_COL) or "").strip()

                if not key:
                    if DROP_ROWS_WITH_EMPTY_UUID:
                        empty_dropped += 1
                        continue
                    if empty_seen:
                        dup_count += 1
                        continue
                    empty_seen = True
                else:
                    if key in seen:
                        dup_count += 1
                        continue
                    seen.add(key)

                writer.writerow({k: row.get(k, "") for k in out_fieldnames})
                written_rows += 1

    if SHOW_SUMMARY:
        missing = [c for c in drop_set if c not in fieldnames_in]
        actually_dropped = [c for c in drop_set if c in fieldnames_in]
        print(f"Input encoding: {ENCODING}")
        print(f"Delimiter: {repr(DELIMITER)}")
        print(f"Input rows: {total_rows}")
        print(f"Output rows: {written_rows}")
        print(f"Duplicate '{UUID_COL}' rows removed: {dup_count}")
        if DROP_ROWS_WITH_EMPTY_UUID:
            print(f"Rows dropped due to empty '{UUID_COL}': {empty_dropped}")
        print(f"Columns dropped: {actually_dropped}")
        if missing:
            print(f"Columns not found (skipped): {missing}")


if __name__ == "__main__":
    clean_csv()
