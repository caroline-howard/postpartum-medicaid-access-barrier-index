# Project Plan

## Project Purpose

This project will build a Power BI portfolio dashboard focused on postpartum Medicaid administrative access barriers. The dashboard combines public Medicaid office-location data, county-level ACS indicators, rural-urban context, and hospital-based obstetric care status to identify counties where limited office availability overlaps with postpartum-relevant access barriers after delivery.

The dashboard is intended as a policy-facing screening tool for identifying places that may warrant closer review, outreach, or support planning. It is not a causal analysis of Medicaid enrollment, retention, or health outcomes.

## Completed Milestones

- Medicaid office cleaning
- County assignment
- Complete county office access base table
- ACS indicators
- Female population ages 15-44
- Rural-urban classification
- Hospital-based obstetric care status

## Current Data Pipeline

1. Acquire the Medicaid office locations dataset from Harvard Dataverse.
2. Clean office address and coordinate fields.
3. Assign office points to counties.
4. Build a complete county office access base table, including zero-office counties.
5. Add ACS indicators relevant to postpartum administrative access barriers, including female population ages 15-44.
6. Add rural-urban classification to support metro/nonmetro comparisons.
7. Add hospital-based obstetric care status as clinical maternity access context.

## Future Milestones

- Build the Potential Postpartum Medicaid Administrative Access Barrier Index.
- Prepare Power BI export files.
- Build the Power BI report.
- Write portfolio summary.

## Planned Power BI Outputs

- National Postpartum Medicaid Access Overview
- Administrative vs. Clinical Access page
- State comparison dashboard page
- County access gaps page
- Potential Postpartum Medicaid Administrative Access Barrier Index page
- Data notes and limitations page

## Current Milestone Note

This cleanup milestone is limited to documentation, repo organization, pipeline instructions, status labels, and validation summary review. It does not add new data sources, Power BI files, or index calculations.
