# P-11 — Glossary

Baseline: 2026-10-30 · Status: **As-built draft — review pending**

Proposed responsible function: Product / Support. No named assignment or approval is implied.

| Term | Meaning in TWSS IVR |
|---|---|
| CDR | Provider call-detail/history record |
| Logical call | Deduplicated customer call identified by provider call ID |
| Call event | A retained provider-reported timeline item or snapshot |
| Department event | Named routing step; used for department-selection cohorts |
| Customer missed | Missed call after recorded department routing |
| Agent miss | Provider-reported missed involvement for a person; distinct from final call outcome |
| Final answerer | Agent evidenced/reported as answering the logical call |
| Failover destination | Designated fallback agent excluded from competitive best/worst ranking |
| Unique caller | One known normalized phone number, even if it called repeatedly |
| Repeat call | An additional selected call from a known caller |
| Candidate lead | A distinct CRM record whose normalized Phone/Mobile matches a caller |
| Current stage / owner | Latest saved CRM values, not a historical value at call time |
| Unresolved/checking | Matching has not established a complete result |
| No match in last check | A completed applicable check found no matching lead |
| CRM index | Saved default-lead-type Phone/Mobile directory |
| IST | Asia/Kolkata display and calendar timezone |
| UTC | Timestamp basis used in storage and generic exports |
| Egress / network transfer | Data sent from Neon to database clients; a Free allowance was exhausted |
| Session / live ticket | Cookie session backed by a token hash; short-lived one-use WebSocket ticket |
| As-built draft | Describes source evidence but is not a signed approval or certification |

---
Evidence: backend/app/domain.py; backend/app/crm.py; backend/app/db.py. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
