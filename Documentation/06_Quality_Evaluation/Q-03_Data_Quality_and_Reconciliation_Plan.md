# Q-03 — Data Quality and Reconciliation Plan

Baseline: 2026-10-30 · Status: **As-built / proposed guidance — review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

## Reconciliation method
Compare the same IST dates, inbound direction and department scope. Count logical provider calls, not raw CDR rows or agent legs. Check missing timestamps and quarantined identity conflicts before changing totals.

## Procedure and review
Verify normalized full phone equality across Phone and Mobile, complete pagination and all duplicate lead candidates. Failed CRM lookups remain unresolved rather than no-match. Distinguish stale saved information from confirmed absence. Do not reconstruct missing department selection or transfer ordering from guesswork.

---
Evidence: README.md; docs/phase-status.md; backend/app; frontend/src; scripts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
