# P-05 — User Workflow Specifications

Baseline: 2026-10-30 · Status: **As-built draft — review pending**

Proposed responsible function: Product / Operations. No named assignment or approval is implied.

## WF-01 Sign in
Receive assigned username and temporary password privately. Sign in and replace the temporary password before reading customer data. Invalid/locked credentials return an error; role comes from the stored account.

## WF-02 Daily analysis
Choose IST From/Through dates → department/status → Apply filters. Review totals, then click a KPI or department count for the scoped call list. An explicit drilldown carries context; ordinary sidebar navigation restores the destination tab's own filters.

## WF-03 Missed caller analysis
LeadSquared insights → Call status Missed → Apply → choose All missed calls or Missed after department selection. Both counts use the same date/search/department filters; choosing a subsection resets pagination and updates caller/lead details. Repeated phone numbers form one caller row with multiple calls.

## WF-04 Weekly staffing review
Call patterns → This week / Last week or custom dates → read busiest weekday/hour/combined slot → click a weekday or heatmap cell to focus hourly volume. Totals aggregate matching weekdays across the selected range. This week ends today; Last week is a full Monday–Sunday interval.

## WF-05 Missing history
Calendar filtering reads stored records only. Admin/Manager may use the supported history-import API or import script for the last 90 calendar days. Check job completion and rejected records; retry an ERROR job from its saved checkpoint. Do not substitute an undocumented archive endpoint.

## WF-06 Recovery
For cloud failure, distinguish Render sleep from Neon refusal. A confirmed monthly transfer suspension needs a billing-cycle reset or an explicitly authorized plan change. Local startup uses the Mac SQLite copy; it does not merge cloud-only records automatically. Follow D-07 before switching or restoring databases.

---
Evidence: frontend/src/ReportFilters.tsx; backend/app/history.py; scripts/internal.py. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
