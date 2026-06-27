"""Prepare Power BI-ready export files.

Inputs:
    data/processed/county_postpartum_access_index.csv
    data/processed/medicaid_offices_with_county.csv
    data/processed/state_postpartum_access_index_summary.csv

Outputs:
    powerbi/data/county_postpartum_access_index.csv
    powerbi/data/medicaid_offices_with_county.csv
    powerbi/data/state_postpartum_access_index_summary.csv
    powerbi/data/powerbi_data_dictionary.csv
    powerbi/data/powerbi_export_metadata.json
    outputs/powerbi_export_summary.md

This step prepares dashboard-ready CSV artifacts only. It does not create or
modify a Power BI .pbix file.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COUNTY_INPUT = PROJECT_ROOT / "data" / "processed" / "county_postpartum_access_index.csv"
OFFICE_INPUT = PROJECT_ROOT / "data" / "processed" / "medicaid_offices_with_county.csv"
STATE_INPUT = PROJECT_ROOT / "data" / "processed" / "state_postpartum_access_index_summary.csv"

POWERBI_DATA_DIR = PROJECT_ROOT / "powerbi" / "data"
COUNTY_EXPORT = POWERBI_DATA_DIR / "county_postpartum_access_index.csv"
OFFICE_EXPORT = POWERBI_DATA_DIR / "medicaid_offices_with_county.csv"
STATE_EXPORT = POWERBI_DATA_DIR / "state_postpartum_access_index_summary.csv"
DATA_DICTIONARY_EXPORT = POWERBI_DATA_DIR / "powerbi_data_dictionary.csv"
METADATA_EXPORT = POWERBI_DATA_DIR / "powerbi_export_metadata.json"
SUMMARY_OUTPUT = PROJECT_ROOT / "outputs" / "powerbi_export_summary.md"

ANALYTIC_UNIVERSE = "50 states and District of Columbia"

COUNTY_FIELDS = [
    "county_fips",
    "county_name",
    "state_fips",
    "state_abbr",
    "state_name",
    "office_count",
    "has_medicaid_office",
    "has_hospital_obstetric_care",
    "no_hospital_obstetric_care",
    "poverty_rate",
    "no_vehicle_rate",
    "no_internet_rate",
    "limited_english_rate",
    "disability_rate",
    "female_15_44_rate",
    "metro_nonmetro_flag",
    "nchs_urban_rural_category",
    "no_medicaid_office_flag",
    "no_hospital_obstetric_care_flag",
    "high_poverty_flag",
    "high_no_vehicle_flag",
    "high_no_internet_flag",
    "high_limited_english_flag",
    "high_disability_flag",
    "high_female_15_44_flag",
    "nonmetro_flag",
    "postpartum_access_barrier_score",
    "postpartum_access_barrier_level",
    "index_component_count",
    "index_component_summary",
]

OFFICE_FIELDS = [
    "office_id",
    "agency_name",
    "full_address",
    "street1",
    "street2",
    "city",
    "state",
    "zip_code",
    "latitude",
    "longitude",
    "county_fips",
    "county_name",
    "state_abbr",
    "county_match_method",
]

STATE_FIELDS = [
    "state_fips",
    "state_abbr",
    "state_name",
    "total_counties",
    "average_postpartum_access_barrier_score",
    "median_postpartum_access_barrier_score",
    "counties_lower_concern",
    "counties_moderate_concern",
    "counties_high_concern",
    "counties_highest_concern",
    "share_counties_high_or_highest_concern",
    "counties_no_medicaid_office",
    "counties_no_hospital_obstetric_care",
    "counties_with_both_admin_and_clinical_gaps",
]

FIELD_DESCRIPTIONS = {
    "county_fips": "Five-digit Census county FIPS code used as the county join key.",
    "county_name": "County or county-equivalent name.",
    "state_fips": "Two-digit Census state FIPS code.",
    "state_abbr": "Two-letter state or District of Columbia abbreviation.",
    "state_name": "State or District of Columbia name.",
    "office_count": "Number of Medicaid office locations assigned to the county.",
    "has_medicaid_office": "Binary indicator for at least one Medicaid office in the county.",
    "has_hospital_obstetric_care": "Binary indicator for hospital-based obstetric care availability.",
    "no_hospital_obstetric_care": "Binary indicator for no hospital-based obstetric care identified.",
    "poverty_rate": "ACS county poverty rate.",
    "no_vehicle_rate": "ACS share of households with no vehicle available.",
    "no_internet_rate": "ACS share of households without an internet subscription.",
    "limited_english_rate": "ACS limited-English-speaking household rate.",
    "disability_rate": "ACS county disability rate used as an access-support context measure.",
    "female_15_44_rate": "ACS female population ages 15-44 share of total population.",
    "metro_nonmetro_flag": "Metro or Nonmetro county grouping from NCHS classification.",
    "nchs_urban_rural_category": "Readable NCHS urban-rural category label.",
    "no_medicaid_office_flag": "Index flag for no Medicaid office in county.",
    "no_hospital_obstetric_care_flag": "Index flag for no hospital-based obstetric care identified.",
    "high_poverty_flag": "Index flag for top-quartile poverty rate.",
    "high_no_vehicle_flag": "Index flag for top-quartile no-vehicle household rate.",
    "high_no_internet_flag": "Index flag for top-quartile no-internet subscription rate.",
    "high_limited_english_flag": "Index flag for top-quartile limited English rate.",
    "high_disability_flag": "Index flag for top-quartile disability rate.",
    "high_female_15_44_flag": "Index flag for top-quartile female population ages 15-44 rate.",
    "nonmetro_flag": "Index flag for Nonmetro county.",
    "postpartum_access_barrier_score": "Weighted Potential Postpartum Medicaid Administrative Access Barrier Index score.",
    "postpartum_access_barrier_level": "Concern level derived from the index score.",
    "index_component_count": "Count of triggered index component flags.",
    "index_component_summary": "Semicolon-separated list of triggered index components.",
    "office_id": "Stable Medicaid office identifier.",
    "agency_name": "Medicaid office or agency name.",
    "full_address": "Concatenated office address.",
    "street1": "Office street address line 1.",
    "street2": "Office street address line 2.",
    "city": "Office city.",
    "state": "Office state abbreviation from the source address.",
    "zip_code": "Office ZIP code.",
    "latitude": "Office latitude.",
    "longitude": "Office longitude.",
    "county_match_method": "Method used to assign the office to a county.",
    "total_counties": "Number of counties or county equivalents in the state.",
    "average_postpartum_access_barrier_score": "Average county index score in the state.",
    "median_postpartum_access_barrier_score": "Median county index score in the state.",
    "counties_lower_concern": "Count of counties in lower concern level.",
    "counties_moderate_concern": "Count of counties in moderate concern level.",
    "counties_high_concern": "Count of counties in high concern level.",
    "counties_highest_concern": "Count of counties in highest concern level.",
    "share_counties_high_or_highest_concern": "Share of counties at high or highest concern.",
    "counties_no_medicaid_office": "Count of counties with no Medicaid office.",
    "counties_no_hospital_obstetric_care": "Count of counties with no hospital-based obstetric care identified.",
    "counties_with_both_admin_and_clinical_gaps": "Count of counties with no Medicaid office and no hospital-based obstetric care identified.",
}

SOURCE_LAYERS = {
    "county_postpartum_access_index.csv": "County access index analytic base",
    "medicaid_offices_with_county.csv": "Medicaid office county assignment",
    "state_postpartum_access_index_summary.csv": "State-level index summary",
}


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


def require_fields(rows: list[dict[str, str]], fields: list[str], *, source: Path) -> None:
    if not rows:
        raise ValueError(f"Input file is empty: {source}")
    missing = sorted(set(fields) - set(rows[0]))
    if missing:
        raise ValueError(
            f"{source.relative_to(PROJECT_ROOT)} is missing required fields: "
            + ", ".join(missing)
        )


def select_fields(rows: list[dict[str, str]], fields: list[str]) -> list[dict[str, str]]:
    return [{field: row.get(field, "") for field in fields} for row in rows]


def normalize_office_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output_rows = []
    for row in rows:
        output = {field: row.get(field, "") for field in OFFICE_FIELDS}
        output["state_abbr"] = row.get("state_abbr") or row.get("county_state_abbr", "")
        output_rows.append(output)
    return output_rows


def count_duplicates(rows: list[dict[str, str]], key: str) -> int:
    seen = set()
    duplicates = 0
    for row in rows:
        value = row.get(key, "")
        if value in seen:
            duplicates += 1
        else:
            seen.add(value)
    return duplicates


def is_unique(rows: list[dict[str, str]], key: str) -> bool:
    return count_duplicates(rows, key) == 0


def build_data_dictionary_rows() -> list[dict[str, str]]:
    dictionary_rows = []
    file_fields = {
        "county_postpartum_access_index.csv": COUNTY_FIELDS,
        "medicaid_offices_with_county.csv": OFFICE_FIELDS,
        "state_postpartum_access_index_summary.csv": STATE_FIELDS,
    }
    for file_name, fields in file_fields.items():
        for field in fields:
            dictionary_rows.append(
                {
                    "file_name": file_name,
                    "field_name": field,
                    "description": FIELD_DESCRIPTIONS.get(field, ""),
                    "source_layer": SOURCE_LAYERS[file_name],
                    "use_in_powerbi": powerbi_use(file_name, field),
                }
            )
    return dictionary_rows


def powerbi_use(file_name: str, field: str) -> str:
    if field in {"county_fips", "state_abbr", "state_fips"}:
        return "Join/filter key"
    if file_name == "medicaid_offices_with_county.csv" and field in {"latitude", "longitude"}:
        return "Map point location"
    if field.endswith("_flag"):
        return "Index component flag"
    if field in {"postpartum_access_barrier_score", "postpartum_access_barrier_level"}:
        return "Index measure and category"
    if field in {"index_component_summary", "index_component_count"}:
        return "Tooltip/explainability"
    return "Dashboard field"


def write_metadata(
    county_rows: list[dict[str, str]],
    office_rows: list[dict[str, str]],
    state_rows: list[dict[str, str]],
) -> None:
    metadata = {
        "export_timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "input_files": [
            str(COUNTY_INPUT.relative_to(PROJECT_ROOT)),
            str(OFFICE_INPUT.relative_to(PROJECT_ROOT)),
            str(STATE_INPUT.relative_to(PROJECT_ROOT)),
        ],
        "output_files": [
            str(COUNTY_EXPORT.relative_to(PROJECT_ROOT)),
            str(OFFICE_EXPORT.relative_to(PROJECT_ROOT)),
            str(STATE_EXPORT.relative_to(PROJECT_ROOT)),
            str(DATA_DICTIONARY_EXPORT.relative_to(PROJECT_ROOT)),
            str(METADATA_EXPORT.relative_to(PROJECT_ROOT)),
        ],
        "county_row_count": len(county_rows),
        "office_row_count": len(office_rows),
        "state_row_count": len(state_rows),
        "analytic_universe": ANALYTIC_UNIVERSE,
        "notes": [
            "Exports are intended for Power BI import.",
            "County index export contains one row per county.",
            "Office export contains one row per Medicaid office.",
            "State export contains one row per state or District of Columbia.",
            "No age 65+ fields are included in the Power BI export package.",
            "This export step does not create a Power BI .pbix file.",
        ],
    }
    METADATA_EXPORT.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def write_summary(
    county_rows: list[dict[str, str]],
    office_rows: list[dict[str, str]],
    state_rows: list[dict[str, str]],
) -> None:
    SUMMARY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    county_unique = is_unique(county_rows, "county_fips")
    office_unique = is_unique(office_rows, "office_id")
    state_unique = is_unique(state_rows, "state_abbr")
    summary = f"""# Power BI Export Summary

