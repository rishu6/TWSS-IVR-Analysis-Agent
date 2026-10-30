# P-01 — Business Requirements Document

Baseline: 2026-10-30 · Status: **As-built draft — review pending**

Proposed responsible function: Business owner / Product. No named assignment or approval is implied.

## Business purpose
TWSS IVR helps The WallStreet School understand incoming call demand, answered and missed calls, agent performance and whether callers already exist in LeadSquared. Founders and managers need understandable figures that can be traced back to calls. Acefone India is the telephony source. LeadSquared supplies CRM leads and user names. The application reads these services; it does not create CRM leads or place calls.

## Business outcomes and scope
| Requirement | Expected business result | Current delivery |
|---|---|---|
| BRD-01 | See incoming volume, answered/missed totals and department answer rate | Analysis dashboard |
| BRD-02 | Identify the busiest weekday and hour | Call patterns, weekday charts and heatmap |
| BRD-03 | Explain who answered and which agents were reported missed | Detailed flow and call drawer |
| BRD-04 | Compare staff outcomes without treating failover as a competitive agent | Answered/missed/best/worst views |
| BRD-05 | Check callers against existing leads | LeadSquared insights, all candidate leads retained |
| BRD-06 | Analyse past dates and departments independently per tab | IST date ranges and route-specific filters |
| BRD-07 | Restrict customer data and operational changes by role | Named accounts, Viewer masking, Admin/Manager permissions |
| BRD-08 | Recover previous call history and keep data across restarts | Resumable imports, Mac SQLite, cloud PostgreSQL |

## Acceptance examples
For the same date and scope, dashboard totals and the call list must reconcile. Sixteen answered calls must not be silently presented as thirteen merely because a department-only filter is enabled: the latter is a separately labelled subset. A department answer rate uses answered department calls in its numerator and all department calls in its denominator. A caller with two different matching leads must show both, without arbitrary selection. A missed agent is distinct from an unanswered customer call.

## Users, constraints and boundaries
Admin manages accounts and mappings. Managers analyse and export. Viewers inspect masked reports. Mac operation is the current working route; cloud service previously deployed to Render Free is blocked by Neon's exhausted monthly network-transfer allowance as of this document date. No paid hosting change is approved. Mac and cloud databases are independent after the original migration.

Not included: verified real-time provider live events, exact transfer-link reconstruction, recording playback, CRM call-activity creation, automated callbacks, SSO/MFA, sentiment analysis, transcription or AI recommendations. This document is a requirements baseline for review, not a signed business acceptance or legal certificate.

## Delivery and approval
Existing implementation and tests are evidence of functionality. Business acceptance, privacy approval, quota recovery and production availability targets remain separate decisions. See P-03 for functional criteria, P-09 for calculation rules, M-03 for risks and Q-02 for sign-off.

---
Evidence: README.md; backend/app/reports.py; frontend/src/main.tsx; docs/phase-status.md. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
