# Project Plan

## Project Purpose

This project will build a Power BI portfolio dashboard focused on postpartum Medicaid administrative access barriers. The dashboard will combine public Medicaid office-location data, county-level ACS indicators, and rural-urban context to identify counties where limited office availability overlaps with postpartum-relevant access barriers after delivery.

The dashboard is intended as a policy-facing screening tool for identifying places that may warrant closer review, outreach, or support planning. It is not a causal analysis of Medicaid enrollment, retention, or health outcomes.

## Initial Milestone

The first milestone was to prepare a clean repository structure and documentation foundation. The current framing milestone narrows the project around postpartum Medicaid access barriers without adding new data sources, scripts, index calculations, or Power BI files.

## Planned Data Pipeline

1. Acquire the Medicaid office locations dataset from Harvard Dataverse.
2. Clean office address and coordinate fields.
3. Prepare county boundary files for spatial joins and mapping.
4. Join office points to counties and calculate county office counts.
5. Add ACS indicators relevant to postpartum administrative access barriers, including a future reproductive-age population context measure such as female population ages 15-44.
6. Add rural-urban classification to support metro/nonmetro comparisons.
7. Build a transparent Potential Postpartum Medicaid Administrative Access Barrier Index.
8. Export final model-ready tables for Power BI.

## Planned Power BI Outputs

- National Postpartum Medicaid Access Overview
- State comparison dashboard page
- County access gaps page
- Potential Postpartum Medicaid Administrative Access Barrier Index page
- Data notes and limitations page

## Current Milestone Note

This milestone is limited to project framing and documentation. It does not add new data, scripts, Power BI files, or index calculations.
