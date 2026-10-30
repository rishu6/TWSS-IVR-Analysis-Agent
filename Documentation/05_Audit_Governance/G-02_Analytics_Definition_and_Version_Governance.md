# G-02 — Analytics Definition and Version Governance

Baseline: 2026-10-30 · Status: **Draft — business review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

## Metric governance
Use P-09 as the metric baseline. Distinguish logical calls, unique callers, agent misses, total missed calls, department misses and department answer rate. Preserve current stage/owner semantics and all CRM candidates.

## Procedure and review
Changes require an example with the same time zone and cohort, regression evidence and a release note explaining the denominator. Record before/after expectations. Competitive rankings exclude Support and the known Vadant failover name variants; raw account counts retain their own scope.

---
Evidence: README.md; docs/phase-status.md; backend/app; frontend/src; scripts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
