# A-08 — Telephony and CRM Data Contracts

Baseline: 2026-10-30 · Status: **As-built draft — review pending**

Proposed responsible function: Integrations / Data. No named assignment or approval is implied.

## Why this replaces the reference document
The other project's payments/registration architecture is not applicable to TWSS IVR. This document instead records the boundaries between call capture, normalization, caller matching and reporting. No payment gateway, checkout, enrollment or registration integration is implemented.

## Contracts
| Boundary | Required identity / semantics | Incomplete evidence behaviour |
|---|---|---|
| CDR → call | Provider plus call_id; inbound/outbound; trustworthy timestamp inputs | Reject conflicting identity; retain unknown phone as null |
| Flow → department selection | Named Department event | Reporting label/mapping alone does not count as selection |
| Flow → agent outcome | Explicit answer/report-missed evidence and agent identity | Unknown attempt linkage remains unknown |
| Caller → CRM | Normalized full Phone/Mobile equality | Preserve multiple leads; pending/error is not no match |
| Owner ID → name | Current saved owner plus user directory | Unavailable name; no invented person |
| Lead date → call relationship | Lead CreatedOn vs first selected call | Unknown date remains unknown; no causal attribution |

## Contract evolution
Add redacted synthetic fixtures for a newly documented shape, retain provider identity semantics, version derived projection changes and test replay. Do not migrate real records using a guessed vendor field. Deletions/custom lead types, webhook signatures, exact transfer edges and recording access require separate verified contracts. Only the actual implemented provider client surface in A-06 is authorized by the current code.

---
Evidence: backend/app/cdr.py; backend/app/crm.py; backend/app/live_sync.py; docs/event-mapping.md. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
