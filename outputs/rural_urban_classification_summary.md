# Rural-Urban Classification Summary

- Source: National Center for Health Statistics 2023 Urban-Rural Classification Scheme for Counties
- Source page: https://www.cdc.gov/nchs/data-analysis-tools/urban-rural.html
- Source file: https://www.cdc.gov/nchs/data/data-analysis/NCHSurb-rural-codes.csv
- Version/vintage: 2023
- Analytic universe: 50 states and District of Columbia
- Territories excluded: Yes, because the Medicaid office dataset covers the 50 states and D.C.
- Input file: `data/processed/county_office_access_with_acs.csv`
- County base reference: `data/processed/county_office_access_base.csv`
- Rural-urban output: `data/processed/rural_urban_county_classification.csv`
- Merged output: `data/processed/county_office_access_with_acs_rurality.csv`
- Counties in analytic input: 3144
- Counties matched: 3144
- Counties unmatched: 0
- States/DC represented: 51
- NCHS rows outside project county base: 0
- Date/time run: 2026-06-25T14:48:19-04:00

## Category Counts

- Large central metro: 67
- Large fringe metro: 368
- Medium metro: 395
- Micropolitan: 658
- Noncore: 1300
- Small metro: 356

## Metro/Nonmetro Counts

- Metro: 1186
- Nonmetro: 1958

## Metro/Nonmetro Office Access Summary

- Metro: 1186 counties, 1543 offices, 170 counties without office, 0.143339 share without office
- Nonmetro: 1958 counties, 1484 offices, 563 counties without office, 0.287538 share without office

## Notes on Limitations

NCHS county-level rurality is useful for comparing broad geographic access patterns but may hide within-county variation, especially in large rural counties and mixed urban-suburban counties. This step uses the project county office plus ACS analytic file as the controlling universe and does not add CMS enrollment data, Power BI files, or barrier index calculations.
