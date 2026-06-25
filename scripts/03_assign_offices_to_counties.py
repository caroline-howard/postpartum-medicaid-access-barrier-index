"""Assign cleaned Medicaid office locations to U.S. counties.

Input:
    data/processed/medicaid_offices_clean.csv

Outputs:
    data/processed/medicaid_offices_with_county.csv
    data/processed/county_office_counts.csv
    data/processed/state_office_summary.csv
    outputs/county_assignment_summary.md
    outputs/offices_without_county_match.csv, only when unmatched offices exist

This step only assigns offices to counties and creates office-count summaries.
It does not add ACS indicators, CMS enrollment data, rurality fields, Power BI
files, or barrier index calculations.
"""

from __future__ import annotations

import csv
import struct
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "medicaid_offices_clean.csv"
OFFICE_COUNTY_OUTPUT = PROJECT_ROOT / "data" / "processed" / "medicaid_offices_with_county.csv"
COUNTY_COUNTS_OUTPUT = PROJECT_ROOT / "data" / "processed" / "county_office_counts.csv"
STATE_SUMMARY_OUTPUT = PROJECT_ROOT / "data" / "processed" / "state_office_summary.csv"
SUMMARY_OUTPUT = PROJECT_ROOT / "outputs" / "county_assignment_summary.md"
UNMATCHED_OUTPUT = PROJECT_ROOT / "outputs" / "offices_without_county_match.csv"

BOUNDARY_SOURCE_NAME = "U.S. Census cartographic boundary county shapefile"
BOUNDARY_LAYER = "cb_2025_us_county_500k"
BOUNDARY_URL = "https://www2.census.gov/geo/tiger/GENZ2025/shp/cb_2025_us_county_500k.zip"

STATE_FIPS_TO_ABBR = {
    "01": "AL",
    "02": "AK",
    "04": "AZ",
    "05": "AR",
    "06": "CA",
    "08": "CO",
    "09": "CT",
    "10": "DE",
    "11": "DC",
    "12": "FL",
    "13": "GA",
    "15": "HI",
    "16": "ID",
    "17": "IL",
    "18": "IN",
    "19": "IA",
    "20": "KS",
    "21": "KY",
    "22": "LA",
    "23": "ME",
    "24": "MD",
    "25": "MA",
    "26": "MI",
    "27": "MN",
    "28": "MS",
    "29": "MO",
    "30": "MT",
    "31": "NE",
    "32": "NV",
    "33": "NH",
    "34": "NJ",
    "35": "NM",
    "36": "NY",
    "37": "NC",
    "38": "ND",
    "39": "OH",
    "40": "OK",
    "41": "OR",
    "42": "PA",
    "44": "RI",
    "45": "SC",
    "46": "SD",
    "47": "TN",
    "48": "TX",
    "49": "UT",
    "50": "VT",
    "51": "VA",
    "53": "WA",
    "54": "WV",
    "55": "WI",
    "56": "WY",
    "60": "AS",
    "66": "GU",
    "69": "MP",
    "72": "PR",
    "78": "VI",
}

