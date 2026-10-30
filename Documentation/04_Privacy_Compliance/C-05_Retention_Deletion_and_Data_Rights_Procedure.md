# C-05 — Retention Deletion and Data Rights Procedure

Baseline: 2026-10-30 · Status: **Draft — business review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

## Implemented retention
Maintenance deletes expired sessions/tickets, deletes IntegrationEvent rows older than 90 days and clears older CallEvent payloads while preserving event identity and projections. Automatic SQLite backups are retained for seven days. Manual backups are not automatically pruned.

## Procedure and review
Calls, projections, leads, normalized phone indexes and audit logs do not have an implemented general business retention period. Define approved periods and rights handling. Deleting a call locally does not prevent the next provider sync from recreating it. Coordinate source-system records, backups, exports and legal holds; verify deletion with a documented request workflow.

---
Evidence: README.md; docs/phase-status.md; backend/app; frontend/src; scripts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
