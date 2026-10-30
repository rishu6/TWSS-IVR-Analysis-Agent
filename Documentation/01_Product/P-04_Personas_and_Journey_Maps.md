# P-04 — Personas and Journey Maps

Baseline: 2026-10-30 · Status: **As-built draft — review pending**

Proposed responsible function: Product / Operations. No named assignment or approval is implied.

## Personas
| Persona | Goal | Need / constraint | App role |
|---|---|---|---|
| Founder / business reviewer | Understand demand and service gaps | Plain language, correct denominator, current filters visible | Manager or Viewer by access decision |
| Operations manager | Review missed callers and staffing patterns | Week/hour comparison, call evidence and date range | Manager |
| Administrator | Maintain access and investigate sync failures | Staff management, mappings, provider state and audit | Admin |
| Read-only analyst | Review aggregate performance safely | Masked numbers and restricted lead names | Viewer |

## Founder journey
Select dates → review incoming/answered/missed KPIs → inspect department answer rate → examine busiest day/hour → drill into missed department calls → inspect lead stage and owner → export permitted call details. Confusion points include mixing agent misses with customer misses, mixing unique callers with call counts, and reading a current CRM stage as a historical one.

## Operations journey
Choose a week or historical day → select department/status → inspect the caller cohort → open a timeline → review agent evidence → identify follow-up work outside the app. No automatic callback or CRM mutation is implied.

## Admin journey
Create a named account → staff changes first password → allocate least privilege → check provider health → investigate an incomplete import or quota → take a protected backup before changes → verify recovery. Formal support roles and escalation contacts require assignment by TWSS; account role alone is not incident ownership.

---
Evidence: frontend/src/InternalLogin.tsx; frontend/src/AnalysisDashboard.tsx; frontend/src/LeadSquaredInsights.tsx. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
