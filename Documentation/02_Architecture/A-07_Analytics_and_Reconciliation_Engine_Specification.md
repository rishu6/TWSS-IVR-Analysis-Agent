# A-07 — Analytics and Reconciliation Engine Specification

Baseline: 2026-10-30 · Status: **As-built draft — review pending**

Proposed responsible function: Engineering / Data. No named assignment or approval is implied.

## Projection pipeline
Normalize and validate a CDR → identify the logical call → hash restricted content → deduplicate exact snapshots → combine retained event evidence → derive participants/final outcome/departments → apply effective mappings → persist the projection. Conflicting identity is quarantined rather than joined by phone/time. Null caller values preserve otherwise identified records.

## Report engines
reports.py produces inbound totals and department-rate denominators. agent_outcomes.py counts each agent once per call per outcome, tracks involvement and conservatively assigns recorded dial positions. crm_analytics.py groups known caller numbers, preserves unknown callers separately and combines current saved lead details with candidate evidence. Frontend callPatternsModel.ts aggregates existing hourly totals into the 7×24 IST matrix; totals must reconcile across day, hour and heatmap views.

## Required invariants
Department answered <= department calls <= inbound calls. Customer missed + missed without department = total missed. All-answered and department-answered figures must be separately labelled. Unique known caller count cannot exceed call count. A source-level absence does not justify a fabricated zero ring count. Best/worst ranking tie/exclusion rules must remain stable across pagination.

## Reconciliation playbook
Match timezone, date boundaries, direction, status, department scope and search before comparing totals. Compare the call ID set before investigating CRM matches. Check sync/import coverage, then quarantined records. Only then consider mapping/projection changes. A completed CRM match does not change telephony outcome or prove that the call created a lead.

---
Evidence: backend/app/cdr.py; backend/app/reports.py; backend/app/agent_outcomes.py; backend/app/crm_analytics.py; frontend/src/callPatternsModel.ts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
