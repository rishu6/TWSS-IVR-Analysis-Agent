# D-06 — Backup Disaster Recovery and Business Continuity

Baseline: 2026-10-30 · Status: **As-built / proposed guidance — review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

## Implemented backups
Local maintenance makes one integrity-checked SQLite backup per UTC day and prunes automatic backups older than seven days. Backups on the same Mac are not off-device disaster recovery. Manual backup files need separate retention management.

## Procedure and review
The SQLite helper does not back up Neon. Establish approved encrypted off-device storage and PostgreSQL recovery procedures, test restores into an isolated database and reconcile record counts without exposing customers. Recovery-time and recovery-point objectives remain unapproved and unmeasured.

---
Evidence: README.md; docs/phase-status.md; backend/app; frontend/src; scripts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
