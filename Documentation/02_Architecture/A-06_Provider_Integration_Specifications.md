# A-06 — Provider Integration Specifications

Baseline: 2026-10-30 · Status: **As-built draft — review pending**

Proposed responsible function: Backend / Integrations. No named assignment or approval is implied.

## Verified client surface
| Provider | Implemented read-only request | Purpose | Boundary |
|---|---|---|---|
| Acefone India | GET https://api.acefone.in/v1/call/records | CDR pages with date range/direction | Provider data retention and exact flow completeness are not guaranteed |
| LeadSquared | POST /v2/LeadManagement.svc/Leads.Get | Default lead-type scan and Phone/Mobile criteria | Preserve all exact normalized candidates; custom object types unverified |
| LeadSquared | GET /v2/UserManagement.svc/Users.Get | Resolve owner IDs to names | Cache hourly; missing names stay unavailable |

## Authentication and transport
Acefone uses a bearer header. LeadSquared uses x-LSQ-AccessKey/x-LSQ-SecretKey on a trusted HTTPS tenant host. Credentials are loaded privately; redirects/proxy inheritance are disabled in the provider transport. The client uses timeouts, paced requests, bounded retries and capped Retry-After handling. Account-specific quota approval is still required; app pacing is not a provider SLA.

## Schema and pagination handling
CDRs use provider call_id, documented paging and restricted payload persistence. A repeated page signature or page limit prevents a false complete-history claim. Lead scans use one-based pages up to 1000 rows, a durable staging cursor and atomic promotion. Phone checks search both fields with LIKE suffix criteria, then accept only full normalized-number equality. Failed or incomplete searches do not establish no match.

## Documentation sources
[Acefone CDR](https://docs.acefone.in/reference/call-detail-records-2), [LeadSquared criteria search](https://apidocs.leadsquared.com/search-by-lead-criteria/), [LeadSquared users](https://apidocs.leadsquared.com/get-users/). These links identify implemented contracts; historical tenant connection evidence is in docs/account-validation.md and phase status. Do not invent endpoints or assert that public docs alone verify a tenant feature.

---
Evidence: backend/app/provider_clients.py; backend/app/live_sync.py; backend/app/owner_directory.py. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
