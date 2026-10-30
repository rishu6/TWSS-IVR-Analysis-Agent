# S-06 — Incident Response Plan

Baseline: 2026-10-30 · Status: **Proposed plan — approval pending**

Proposed responsible function: Operations / Security / Legal. No named assignment or approval is implied.

## Severity and first actions
Treat suspected account/provider-key exposure or customer-record disclosure as a high-priority security incident. Treat a database quota suspension as an availability incident unless there is separate evidence of compromise. Record IST/UTC timestamps, symptoms, scope, deployment version and owner. Preserve relevant evidence before deletion/rotation; never paste credentials into an incident ticket.

## Response sequence
1. Confirm health, deployment, database and provider status separately.
2. Contain the confirmed issue: revoke affected sessions/keys for compromise; stop an identified abusive workload for exhaustion.
3. Assess affected data, accounts, retention and business continuity.
4. Restore through a reviewed recovery path; validate login, role restrictions, counts and backups.
5. Record root cause, unresolved risks and follow-up actions.

## Reporting and responsibilities
Business/incident owner, engineering, infrastructure account owner and privacy/legal reviewer are proposed functions, not an established staffed rota. Applicable CERT-In and privacy notification duties must be assessed immediately by the responsible legal/security owner using the current official directions and commencement rules; do not wait for this draft's approval if a binding reporting duty applies. This document is not a legal determination of applicability or deadlines.

## Known incident
On 30 October, Neon rejected startup connections and its console confirmed monthly network-transfer exhaustion. The approved free-hosting preference remains. Mac operation is an independent fallback, not proof that cloud-only data is present locally. See D-07 and M-03.

---
Evidence: docs/phase-status.md; scripts/cloud.py; backend/app/auth.py. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
