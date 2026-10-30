# A-04 — API Specification and Standards

Baseline: 2026-10-30 · Status: **As-built draft — review pending**

Proposed responsible function: Backend engineering. No named assignment or approval is implied.

## Contract source
The endpoint catalogue below is generated from the current FastAPI route graph. [OpenAPI JSON](A-04_OpenAPI.json) contains request/response schema details. The exported file adds documentation annotations for cookie authentication and the middleware CSRF header; it does not enable public /docs or change runtime authorization. The source application intentionally disables interactive API docs routes.

## Request conventions
Most business routes require an authenticated session cookie. Every write request needs x-csrf-protection: 1; supplied browser Origin must match the configured exact origin. Sessions last one hour. Common errors are JSON detail with 401 unauthenticated, 403 forbidden/CSRF/temporary-password restriction, 404 unavailable resource, 409 conflict, 422 validation and 429 request limit. Quota/startup failures may prevent an HTTP application response entirely.

List pagination is one-based. Common page_size is bounded to 100 and show_all is explicit. Dates in filter URLs are timezone-aware start-inclusive/end-exclusive instants. UI calendars translate IST days to UTC boundaries. CSV/XLSX exports carry UTC timestamps.

## Scope caveats
Generic exports contain eight call-detail columns, not the full CRM analytics report. missed_department is explicitly handled in exports; department_selected used by CRM/answer-rate drilldowns is not explicitly implemented by the generic export route. Track parity as an open defect rather than claiming all screens export identical cohorts. Recording requests return unavailable. Demo mutation endpoints are disabled outside demo mode.

## Endpoint catalogue
| Method | Path | Permission / mode | Source |
|---|---|---|---|
| GET | `/healthz` | Public | `backend/app/main.py` |
| POST | `/api/v1/auth/login` | Public | `backend/app/auth.py` |
| GET | `/api/v1/auth/configuration` | Public | `backend/app/auth.py` |
| GET | `/api/v1/auth/me` | Authenticated staff | `backend/app/auth.py` |
| POST | `/api/v1/auth/change-password` | Authenticated staff | `backend/app/auth.py` |
| POST | `/api/v1/auth/logout` | Authenticated staff | `backend/app/auth.py` |
| POST | `/api/v1/admin/sync` | Admin | `backend/app/api.py` |
| GET | `/api/v1/filter-options` | Authenticated staff | `backend/app/api.py` |
| GET | `/api/v1/metrics/overview` | Authenticated staff | `backend/app/api.py` |
| GET | `/api/v1/reports/leadsquared` | Authenticated staff | `backend/app/api.py` |
| GET | `/api/v1/calls` | Authenticated staff | `backend/app/api.py` |
| GET | `/api/v1/calls-summary` | Authenticated staff | `backend/app/api.py` |
| GET | `/api/v1/calls/{id}` | Authenticated staff | `backend/app/api.py` |
| GET | `/api/v1/calls/{id}/journey` | Authenticated staff | `backend/app/api.py` |
| GET | `/api/v1/calls/{id}/crm` | Authenticated staff | `backend/app/api.py` |
| GET | `/api/v1/calls/{id}/recording` | Admin, Manager; unavailable (404) | `backend/app/api.py` |
| GET | `/api/v1/reports/agents` | Authenticated staff | `backend/app/api.py` |
| GET | `/api/v1/reports/departments` | Authenticated staff | `backend/app/api.py` |
| GET | `/api/v1/reports/missed-calls` | Authenticated staff | `backend/app/api.py` |
| GET | `/api/v1/reports/exports` | Admin, Manager | `backend/app/api.py` |
| GET | `/api/v1/integrations/status` | Authenticated staff | `backend/app/api.py` |
| POST | `/api/v1/demo/events` | Admin; demo mode only | `backend/app/api.py` |
| POST | `/api/v1/demo/retry-crm` | Admin, Manager; demo mode only | `backend/app/api.py` |
| POST | `/api/v1/webhooks/acefone` | Admin; disabled (503) | `backend/app/api.py` |
| GET | `/api/v1/admin/raw-events` | Admin | `backend/app/api.py` |
| GET | `/api/v1/admin/import-issues` | Admin | `backend/app/api.py` |
| GET | `/api/v1/admin/audit` | Admin | `backend/app/api.py` |
| POST | `/api/v1/live-token` | Authenticated staff | `backend/app/api.py` |
| GET | `/api/v1/admin/users` | Admin | `backend/app/accounts.py` |
| POST | `/api/v1/admin/users` | Admin | `backend/app/accounts.py` |
| PATCH | `/api/v1/admin/users/{id}` | Admin | `backend/app/accounts.py` |
| GET | `/api/v1/admin/department-mappings` | Admin | `backend/app/mappings.py` |
| POST | `/api/v1/admin/department-mappings` | Admin | `backend/app/mappings.py` |
| POST | `/api/v1/admin/department-mappings/{id}/end` | Admin | `backend/app/mappings.py` |
| POST | `/api/v1/history/import` | Admin, Manager | `backend/app/history.py` |
| GET | `/api/v1/history/imports` | Authenticated staff | `backend/app/history.py` |
| POST | `/api/v1/history/imports/{id}/retry` | Admin, Manager | `backend/app/history.py` |
| GET | `/api/v1/integrations/health` | Authenticated staff | `backend/app/main.py` |
| GET | `/api/v1/admin` | Admin | `backend/app/main.py` |

## WebSocket
/api/v1/live uses a one-use live ticket from /api/v1/live-token, sent as the first frame, bound to the cookie session. It emits invalidation messages, not provider call events. Internal UI now relies on normal report polling instead of subscribing to the demo's repeated invalidations.

---
Evidence: backend/app/main.py; backend/app/api.py; backend/app/auth.py; backend/app/accounts.py; backend/app/history.py. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
