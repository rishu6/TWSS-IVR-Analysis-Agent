# Q-01 — Test Strategy and Coverage

Baseline: 2026-10-30 · Status: **As-built / proposed guidance — review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

## Verification layers
Backend tests cover API permissions, normalization, reconciliation, imports, metrics and database behaviour. Frontend tests cover calculation models and route behaviour; targeted browser checks exercise synthetic interfaces. Tests use fixtures rather than provider production writes.

## Procedure and review
The last recorded application baseline is 111 backend and 20 frontend passing tests. This is not a coverage percentage, load certification or assurance that every historic browser test was rerun. For this documentation release, see validation-results.json for the checks actually executed.

---
Evidence: README.md; docs/phase-status.md; backend/app; frontend/src; scripts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
