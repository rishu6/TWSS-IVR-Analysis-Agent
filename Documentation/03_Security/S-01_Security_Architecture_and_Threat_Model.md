# S-01 — Security Architecture and Threat Model

Baseline: 2026-10-30 · Status: **As-built draft — review pending**

Proposed responsible function: Security / Engineering. No named assignment or approval is implied.

## Assets and boundaries
Protect provider credentials, staff passwords/session tokens, customer phone numbers, lead details, call evidence, exports and backups. Boundaries are staff browser → FastAPI → local/cloud database → provider APIs, plus Mac OS/hosting control planes. A Viewer is not trusted with an unmasked export; an app Admin is not automatically an infrastructure administrator.

## Threat and control review
| Threat | Current control | Remaining review |
|---|---|---|
| Role spoofing | Backend derives role from stored user/session | Penetration-test role/resource coverage |
| Session theft | Hashed token storage, HttpOnly/SameSite cookie, Secure on HTTPS | Device policies and MFA absent |
| CSRF | Explicit write header and configured-origin validation | Test real deployment origins after changes |
| Secret/recording URL leakage | Private files/env, fixed provider hosts, restricted payloads | Audit debug tools, logs and backups |
| Query abuse / injection | SQLAlchemy parameterization, escaped text search, bounded validation | Representative load and abuse tests |
| CSV formula execution | csv_safe prefixes risky leading characters | Validate downstream spreadsheet handling |
| Data overexposure | Viewer masking and export denial | No row-level department isolation |
| Resource exhaustion | Pacing/retries, request limits, reduced repeated reads | Actual quota suspension occurred; alerts/caching remain gaps |

## Residual risk and evidence
SQLite and local backups depend on device protection; application code does not encrypt these files itself. Audit rows are not an independently immutable/tamper-evident log. Provider raw payload controls and missing-evidence rules reduce accidental disclosure/misstatement but do not establish legal compliance. No external penetration-test report is available. Prioritize quota recovery, restore verification and scoped export parity before representing broad production readiness.

---
Evidence: backend/app/auth.py; backend/app/main.py; backend/app/provider_clients.py; backend/app/cdr.py; backend/app/api.py. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
