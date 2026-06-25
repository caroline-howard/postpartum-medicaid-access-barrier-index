# County Assignment Summary

- Input file: `data/processed/medicaid_offices_clean.csv`
- Office-level output: `data/processed/medicaid_offices_with_county.csv`
- County count output: `data/processed/county_office_counts.csv`
- State summary output: `data/processed/state_office_summary.csv`
- Boundary source used: U.S. Census cartographic boundary county shapefile, cb_2025_us_county_500k
- Boundary file URL: `https://www2.census.gov/geo/tiger/GENZ2025/shp/cb_2025_us_county_500k.zip`
- Offices read: 3027
- Offices successfully matched: 3025
- Offices unmatched: 2
- Counties with at least one office: 2410
- States/DC represented: 51
- Date/time run: 2026-06-25T13:39:01-04:00

## Top 10 States By Office Count

- TX: 248
- CA: 239
- GA: 157
- KY: 132
- MO: 125
- VA: 120
- MN: 109
- NC: 104
- IN: 102
- IA: 100

## Unmatched Offices

Unmatched offices were written to `outputs/offices_without_county_match.csv`.

## Limitations

County assignment uses office latitude/longitude points and Census 2025 cartographic county boundaries. This is appropriate for county-level summaries but does not measure travel distance, within-county access variation, or whether an office serves residents across county or state lines. Boundary vintages may differ from the late-2023 office dataset. Coastal or boundary-edge points may fail to match generalized cartographic polygons; unmatched offices are exported for review instead of being forced into a county.
