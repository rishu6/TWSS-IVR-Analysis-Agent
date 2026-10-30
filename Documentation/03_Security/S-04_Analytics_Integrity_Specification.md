# S-04 — Analytics Integrity Specification

Baseline: 2026-10-30 · Status: **As-built draft — review pending**

Proposed responsible function: Data / QA / Engineering. No named assignment or approval is implied.

## Integrity objectives
Prevent inflated call counts, arbitrary lead selection, fabricated agent attempts and misleading rate denominators. This replaces learning-assessment integrity from the reference project; TWSS IVR has no grading, examinations or contest engine.

## Implemented boundaries
Provider call_id is the root identity. Exact restricted snapshots are deduplicated by hash; changed snapshots remain evidence. Caller phone/time proximity is not a merge rule. A dial is not automatically a missed attempt. Simultaneous/repeated dials do not establish an unambiguous attempt position. Every distinct matching CRM lead is preserved.

## Review controls
Reconcile totals before/after department filtering and pagination. Maintain tests for repeated records, unknown phone numbers, late updates, mapped labels without Department events, multiple CRM matches, current-owner lookup and zero denominators. Verify chart totals against the filtered hourly data and ties against all maxima. Capture expected-versus-actual count differences using synthetic or aggregate evidence, not full customer screenshots.

## Remaining risks
The provider can omit flow events; a saved database can be incomplete or stale; a changing CRM scan is not a transactional remote snapshot. Audit hashes do not establish an independent chain of custody. Formal external validation and historical stage/owner snapshots are not implemented. Corrective projection rebuilds must preserve source identity and be tested on a backup first.

---
Evidence: backend/app/cdr.py; backend/app/agent_outcomes.py; backend/app/crm.py; tests/test_dashboard_metrics.py. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