## Input Files

- `{COUNTY_INPUT.relative_to(PROJECT_ROOT)}`
- `{OFFICE_INPUT.relative_to(PROJECT_ROOT)}`
- `{STATE_INPUT.relative_to(PROJECT_ROOT)}`

## Exported Files

- `{COUNTY_EXPORT.relative_to(PROJECT_ROOT)}`
- `{OFFICE_EXPORT.relative_to(PROJECT_ROOT)}`
- `{STATE_EXPORT.relative_to(PROJECT_ROOT)}`
- `{DATA_DICTIONARY_EXPORT.relative_to(PROJECT_ROOT)}`
- `{METADATA_EXPORT.relative_to(PROJECT_ROOT)}`

## Row Counts

- County index rows: {len(county_rows)}
- Medicaid office rows: {len(office_rows)}
- State summary rows: {len(state_rows)}

## Key Validation Checks

- `county_fips` unique in county index export: {county_unique}
- `office_id` unique in office export: {office_unique}
- `state_abbr` unique in state export: {state_unique}
- Duplicate `county_fips` values: {count_duplicates(county_rows, "county_fips")}
- Duplicate `office_id` values: {count_duplicates(office_rows, "office_id")}
- Duplicate `state_abbr` values: {count_duplicates(state_rows, "state_abbr")}

