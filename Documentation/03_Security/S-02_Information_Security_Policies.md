# S-02 — Information Security Policies

Baseline: 2026-10-30 · Status: **Proposed policy — approval pending**

Proposed responsible function: Security / Business owner. No named assignment or approval is implied.

## Proposed operating policy
Assign individual accounts and the minimum app role needed. Do not share administrative passwords. Use OS/hosting account protections and MFA where those providers support it; TWSS IVR has no integrated SSO/MFA. Review access at staff movement and on a proposed quarterly schedule. These organizational controls need approval and operational evidence; they are not automatically enforced by this document.

## Implemented authentication controls
New internal passwords are 12–256 characters. scrypt uses a per-password random salt and constant-time comparison. Five failed attempts lock a known account for fifteen minutes. Sessions expire after one hour; temporary-password users cannot access reports until changing it. Staff role/access/password changes revoke sessions. No credentials belong in chat, repository, exported documentation or frontend bundles.

## Secrets and endpoints
Keep integration and hosting credentials in protected local files/service secrets. Use the exact approved HTTPS provider host, never an arbitrary customer-supplied base URL. Rotate a leaked secret at its issuer and update the private configuration; assess sessions/provider logs. Do not automatically print a connection string while diagnosing a database error.

## Evidence and approval
Record account grants, access reviews, secret rotation evidence and any exceptions. Encryption-at-rest claims require device/vendor evidence; file permissions alone are not encryption. Formal password rotation rules, ownership and vendor contractual controls are approval items. See C-04/C-07 and D-07 for incident/recovery handling.

---
Evidence: backend/app/passwords.py; backend/app/auth.py; backend/app/credentials.py. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
