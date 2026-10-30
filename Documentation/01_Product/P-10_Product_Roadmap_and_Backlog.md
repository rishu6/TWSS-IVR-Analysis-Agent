# P-10 — Product Roadmap and Backlog

Baseline: 2026-10-30 · Status: **As-built draft — review pending**

Proposed responsible function: Business owner / Engineering. No named assignment or approval is implied.

## Delivered baseline
Named-account local app; overview and weekly call-pattern visuals; detailed recorded flows; agent/department reports; CRM candidate matching and owner names; independent filters/page sizes; answered defaults and missed-department subsections; protected exports; historical imports; local backup/retention; Render/Neon deployment support.

## Prioritized follow-up
| Priority | Work | Exit condition |
|---|---|---|
| P0 | Restore cloud database access after transfer suspension | Database accepts connections and reports/accounts verified |
| P0 | Deploy/read-measure the traffic reductions already in source | Active-tab-only reads and unchanged-CRM skips verified in cloud |
| P1 | Generic export parity with department_selected scopes | Exported cohort reconciles with the selected caller view |
| P1 | Off-device backups and PostgreSQL recovery drill | Recovery evidence and approved storage destination |
| P1 | Automated quota monitoring and operational ownership | Alert route and response owner tested |
| P1 | Full accessibility/security/load assessment | Findings tracked and accepted/remediated |
| P2 | Incremental CRM refresh and quota-aware aggregation | Demonstrated freshness with measured lower data transfer |
| P2 | Deployment automation and staging | Authorized CI workflow and reviewed release process |

## Capability-gated work
Exact transfer reconstruction, authenticated webhooks, recording playback and custom CRM object coverage require verified contracts/tenant evidence before implementation. SSO/MFA and department-scoped access need an approved identity model. AI/audio analysis is not a current feature; see L-01. No delivery dates, paid resources or owners are committed by this roadmap alone.

---
Evidence: docs/phase-status.md; backend/app/api.py; scripts/render_service.py. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