STATE_ABBR_TO_NAME = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "DC": "District of Columbia",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "AS": "American Samoa",
    "GU": "Guam",
    "MP": "Northern Mariana Islands",
    "PR": "Puerto Rico",
    "VI": "U.S. Virgin Islands",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing input file: {path.relative_to(PROJECT_ROOT)}. "
            "Run scripts/02_clean_medicaid_offices.py first."
        )
    with path.open("r", newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def ring_bbox(ring: list[list[float]]) -> tuple[float, float, float, float]:
    xs = [point[0] for point in ring]
    ys = [point[1] for point in ring]
    return min(xs), min(ys), max(xs), max(ys)


def bbox_contains(bbox: tuple[float, float, float, float], lon: float, lat: float) -> bool:
    min_lon, min_lat, max_lon, max_lat = bbox
    return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat


def point_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    inside = False
    if len(ring) < 3:
        return inside

    previous_lon, previous_lat = ring[-1]
    for current_lon, current_lat in ring:
        crosses_lat = (current_lat > lat) != (previous_lat > lat)
        if crosses_lat:
            slope_lon = (
                (previous_lon - current_lon)
                * (lat - current_lat)
                / (previous_lat - current_lat)
                + current_lon
            )
            if lon < slope_lon:
                inside = not inside
        previous_lon, previous_lat = current_lon, current_lat

    return inside


def point_in_polygon(lon: float, lat: float, polygon: list[list[list[float]]]) -> bool:
    inside = False
    for ring in polygon:
        if point_in_ring(lon, lat, ring):
            inside = not inside
    return inside


def download_boundary_zip() -> bytes:
    try:
        with urlopen(BOUNDARY_URL, timeout=90) as response:
            return response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Could not download Census county boundary ZIP: {exc}") from exc


def read_dbf_records(dbf_bytes: bytes) -> list[dict[str, str]]:
    record_count = struct.unpack("<I", dbf_bytes[4:8])[0]
    header_length = struct.unpack("<H", dbf_bytes[8:10])[0]
    record_length = struct.unpack("<H", dbf_bytes[10:12])[0]

    fields = []
    offset = 32
    while dbf_bytes[offset] != 0x0D:
        descriptor = dbf_bytes[offset : offset + 32]
        name = descriptor[:11].split(b"\x00", 1)[0].decode("ascii").strip()
        length = descriptor[16]
        fields.append((name, length))
        offset += 32

    records = []
    for index in range(record_count):
        start = header_length + index * record_length
        record = dbf_bytes[start : start + record_length]
        if not record or record[:1] == b"*":
            continue

        position = 1
        parsed_record: dict[str, str] = {}
        for name, length in fields:
            raw_value = record[position : position + length]
            parsed_record[name] = raw_value.decode("latin1").strip()
            position += length
        records.append(parsed_record)

    return records


def read_shp_polygons(shp_bytes: bytes) -> list[dict[str, Any]]:
    position = 100
    shapes = []
    while position < len(shp_bytes):
        if position + 8 > len(shp_bytes):
            break
        content_length_words = struct.unpack(">i", shp_bytes[position + 4 : position + 8])[0]
        content_length = content_length_words * 2
        content_start = position + 8
        content = shp_bytes[content_start : content_start + content_length]
        position = content_start + content_length

        if len(content) < 44:
            continue
        shape_type = struct.unpack("<i", content[:4])[0]
        if shape_type not in {5, 15}:  # Polygon or PolygonZ
            shapes.append({"rings": [], "bbox": (0, 0, 0, 0)})
            continue

        min_lon, min_lat, max_lon, max_lat = struct.unpack("<4d", content[4:36])
        num_parts, num_points = struct.unpack("<2i", content[36:44])
        parts_start = 44
        points_start = parts_start + num_parts * 4
        parts = list(struct.unpack(f"<{num_parts}i", content[parts_start:points_start]))

        points = []
        for point_index in range(num_points):
            point_start = points_start + point_index * 16
            lon, lat = struct.unpack("<2d", content[point_start : point_start + 16])
            points.append([lon, lat])

        rings = []
        for part_index, start_index in enumerate(parts):
            end_index = parts[part_index + 1] if part_index + 1 < len(parts) else num_points
            rings.append(points[start_index:end_index])

        shapes.append({"rings": rings, "bbox": (min_lon, min_lat, max_lon, max_lat)})

    return shapes


def load_counties_from_boundary_zip(state_fips_values: set[str]) -> list[dict[str, Any]]:
    boundary_bytes = download_boundary_zip()
    with zipfile.ZipFile(BytesIO(boundary_bytes)) as archive:
        shp_name = next(name for name in archive.namelist() if name.endswith(".shp"))
        dbf_name = next(name for name in archive.namelist() if name.endswith(".dbf"))
        shapes = read_shp_polygons(archive.read(shp_name))
        records = read_dbf_records(archive.read(dbf_name))

    if len(shapes) != len(records):
        raise RuntimeError(
            f"Boundary shape/record count mismatch: {len(shapes)} shapes, {len(records)} records"
        )

    counties: list[dict[str, Any]] = []
    for record, shape in zip(records, shapes, strict=True):
        state_fips = str(record.get("STATEFP", "")).zfill(2)
        if state_fips not in state_fips_values:
            continue
        state_abbr = STATE_FIPS_TO_ABBR.get(state_fips, "")
        county_fips = str(record.get("GEOID", ""))
        county_name = str(record.get("NAMELSAD") or record.get("NAME", ""))
        if shape["rings"]:
            counties.append(
                {
                    "county_fips": county_fips,
                    "county_name": county_name,
                    "state_fips": state_fips,
                    "state_abbr": state_abbr,
                    "state_name": STATE_ABBR_TO_NAME.get(state_abbr, ""),
                    "polygons": [shape],
                }
            )
    return counties


def assign_county(
    lon: float,
    lat: float,
    counties_by_state: dict[str, list[dict[str, Any]]],
    state_abbr: str,
) -> dict[str, Any] | None:
    candidate_counties = counties_by_state.get(state_abbr, [])
    for county in candidate_counties:
        for polygon in county["polygons"]:
            if bbox_contains(polygon["bbox"], lon, lat) and point_in_polygon(
                lon, lat, polygon["rings"]
            ):
                return county

    # Fallback in case source state abbreviations differ from boundary state abbreviations.
    for counties in counties_by_state.values():
        for county in counties:
            for polygon in county["polygons"]:
                if bbox_contains(polygon["bbox"], lon, lat) and point_in_polygon(
                    lon, lat, polygon["rings"]
                ):
                    return county
    return None


def write_rows(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_county_counts(assigned_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    counts = Counter(row["county_fips"] for row in assigned_rows if row.get("county_fips"))
    county_lookup = {
        row["county_fips"]: {
            "county_fips": row["county_fips"],
            "county_name": row["county_name"],
            "state_abbr": row["county_state_abbr"],
            "state_name": STATE_ABBR_TO_NAME.get(row["county_state_abbr"], ""),
        }
        for row in assigned_rows
        if row.get("county_fips")
    }
    output = []
    for county_fips, count in sorted(counts.items()):
        row = dict(county_lookup[county_fips])
        row["office_count"] = count
        output.append(row)
    return output


def build_state_summary(
    assigned_rows: list[dict[str, str]],
    counties: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    office_counts = Counter(row.get("state", "") for row in assigned_rows)
    counties_with_office: dict[str, set[str]] = defaultdict(set)
    total_counties = Counter(county["state_abbr"] for county in counties if county["state_abbr"])

    for row in assigned_rows:
        state_abbr = row.get("state", "")
        county_fips = row.get("county_fips", "")
        if state_abbr and county_fips:
            counties_with_office[state_abbr].add(county_fips)

    output = []
    for state_abbr, office_count in sorted(office_counts.items()):
        total = total_counties.get(state_abbr, 0)
        county_count = len(counties_with_office.get(state_abbr, set()))
        output.append(
            {
                "state_fips": next(
                    (fips for fips, abbr in STATE_FIPS_TO_ABBR.items() if abbr == state_abbr),
                    "",
                ),
                "state_name": STATE_ABBR_TO_NAME.get(state_abbr, ""),
                "state_abbr": state_abbr,
                "office_count": office_count,
                "county_count_with_office": county_count,
                "total_counties": total,
                "share_counties_with_office": round(county_count / total, 4) if total else "",
            }
        )
    return output


def write_summary(
    offices_read: int,
    offices_matched: int,
    unmatched_rows: list[dict[str, str]],
    county_count: int,
    state_count: int,
    top_states: list[tuple[str, int]],
) -> None:
    SUMMARY_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    run_time = datetime.now().astimezone().isoformat(timespec="seconds")
    unmatched_note = (
        f"Unmatched offices were written to `{UNMATCHED_OUTPUT.relative_to(PROJECT_ROOT)}`."
        if unmatched_rows
        else "No unmatched offices were found, so no unmatched-office file was written."
    )
    top_states_text = "\n".join(f"- {state}: {count}" for state, count in top_states)
    summary = f"""# County Assignment Summary

- Input file: `{INPUT_FILE.relative_to(PROJECT_ROOT)}`
- Office-level output: `{OFFICE_COUNTY_OUTPUT.relative_to(PROJECT_ROOT)}`
- County count output: `{COUNTY_COUNTS_OUTPUT.relative_to(PROJECT_ROOT)}`
- State summary output: `{STATE_SUMMARY_OUTPUT.relative_to(PROJECT_ROOT)}`
- Boundary source used: {BOUNDARY_SOURCE_NAME}, {BOUNDARY_LAYER}
- Boundary file URL: `{BOUNDARY_URL}`
- Offices read: {offices_read}
- Offices successfully matched: {offices_matched}
- Offices unmatched: {len(unmatched_rows)}
- Counties with at least one office: {county_count}
- States/DC represented: {state_count}
- Date/time run: {run_time}

## Top 10 States By Office Count

{top_states_text}

## Unmatched Offices

{unmatched_note}

## Limitations

County assignment uses office latitude/longitude points and Census 2025 cartographic county boundaries. This is appropriate for county-level summaries but does not measure travel distance, within-county access variation, or whether an office serves residents across county or state lines. Boundary vintages may differ from the late-2023 office dataset. Coastal or boundary-edge points may fail to match generalized cartographic polygons; unmatched offices are exported for review instead of being forced into a county.
"""
    SUMMARY_OUTPUT.write_text(summary, encoding="utf-8")


def main() -> int:
    office_rows = read_csv(INPUT_FILE)
    state_fips_values = sorted(
        {
            str(row.get("state_fips", "")).zfill(2)
            for row in office_rows
            if row.get("state_fips", "")
        }
    )
    print("Downloading Census county cartographic boundary shapefile...", flush=True)
    counties = load_counties_from_boundary_zip(set(state_fips_values))
    print(f"Loaded {len(counties)} county boundary features.", flush=True)
    counties_by_state: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for county in counties:
        counties_by_state[county["state_abbr"]].append(county)

    assigned_rows: list[dict[str, str]] = []
    unmatched_rows: list[dict[str, str]] = []

    for row in office_rows:
        try:
            lat = float(row.get("latitude", ""))
            lon = float(row.get("longitude", ""))
        except ValueError:
            unmatched_rows.append(row)
            continue

        county = assign_county(lon, lat, counties_by_state, row.get("state", ""))
        output_row = dict(row)
        if county:
            output_row.update(
                {
                    "county_fips": county["county_fips"],
                    "county_name": county["county_name"],
                    "county_state_abbr": county["state_abbr"],
                }
            )
            assigned_rows.append(output_row)
        else:
            output_row.update({"county_fips": "", "county_name": "", "county_state_abbr": ""})
            unmatched_rows.append(output_row)

    office_fieldnames = list(office_rows[0].keys()) + [
        "county_fips",
        "county_name",
        "county_state_abbr",
    ]
    write_rows(OFFICE_COUNTY_OUTPUT, assigned_rows + unmatched_rows, office_fieldnames)

    county_counts = build_county_counts(assigned_rows)
    write_rows(
        COUNTY_COUNTS_OUTPUT,
        county_counts,
        ["county_fips", "county_name", "state_abbr", "state_name", "office_count"],
    )

    state_summary = build_state_summary(assigned_rows, counties)
    write_rows(
        STATE_SUMMARY_OUTPUT,
        state_summary,
        [
            "state_fips",
            "state_name",
            "state_abbr",
            "office_count",
            "county_count_with_office",
            "total_counties",
            "share_counties_with_office",
        ],
    )

    if unmatched_rows:
        write_rows(UNMATCHED_OUTPUT, unmatched_rows, office_fieldnames)
    elif UNMATCHED_OUTPUT.exists():
        UNMATCHED_OUTPUT.unlink()

    state_counts = Counter(row.get("state", "") for row in assigned_rows)
    top_states = state_counts.most_common(10)
    write_summary(
        offices_read=len(office_rows),
        offices_matched=len(assigned_rows),
        unmatched_rows=unmatched_rows,
        county_count=len(county_counts),
        state_count=len(state_counts),
        top_states=top_states,
    )

    print(f"Number of offices read: {len(office_rows)}")
    print(f"Number of offices assigned to counties: {len(assigned_rows)}")
    print(f"Number of offices not assigned to counties: {len(unmatched_rows)}")
    print(f"Number of counties with at least one office: {len(county_counts)}")
    print(f"Number of states/DC represented: {len(state_counts)}")
    print("Top 10 states by office count:")
    for state, count in top_states:
        print(f"- {state}: {count}")
    if unmatched_rows:
        print(f"Unmatched offices written to: {UNMATCHED_OUTPUT.relative_to(PROJECT_ROOT)}")
    else:
        print("Any unmatched offices: none")
    print(f"Wrote office county assignment: {OFFICE_COUNTY_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"Wrote county office counts: {COUNTY_COUNTS_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"Wrote state office summary: {STATE_SUMMARY_OUTPUT.relative_to(PROJECT_ROOT)}")
    print(f"Wrote county assignment summary: {SUMMARY_OUTPUT.relative_to(PROJECT_ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
