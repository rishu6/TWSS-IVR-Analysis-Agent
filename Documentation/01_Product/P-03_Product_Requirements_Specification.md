# P-03 — Product Requirements Specification

Baseline: 2026-10-30 · Status: **As-built draft — review pending**

Proposed responsible function: Product / Engineering. No named assignment or approval is implied.

## Functional acceptance matrix
| ID | Requirement and pass condition | Evidence |
|---|---|---|
| FR-01 | Staff sign in by username/password; client-selected role never elevates permissions | auth.py; test_internal.py |
| FR-02 | Overview counts distinct logical inbound calls and known unique phone numbers | reports.py; test_dashboard_metrics.py |
| FR-03 | Department answer rate excludes both answered and missed calls without routing evidence | reports.py; test_dashboard_metrics.py |
| FR-04 | Flow retains provider identity, unknown numbers, event order and reported misses | cdr.py; test_history_and_flow.py |
| FR-05 | LeadSquared preserves every matching lead and resolves owner names where available | crm_analytics.py; test_owner_directory.py |
| FR-06 | LeadSquared opens with all answered calls; Missed offers the department subsection | LeadSquaredInsights.tsx; ls-missed.spec.ts |
| FR-07 | Weekday/hour grouping uses Asia/Kolkata, preserves ties and has no zero-volume winner | callPatternsModel.ts; its unit tests |
| FR-08 | Sidebar navigation restores each tab's own applied query; row preferences are per route | main.tsx; PageSize.tsx; tab-filters.spec.ts |
| FR-09 | CSV/XLSX call exports require Manager/Admin and create audit records | api.py; test_api.py |
| FR-10 | History import checkpoints survive interruption and reject unsupported date ranges | history.py; test_history_and_flow.py |

## Error and empty states
An empty filtered page means no matching stored records; it does not prove complete provider coverage. CRM checking/pending is not equivalent to no lead. Invalid caller numbers do not erase identified call records. Provider failure retains previous data and surfaces health status. Zero department calls produce an unavailable rate, not a fabricated zero-percent success figure.

## Release constraints
Exact transfer edges, per-agent ring totals and recording playback remain unavailable. There is no claim of production load certification or uninterrupted cloud service. Generic exports do not include the full LeadSquared analytics table; department_selected export parity is an identified gap. See Q-01/Q-02 for verification and U-01 for user-facing operation.

---
Evidence: tests/; frontend/e2e/; frontend/e2e-internal/; backend/app/api.py. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
