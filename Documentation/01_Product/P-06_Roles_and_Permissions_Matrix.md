# P-06 — Roles and Permissions Matrix

Baseline: 2026-10-30 · Status: **As-built draft — review pending**

Proposed responsible function: Security / Product. No named assignment or approval is implied.

## Implemented roles
| Action | Viewer | Manager | Admin |
|---|---|---|---|
| Read overview, patterns, agent, department and CRM reports | Yes, masked | Yes | Yes |
| Read call journey and provider health | Yes, masked | Yes | Yes |
| Change own password / sign out | Yes | Yes | Yes |
| CSV/XLSX export | No | Yes | Yes |
| Request/retry supported historical import | No | Yes | Yes |
| Request sync now | No | No | Yes |
| List/create/update staff | No | No | Yes |
| Create/end department mapping | No | No | Yes |
| Inspect audit/quarantine/raw-event administrative endpoints | No | No | Yes |
| Play a recording | Unavailable | Endpoint returns unavailable | Endpoint returns unavailable |
| Mutate Acefone/LeadSquared records | Not implemented | Not implemented | Not implemented |

## Enforced rules
Authorization is checked in the backend. Hidden buttons are not a permission boundary. Viewer responses mask caller/DID numbers and selected agent-number evidence, and replace lead display names with Restricted lead. This is masking, not anonymization: aggregate counts, last digits and staff-related fields may remain visible. No field-level privacy certification is implied.

The last active administrator cannot be disabled/demoted through the account API. Account role/access/password updates revoke sessions. Password change revokes other sessions. Named accounts have mandatory first-password replacement, and the login form cannot grant a different role.

## Scope and gaps
There is no department-restricted row-level authorization, tenant partitioning, SSO/MFA or formal break-glass workflow. The app's Admin account does not grant OS, Render or Neon access. Manual username/display-name changes have been operational actions; the current staff-edit API supports role, active flag and password, not username editing.

---
Evidence: backend/app/auth.py; backend/app/accounts.py; backend/app/reports.py; backend/app/api.py. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
