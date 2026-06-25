"""Add NCHS county-level rural-urban classification.

Inputs:
    data/processed/county_office_access_with_acs.csv
    data/processed/county_office_access_base.csv

Outputs:
    data/processed/rural_urban_county_classification.csv
    data/processed/county_office_access_with_acs_rurality.csv
    outputs/rural_urban_classification_summary.md

This step adds NCHS 2023 rural-urban county classification only. It does not
add CMS enrollment data, Power BI files, or access-barrier index calculations.
"""

from __future__ import annotations

import csv
import ssl
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANALYTIC_INPUT = PROJECT_ROOT / "data" / "processed" / "county_office_access_with_acs.csv"
COUNTY_BASE_INPUT = PROJECT_ROOT / "data" / "processed" / "county_office_access_base.csv"
MANUAL_NCHS_INPUT = PROJECT_ROOT / "data" / "manual" / "NCHSurb-rural-codes.csv"
RURALITY_OUTPUT = PROJECT_ROOT / "data" / "processed" / "rural_urban_county_classification.csv"
MERGED_OUTPUT = PROJECT_ROOT / "data" / "processed" / "county_office_access_with_acs_rurality.csv"
SUMMARY_OUTPUT = PROJECT_ROOT / "outputs" / "rural_urban_classification_summary.md"

NCHS_SOURCE_PAGE = "https://www.cdc.gov/nchs/data-analysis-tools/urban-rural.html"
NCHS_CSV_URL = "https://www.cdc.gov/nchs/data/data-analysis/NCHSurb-rural-codes.csv"
NCHS_SOURCE_NAME = "National Center for Health Statistics 2023 Urban-Rural Classification Scheme for Counties"
NCHS_VERSION = "2023"

# The NCHS 2023 page states the scheme classifies 3,144 counties/county
# equivalents and excludes U.S. territories. Keep this explicit state-FIPS
# filter aligned with the county office access base and ACS steps.
ANALYTIC_STATE_FIPS_50_DC = {
    "01",
    "02",
    "04",
    "05",
    "06",
    "08",
    "09",
    "10",
    "11",
    "12",
    "13",
    "15",
    "16",
    "17",
    "18",
    "19",
    "20",
    "21",
    "22",
    "23",
    "24",
    "25",
    "26",
    "27",
    "28",
    "29",
    "30",
    "31",
    "32",
    "33",
    "34",
    "35",
    "36",
    "37",
    "38",
    "39",
    "40",
    "41",
    "42",
    "44",
    "45",
    "46",
    "47",
    "48",
    "49",
    "50",
    "51",
    "53",
    "54",
    "55",
    "56",
}

NCHS_CATEGORY_LABELS = {
    1: "Large central metro",
    2: "Large fringe metro",
    3: "Medium metro",
    4: "Small metro",
    5: "Micropolitan",
    6: "Noncore",
}

