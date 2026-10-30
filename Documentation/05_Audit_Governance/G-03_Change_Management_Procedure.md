# G-03 — Change Management Procedure

Baseline: 2026-10-30 · Status: **Draft — business review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

## Proposed review process
Use a scoped branch or commit with a clear problem, final behaviour, validation and rollback plan. Avoid including environment files, database snapshots, customer exports or passwords in commits.

## Procedure and review
Review code and migration effects before release. Changes to definitions, role permissions, data retention or hosting cost need the corresponding business owner review. A Git commit is not a production deployment: Render auto-deploy is off and its database quota is currently blocked.

---
Evidence: README.md; docs/phase-status.md; backend/app; frontend/src; scripts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
