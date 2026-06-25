"""Clean the raw Medicaid office locations workbook.

Input:
    data/raw/medicaid_offices.xlsx

Outputs:
    data/processed/medicaid_offices_clean.csv
    outputs/cleaning_summary.md

The raw Excel file is never modified. This script performs only the first
office-location cleaning step; it does not add county joins, ACS indicators,
CMS enrollment data, rurality fields, Power BI files, or index calculations.
"""

from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from openpyxl import load_workbook
except ImportError as exc:
    raise SystemExit(
        "Missing required package: openpyxl. Install it before running this script."
    ) from exc


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_INPUT = PROJECT_ROOT / "data" / "raw" / "medicaid_offices.xlsx"
CLEAN_OUTPUT = PROJECT_ROOT / "data" / "processed" / "medicaid_offices_clean.csv"
SUMMARY_OUTPUT = PROJECT_ROOT / "outputs" / "cleaning_summary.md"

EXPECTED_FIELDS = [
    "state_fips",
    "state_name",
    "agency_name",
    "street1",
    "street2",
    "city",
    "state",
    "zip_code",
    "latitude",
    "longitude",
]


def snake_case(value: Any) -> str:
    """Convert a spreadsheet column label to snake_case."""
    text = "" if value is None else str(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def clean_cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def build_full_address(row: dict[str, str]) -> str:
    parts = [
        row.get("street1", ""),
        row.get("street2", ""),
        row.get("city", ""),
        row.get("state", ""),
        row.get("zip_code", ""),
    ]
    return ", ".join(part for part in parts if part)


def build_office_id(row: dict[str, str]) -> str:
    stable_values = [
        row.get("state_fips", ""),
        row.get("state_name", ""),
        row.get("agency_name", ""),
        row.get("full_address", ""),
        row.get("latitude", ""),
        row.get("longitude", ""),
    ]
    digest = hashlib.sha1("|".join(stable_values).encode("utf-8")).hexdigest()[:12]
    return f"office_{digest}"


def read_workbook(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    workbook = load_workbook(path, read_only=True, data_only=True)
    worksheet = workbook[workbook.sheetnames[0]]
    rows = worksheet.iter_rows(values_only=True)

    try:
        raw_headers = next(rows)
    except StopIteration as exc:
        raise ValueError(f"Workbook is empty: {path}") from exc

    headers = [snake_case(header) for header in raw_headers]
    if len(headers) != len(set(headers)):
        duplicates = [header for header, count in Counter(headers).items() if count > 1]
        raise ValueError(f"Duplicate column names after snake_case conversion: {duplicates}")

    records: list[dict[str, str]] = []
    for values in rows:
        record = {
            header: clean_cell(value)
            for header, value in zip(headers, values, strict=False)
            if header
        }
        records.append(record)

    return headers, records


def validate_expected_fields(headers: list[str]) -> None:
    missing = [field for field in EXPECTED_FIELDS if field not in headers]
    if missing:
        expected = ", ".join(EXPECTED_FIELDS)
        found = ", ".join(headers)
        missing_text = ", ".join(missing)
        raise ValueError(
            "Missing expected field(s): "
            f"{missing_text}\nExpected fields: {expected}\nFound fields: {found}"
        )


def write_clean_csv(rows: list[dict[str, str]], source_headers: list[str]) -> None:
    CLEAN_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["office_id", *source_headers, "full_address"]

    with CLEAN_OUTPUT.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_summary(
    raw_count: int,
    clean_count: int,
    removed_missing_coordinates: int,
    states_represented: int,
    duplicate_coordinate_pairs: int,
) -> None:
    SUMMARY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    run_time = datetime.now().astimezone().isoformat(timespec="seconds")
    summary = f"""# Medicaid Office Cleaning Summary

- Input file path: `{RAW_INPUT.relative_to(PROJECT_ROOT)}`
- Output file path: `{CLEAN_OUTPUT.relative_to(PROJECT_ROOT)}`
- Raw row count: {raw_count}
- Cleaned row count: {clean_count}
- Rows removed for missing coordinates: {removed_missing_coordinates}
- States represented: {states_represented}
- Duplicate latitude/longitude pairs: {duplicate_coordinate_pairs}
- Date/time run: {run_time}
- Raw file modified: No

## Notes

The raw Excel file was not modified. Cleaning was performed by `scripts/02_clean_medicaid_offices.py`, and the cleaned CSV is generated locally under `data/processed/`.
"""
    SUMMARY_OUTPUT.write_text(summary, encoding="utf-8")


def main() -> int:
    if not RAW_INPUT.exists():
        raise FileNotFoundError(
            f"Missing raw input file: {RAW_INPUT.relative_to(PROJECT_ROOT)}. "
            "See docs/data_download_instructions.md."
        )

    headers, raw_rows = read_workbook(RAW_INPUT)
    validate_expected_fields(headers)

    cleaned_rows: list[dict[str, str]] = []
    removed_missing_coordinates = 0

    for row in raw_rows:
        latitude = row.get("latitude", "")
        longitude = row.get("longitude", "")
        if not latitude or not longitude:
            removed_missing_coordinates += 1
            continue

        cleaned_row = {header: row.get(header, "") for header in headers}
        cleaned_row["full_address"] = build_full_address(cleaned_row)
        cleaned_row["office_id"] = build_office_id(cleaned_row)
        cleaned_rows.append(cleaned_row)

    state_counts = Counter(row.get("state", "") for row in cleaned_rows if row.get("state", ""))
    coordinate_counts = Counter(
        (row.get("latitude", ""), row.get("longitude", "")) for row in cleaned_rows
    )
    duplicate_coordinate_pairs = sum(1 for count in coordinate_counts.values() if count > 1)

    write_clean_csv(cleaned_rows, headers)
    write_summary(
        raw_count=len(raw_rows),
        clean_count=len(cleaned_rows),
        removed_missing_coordinates=removed_missing_coordinates,
        states_represented=len(state_counts),
        duplicate_coordinate_pairs=duplicate_coordinate_pairs,
    )

    print(f"Raw row count: {len(raw_rows)}")
    print(f"Cleaned row count: {len(cleaned_rows)}")
    print(f"Rows removed for missing coordinates: {removed_missing_coordinates}")
    print(f"Number of states represented: {len(state_counts)}")
    print("Office count by state:")
    for state, count in sorted(state_counts.items()):
        print(f"- {state}: {count}")
    print(f"Duplicate latitude/longitude pairs: {duplicate_coordinate_pairs}")
    print(f"Wrote cleaned CSV: {CLEAN_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"Wrote cleaning summary: {SUMMARY_OUTPUT.relative_to(PROJECT_ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