## Notes

These exports are intended for Power BI import. The county index file supports county-level maps, scorecards, and ranked tables. The Medicaid office file supports office point maps and office-level drillthrough. The state summary file supports state comparison visuals. The export package does not create or modify a Power BI `.pbix` report file. Age 65+ fields are intentionally excluded from the Power BI export package because they are not part of the postpartum index or dashboard context.
"""
    SUMMARY_OUTPUT.write_text(summary, encoding="utf-8")


def main() -> int:
    county_input_rows = read_csv_rows(COUNTY_INPUT)
    office_input_rows = read_csv_rows(OFFICE_INPUT)
    state_input_rows = read_csv_rows(STATE_INPUT)

    require_fields(county_input_rows, COUNTY_FIELDS, source=COUNTY_INPUT)
    require_fields(office_input_rows, [field for field in OFFICE_FIELDS if field != "state_abbr"], source=OFFICE_INPUT)
    require_fields(state_input_rows, STATE_FIELDS, source=STATE_INPUT)

    county_rows = select_fields(county_input_rows, COUNTY_FIELDS)
    office_rows = normalize_office_rows(office_input_rows)
    state_rows = select_fields(state_input_rows, STATE_FIELDS)
    dictionary_rows = build_data_dictionary_rows()

    write_csv_rows(COUNTY_EXPORT, county_rows, COUNTY_FIELDS)
    write_csv_rows(OFFICE_EXPORT, office_rows, OFFICE_FIELDS)
    write_csv_rows(STATE_EXPORT, state_rows, STATE_FIELDS)
    write_csv_rows(
        DATA_DICTIONARY_EXPORT,
        dictionary_rows,
        ["file_name", "field_name", "description", "source_layer", "use_in_powerbi"],
    )
    write_metadata(county_rows, office_rows, state_rows)
    write_summary(county_rows, office_rows, state_rows)

    print(f"County index rows exported: {len(county_rows)}")
    print(f"Office rows exported: {len(office_rows)}")
    print(f"State summary rows exported: {len(state_rows)}")
    print(f"county_fips unique in county export: {is_unique(county_rows, 'county_fips')}")
    print(f"office_id unique in office export: {is_unique(office_rows, 'office_id')}")
    print(f"state_abbr unique in state export: {is_unique(state_rows, 'state_abbr')}")
    print(f"Wrote Power BI export folder: {POWERBI_DATA_DIR.relative_to(PROJECT_ROOT)}")
    print(f"Wrote summary: {SUMMARY_OUTPUT.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
