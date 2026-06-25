# Project Plan

## Project Purpose

This project will build a Power BI portfolio dashboard that examines geographic access to Medicaid office locations and county-level administrative access barriers. The dashboard will combine public office-location, demographic, enrollment, rurality, and optional vulnerability data to identify places where in-person Medicaid enrollment support may be limited relative to need.

## Initial Milestone

The first milestone is only to prepare a clean repository structure and documentation foundation. It does not perform data analysis, add raw data files, create processed datasets, or build the Power BI report.

## Planned Data Pipeline

1. Acquire the Medicaid office locations dataset from Harvard Dataverse.
2. Clean office address and coordinate fields.
3. Prepare county boundary files for spatial joins and mapping.
4. Join office points to counties and calculate county office counts.
5. Add ACS, CMS Medicaid enrollment, rural-urban classification, and optional SVI indicators.
6. Calculate access measures such as office density, zero-office counties, and nearest-office distance.
7. Build a transparent county-level access barrier index.
8. Export final model-ready tables for Power BI.

## Planned Power BI Outputs

- National Medicaid office access map
- State comparison dashboard page
- County access gaps page
- Access Barrier Index page
- Data notes and limitations page

## First Milestone Note

This first milestone is limited to repository organization and documentation placeholders. Data analysis and dashboard development will begin in later milestones.
