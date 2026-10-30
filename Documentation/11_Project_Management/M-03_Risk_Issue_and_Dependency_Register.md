# M-03 — Risk Issue and Dependency Register

Baseline: 2026-10-30 · Status: **Draft — business review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

## Open issues
High: Neon transfer exhaustion prevents cloud operation; off-device backups and restore drills are not established. Medium: provider transfer/ring data is incomplete; current-only CRM snapshots can be mistaken for history; exports omit some CRM cohort semantics; no formal load/security/accessibility certification.

## Procedure and review
Mitigations: operate locally within authorized access, restore database availability through an approved option, measure transfer consumption, label metrics accurately, reconcile cohorts and test restores. Track owner, severity, next action and evidence in the project issue system. Do not close a risk merely because this documentation describes it.

---
Evidence: README.md; docs/phase-status.md; backend/app; frontend/src; scripts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
