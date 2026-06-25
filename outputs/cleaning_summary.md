# Medicaid Office Cleaning Summary

- Input file path: `data/raw/medicaid_offices.xlsx`
- Output file path: `data/processed/medicaid_offices_clean.csv`
- Available workbook sheets: `Sheet1`
- Selected worksheet: `Sheet1`
- Raw row count: 3027
- Cleaned row count: 3027
- Article-reported office count: 3026
- Rows removed for missing coordinates: 0
- States represented: 51
- Duplicate latitude/longitude pairs: 0
- Exact duplicate source rows: 0
- Blank source rows: 0
- Rows with invalid or suspicious coordinates: 0
- Date/time run: 2026-06-25T13:18:52-04:00
- Raw file modified: No

## Workbook Structure

The workbook contains one sheet, so `Sheet1` is the selected data sheet.

## Required Field Checks

- Rows missing `agency_name`: 0
- Rows missing `street1`: 0
- Rows missing `city`: 0
- Rows missing `state`: 0
- Rows missing `zip_code`: 0

## Suspicious Row Checks

- None found

## Count Discrepancy Note

The Data in Brief article reports 3,026 office locations. The downloaded Excel file currently contains 3,027 rows after cleaning. No metadata, blank, duplicated, or invalid row was identified by the current validation checks, so the cleaning step preserves the source file as downloaded and documents the count discrepancy transparently.

## Notes

The raw Excel file was not modified. Cleaning was performed by `scripts/02_clean_medicaid_offices.py`, and the cleaned CSV is generated locally under `data/processed/`.
