# P-09 — Business Rules Specification

Baseline: 2026-10-30 · Status: **As-built draft — review pending**

Proposed responsible function: Product / Data / Engineering. No named assignment or approval is implied.

## Call identity and routing
BR-01: One logical call is identified by provider plus call_id; never merge by caller phone and nearby time. BR-02: Unknown caller/DID values do not erase an otherwise identified call. Conflicting root identities and unsupported directions are quarantined. BR-03: For real CDRs, department selection means a named Department event in the retained flow. A DID mapping/reporting label or DTMF digit alone is not enough.

## KPI definitions
| Metric | Rule |
|---|---|
| Inbound calls | Filtered logical calls whose direction is inbound |
| Answered / total missed | Respective final call outcome, not sums of agent events |
| Customer missed | MISSED inbound calls with recorded department routing |
| Department answer rate | ANSWERED inbound department calls / all inbound department calls |
| Overall answer rate | All ANSWERED inbound calls / all inbound calls, separately available in the API |
| Unique callers | Distinct known normalized caller numbers in scope |
| Repeat calls in CRM report | Additional calls per known number after its first selected call |

Zero department calls return null for the department rate. Synthetic illustration: 9 answered among 12 department calls gives 75%; answered calls without department evidence are excluded from both sides.

## Agent and CRM rules
Agent answered/missed counts use distinct calls per agent. One agent can miss and later answer the same call; the two ratios can overlap. Recorded dial positions do not prove exact provider ring-attempt coverage. Best/worst ranking excludes Support calls and the configured Vadant/Vadat/Vadnt failover name variants. Best is highest answered-call count; worst is highest reported missed-call count. Ties are shown.

Phone/Mobile are normalized, and all distinct matching lead IDs are retained. A positive cache match can be shown before a per-call projection refresh. Failed/incomplete searches do not establish absence. Lead creation is compared with the caller's first selected call; creation after a call does not prove causation. Stage and owner are current saved values, not historical snapshots.

## Date, scope and peak rules
IST calendar ranges are start-inclusive/end-exclusive. CRM defaults to all answered calls; department filtering is optional. Missed subsection counts are calculated before pagination. Weekly patterns aggregate incoming calls with known start times by IST weekday/hour, preserving ties. Filtering dates does not import missing provider history.

---
Evidence: backend/app/cdr.py; backend/app/reports.py; backend/app/agent_outcomes.py; backend/app/crm_analytics.py; frontend/src/callPatternsModel.ts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
