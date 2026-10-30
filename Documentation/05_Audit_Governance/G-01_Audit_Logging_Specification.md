# G-01 — Audit Logging Specification

Baseline: 2026-10-30 · Status: **Draft — business review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

## Implemented audit events
Audit entries record time, role, action, resource and user identity. Examples include login/logout, password changes, account changes, export, sync requests, history imports and restricted raw-data access. Audit records are stored in the application database.

## Procedure and review
Not every report read is audited, and the log is not cryptographically immutable or exported to an independently controlled security system. Restrict access, review privileged changes and define a retention policy. Do not treat operational logs as a complete history of every customer-record view.

---
Evidence: README.md; docs/phase-status.md; backend/app; frontend/src; scripts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
