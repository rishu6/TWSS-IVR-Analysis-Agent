# P-08 — Reporting Content and Data Presentation Guide

Baseline: 2026-10-30 · Status: **As-built draft — review pending**

Proposed responsible function: Product / Data. No named assignment or approval is implied.

## Purpose
Replace the reference project's learning-content authoring rules with reporting rules relevant to TWSS IVR. Every caption should help a business reader understand the cohort and unit being counted.

## Presentation rules
| Concept | Preferred wording | Avoid |
|---|---|---|
| All answered customer calls | Answered calls | Answered legs when leg coverage is absent |
| Missed routed calls | Missed after department selection | Using every missed call as customer missed |
| CRM pending | Checking LeadSquared | No lead found before a successful check |
| Current owner | Resolved owner name or Owner name unavailable | Labelling a GUID as a person's name |
| Time | IST with date/hour where needed | Mixing UTC export timestamps with local display silently |
| No denominator | Unavailable / — | NaN, infinity or invented zero |

## Evidence and examples
Use synthetic caller IDs and fictional names in training material. Do not paste API tokens, signed recording URLs, staff passwords or tenant captures into documents. A department reporting label alone is insufficient to prove a Department event. The UI may use business-friendly wording, but technical specifications retain this limitation.

## Review checklist
Verify numerator and denominator; distinguish calls from unique callers; label any selected subset; preserve tied leaders; identify incomplete provider coverage; keep current-stage wording; confirm that screenshots represent the referenced release. For exports, state which columns and filters the actual route supports.

---
Evidence: backend/app/reports.py; backend/app/crm_analytics.py; frontend/src/LeadSquaredInsights.tsx. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
