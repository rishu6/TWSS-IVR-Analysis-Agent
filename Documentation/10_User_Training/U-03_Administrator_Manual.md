# U-03 — Administrator Manual

Baseline: 2026-10-30 · Status: **As-built / proposed guidance — review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

## Administration
Admins manage named accounts, roles, password resets, department mappings and approved imports. Use strong unique temporary passwords and let staff change them at first login. Role, active-status and password changes revoke sessions. Protect the last active Admin.

## Procedure and review
Historical date filters query stored records; they do not automatically fetch missing dates. Start or resume an approved import within supported history bounds. Check integration progress and quarantine for data failures. Protect private environment files and runtime backups; never email credentials or copy them into GitHub issues. Username changes are not an exposed self-service feature.

---
Evidence: README.md; docs/phase-status.md; backend/app; frontend/src; scripts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
