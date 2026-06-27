# Power BI Export Summary

## Input Files

- `data/processed/county_postpartum_access_index.csv`
- `data/processed/medicaid_offices_with_county.csv`
- `data/processed/state_postpartum_access_index_summary.csv`

## Exported Files

- `powerbi/data/county_postpartum_access_index.csv`
- `powerbi/data/medicaid_offices_with_county.csv`
- `powerbi/data/state_postpartum_access_index_summary.csv`
- `powerbi/data/powerbi_data_dictionary.csv`
- `powerbi/data/powerbi_export_metadata.json`

## Row Counts

- County index rows: 3144
- Medicaid office rows: 3027
- State summary rows: 51

## Key Validation Checks

- `county_fips` unique in county index export: True
- `office_id` unique in office export: True
- `state_abbr` unique in state export: True
- Duplicate `county_fips` values: 0
- Duplicate `office_id` values: 0
- Duplicate `state_abbr` values: 0

## Notes

These exports are intended for Power BI import. The county index file supports county-level maps, scorecards, and ranked tables. The Medicaid office file supports office point maps and office-level drillthrough. The state summary file supports state comparison visuals. The export package does not create or modify a Power BI `.pbix` report file. Age 65+ fields are intentionally excluded from the Power BI export package because they are not part of the postpartum index or dashboard context.