RURALITY_FIELDS = [
    "county_fips",
    "state_fips",
    "state_abbr",
    "county_name",
    "nchs_urban_rural_code",
    "nchs_urban_rural_category",
    "metro_nonmetro_flag",
]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    with path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def write_csv_rows(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def download_nchs_csv() -> tuple[str, str]:
    try:
        context = ssl.create_default_context()
        with urlopen(NCHS_CSV_URL, timeout=60, context=context) as response:
            content = response.read()
        return content.decode("cp1252"), NCHS_CSV_URL
    except (HTTPError, URLError, TimeoutError, ssl.SSLError, UnicodeDecodeError) as error:
        if MANUAL_NCHS_INPUT.exists():
            return MANUAL_NCHS_INPUT.read_text(encoding="cp1252"), str(MANUAL_NCHS_INPUT)
        instructions = (
            "Unable to download the official NCHS rural-urban classification CSV.\n"
            f"Source page: {NCHS_SOURCE_PAGE}\n"
            f"CSV URL: {NCHS_CSV_URL}\n"
            f"Manual fallback: download the CSV and save it as {MANUAL_NCHS_INPUT}\n"
            f"Original error: {error}"
        )
        raise RuntimeError(instructions) from error


def parse_nchs_rows(csv_text: str) -> list[dict[str, str]]:
    rows = list(csv.DictReader(csv_text.splitlines()))
    required_fields = {"STFIPS", "CTYFIPS", "ST_ABBREV", "CTYNAME", "CODE2023"}
    missing_fields = sorted(required_fields - set(rows[0].keys())) if rows else sorted(required_fields)
    if missing_fields:
        raise ValueError(
            "NCHS rural-urban file is missing expected columns: "
            + ", ".join(missing_fields)
        )
    return rows


def normalize_nchs_rows(nchs_rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for source_row in nchs_rows:
        state_fips = source_row["STFIPS"].strip().zfill(2)
        county_part = source_row["CTYFIPS"].strip().zfill(3)
        county_fips = f"{state_fips}{county_part}"
        if state_fips not in ANALYTIC_STATE_FIPS_50_DC:
            continue
        if not source_row["CODE2023"].strip():
            continue

        try:
            code = int(source_row["CODE2023"])
        except ValueError as error:
            raise ValueError(f"Invalid NCHS CODE2023 for county {county_fips}") from error
        if code not in NCHS_CATEGORY_LABELS:
            raise ValueError(f"Unexpected NCHS CODE2023 value {code} for county {county_fips}")

        lookup[county_fips] = {
            "county_fips": county_fips,
            "state_fips": state_fips,
            "state_abbr": source_row["ST_ABBREV"].strip(),
            "county_name": source_row["CTYNAME"].strip(),
            "nchs_urban_rural_code": code,
            "nchs_urban_rural_category": NCHS_CATEGORY_LABELS[code],
            "metro_nonmetro_flag": "Metro" if code in {1, 2, 3, 4} else "Nonmetro",
        }
    return lookup


def build_rurality_rows(
    analytic_rows: list[dict[str, str]],
    nchs_lookup: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rurality_rows: list[dict[str, Any]] = []
    unmatched_rows: list[dict[str, str]] = []

    for analytic_row in sorted(analytic_rows, key=lambda row: row["county_fips"]):
        county_fips = analytic_row["county_fips"]
        if county_fips[:2] not in ANALYTIC_STATE_FIPS_50_DC:
            raise RuntimeError(
                "Analytic input contains a county outside the 50 states and D.C. "
                f"universe: {county_fips}"
            )

        rurality_row = nchs_lookup.get(county_fips)
        if not rurality_row:
            unmatched_rows.append(analytic_row)
            continue

        # Preserve the project county naming fields from the analytic file so
        # downstream joins remain consistent with earlier pipeline steps.
        row = dict(rurality_row)
        row["county_name"] = analytic_row.get("county_name", row["county_name"])
        row["state_fips"] = analytic_row.get("state_fips", row["state_fips"])
        row["state_abbr"] = analytic_row.get("state_abbr", row["state_abbr"])
        rurality_rows.append(row)

    return rurality_rows, unmatched_rows


def merge_rurality(
    analytic_rows: list[dict[str, str]],
    rurality_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rurality_lookup = {row["county_fips"]: row for row in rurality_rows}
    merged_rows: list[dict[str, Any]] = []
    for analytic_row in analytic_rows:
        merged_row = dict(analytic_row)
        rurality_row = rurality_lookup.get(analytic_row["county_fips"], {})
        for field in [
            "nchs_urban_rural_code",
            "nchs_urban_rural_category",
            "metro_nonmetro_flag",
        ]:
            merged_row[field] = rurality_row.get(field, "")
        merged_rows.append(merged_row)
    return merged_rows


def to_int(value: str | int | None) -> int:
    if value in {None, ""}:
        return 0
    return int(value)


def summarize_by_flag(merged_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "county_count": 0,
            "office_count": 0,
            "counties_without_medicaid_office": 0,
        }
    )
    for row in merged_rows:
        flag = row.get("metro_nonmetro_flag", "Unmatched") or "Unmatched"
        summary[flag]["county_count"] += 1
        summary[flag]["office_count"] += to_int(row.get("office_count"))
        if to_int(row.get("has_medicaid_office")) == 0:
            summary[flag]["counties_without_medicaid_office"] += 1

    rows: list[dict[str, Any]] = []
    for flag in sorted(summary):
        values = summary[flag]
        county_count = values["county_count"]
        without_office = values["counties_without_medicaid_office"]
        share_without = round(without_office / county_count, 6) if county_count else None
        rows.append(
            {
                "metro_nonmetro_flag": flag,
                "county_count": county_count,
                "office_count": values["office_count"],
                "counties_without_medicaid_office": without_office,
                "share_counties_without_medicaid_office": share_without,
            }
        )
    return rows


def format_count_dict(counts: Counter[str]) -> str:
    if not counts:
        return "- None"
    return "\n".join(f"- {key}: {counts[key]}" for key in sorted(counts))


def format_metro_summary(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "- None"
    return "\n".join(
        "- {metro_nonmetro_flag}: {county_count} counties, {office_count} offices, "
        "{counties_without_medicaid_office} counties without office, "
        "{share_counties_without_medicaid_office} share without office".format(**row)
        for row in rows
    )


def write_summary(
    *,
    source_location: str,
    analytic_count: int,
    matched_count: int,
    unmatched_count: int,
    states_represented: int,
    category_counts: Counter[str],
    flag_counts: Counter[str],
    metro_summary_rows: list[dict[str, Any]],
    extra_nchs_rows_outside_base: int,
) -> None:
    run_timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    summary = f"""# Rural-Urban Classification Summary

- Source: {NCHS_SOURCE_NAME}
- Source page: {NCHS_SOURCE_PAGE}
- Source file: {source_location}
- Version/vintage: {NCHS_VERSION}
- Analytic universe: 50 states and District of Columbia
- Territories excluded: Yes, because the Medicaid office dataset covers the 50 states and D.C.
- Input file: `{ANALYTIC_INPUT.relative_to(PROJECT_ROOT)}`
- County base reference: `{COUNTY_BASE_INPUT.relative_to(PROJECT_ROOT)}`
- Rural-urban output: `{RURALITY_OUTPUT.relative_to(PROJECT_ROOT)}`
- Merged output: `{MERGED_OUTPUT.relative_to(PROJECT_ROOT)}`
- Counties in analytic input: {analytic_count}
- Counties matched: {matched_count}
- Counties unmatched: {unmatched_count}
- States/DC represented: {states_represented}
- NCHS rows outside project county base: {extra_nchs_rows_outside_base}
- Date/time run: {run_timestamp}

## Category Counts

{format_count_dict(category_counts)}

## Metro/Nonmetro Counts

{format_count_dict(flag_counts)}

## Metro/Nonmetro Office Access Summary

{format_metro_summary(metro_summary_rows)}

## Notes on Limitations

NCHS county-level rurality is useful for comparing broad geographic access patterns but may hide within-county variation, especially in large rural counties and mixed urban-suburban counties. This step uses the project county office plus ACS analytic file as the controlling universe and does not add CMS enrollment data, Power BI files, or barrier index calculations.
"""
    SUMMARY_OUTPUT.write_text(summary, encoding="utf-8")


def main() -> int:
    analytic_rows = read_csv_rows(ANALYTIC_INPUT)
    county_base_rows = read_csv_rows(COUNTY_BASE_INPUT)
    county_base_fips = {row["county_fips"] for row in county_base_rows}

    csv_text, source_location = download_nchs_csv()
    nchs_rows = parse_nchs_rows(csv_text)
    nchs_lookup = normalize_nchs_rows(nchs_rows)
    extra_nchs_rows_outside_base = len(set(nchs_lookup) - county_base_fips)

    rurality_rows, unmatched_rows = build_rurality_rows(analytic_rows, nchs_lookup)
    merged_rows = merge_rurality(analytic_rows, rurality_rows)

    merged_fields = list(
        dict.fromkeys(
            [
                *analytic_rows[0].keys(),
                "nchs_urban_rural_code",
                "nchs_urban_rural_category",
                "metro_nonmetro_flag",
            ]
        )
    )

    write_csv_rows(RURALITY_OUTPUT, rurality_rows, RURALITY_FIELDS)
    write_csv_rows(MERGED_OUTPUT, merged_rows, merged_fields)

    category_counts = Counter(row["nchs_urban_rural_category"] for row in rurality_rows)
    flag_counts = Counter(row["metro_nonmetro_flag"] for row in rurality_rows)
    metro_summary_rows = summarize_by_flag(merged_rows)
    states_represented = len({row["state_fips"] for row in merged_rows})

    print(f"Counties in county_office_access_with_acs.csv: {len(analytic_rows)}")
    print(f"Counties with rural-urban match: {len(rurality_rows)}")
    print(f"Counties missing rural-urban match: {len(unmatched_rows)}")
    print(f"States/DC represented: {states_represented}")
    print("Count by NCHS category:")
    for category in sorted(category_counts):
        print(f"- {category}: {category_counts[category]}")
    print("Count by metro_nonmetro_flag:")
    for flag in sorted(flag_counts):
        print(f"- {flag}: {flag_counts[flag]}")
    print("Metro/nonmetro office access summary:")
    for row in metro_summary_rows:
        print(
            "- {metro_nonmetro_flag}: {county_count} counties, {office_count} offices, "
            "{counties_without_medicaid_office} counties without office, "
            "{share_counties_without_medicaid_office} share without office".format(**row)
        )
    if unmatched_rows:
        print("Unmatched counties:")
        for row in unmatched_rows:
            print(f"- {row.get('county_name', '')} ({row.get('county_fips', '')})")

    write_summary(
        source_location=source_location,
        analytic_count=len(analytic_rows),
        matched_count=len(rurality_rows),
        unmatched_count=len(unmatched_rows),
        states_represented=states_represented,
        category_counts=category_counts,
        flag_counts=flag_counts,
        metro_summary_rows=metro_summary_rows,
        extra_nchs_rows_outside_base=extra_nchs_rows_outside_base,
    )

    print(f"Wrote rural-urban classification: {RURALITY_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"Wrote merged county file: {MERGED_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"Wrote summary: {SUMMARY_OUTPUT.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
