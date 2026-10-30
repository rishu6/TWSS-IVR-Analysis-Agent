# G-04 — Access Review Procedure

Baseline: 2026-10-30 · Status: **Draft — business review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

## Proposed periodic review
Admin can create staff accounts, change roles or active status and reset passwords. Sensitive account updates revoke sessions; the last active Admin cannot be disabled or demoted. There is no SSO or MFA integration.

## Procedure and review
Maintain named accounts and review active users, roles and export privileges with the business owner. Revoke access promptly when staff leave. Record reviewer/date/actions outside this draft until an approved access-review record exists. Viewer masking is not department-level isolation.

---
Evidence: README.md; docs/phase-status.md; backend/app; frontend/src; scripts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
