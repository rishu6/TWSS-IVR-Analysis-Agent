# VS Code Agent Development Prompt — Acefone + LeadSquared Real-Time Dashboard

You are a senior full-stack engineer, integration architect, and QA engineer. Build a production-oriented internal analytics web application integrating Acefone telephony and LeadSquared CRM.

## Primary objective
Track every inbound customer call as ONE logical call, preserving all underlying call legs, IVR steps, department routing, ring attempts, transfers, answer events, termination and recording metadata. Show every agent who failed to answer before the agent who answered. Join callers to LeadSquared records and show lead creation date, current stage, owner, source and historical snapshot when possible. Deliver an internal dashboard with searchable call journeys and accurate agent/department reporting.

## Important constraint: do not invent provider capabilities
First inspect the actual Acefone and LeadSquared API documentation supplied to the project. Create `docs/integration-capability-matrix.md` listing verified endpoints, authentication methods, request/response examples, pagination, rate limits, webhook payloads, call ID/leg ID semantics, timestamps, recordings and agent-ring event availability. Mark unsupported or unverified features explicitly. Implement adapters against documented endpoints only. Never fabricate API paths or response fields. If Acefone does not expose per-agent ring attempts, show 'unavailable from provider' rather than guessing.

## Tech stack
- Frontend: React, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query, Recharts; accessible responsive UI.
- Backend: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic.
- Database: PostgreSQL; Redis and Celery for async sync/reconciliation jobs.
- Live updates: backend WebSocket authenticated with short-lived tokens, with graceful polling fallback.
- Deployment: Docker Compose for local development; Nginx or secure reverse proxy, HTTPS for production.
- Testing: pytest, httpx, Playwright/Vitest as appropriate.

## Functional requirements
1. Dashboard overview: total logical inbound calls, answered, customer-level missed, IVR-only, abandoned, in progress, answer rate, first response time, duration, hourly trend, by DID and department.
2. Call journey explorer: chronological events for inbound, IVR prompt, DTMF press, queue, department, agent ringing, no-answer, agent answer, hold, transfer, disconnect, recording. Search by caller, call ID, DID, agent, date, department, lead stage, lead owner.
3. Agent performance: ring attempts, missed ring attempts, answered legs, talk time, response time, transfers. Do not equate agent missed attempts to missed customer calls.
4. Department reporting: configurable mapping from provider queues/IVR nodes/DIDs to departments; document how cross-department transfers affect attribution.
5. LeadSquared: normalize phone numbers using a tested phone library, query supported lead lookup API, store all candidate matches, display lead ID, name, created timestamp, current stage, current owner, source and latest sync. Separate 'first-time caller' from 'new CRM lead'; report multiple matches and lookup errors. Do not create leads without an explicit feature flag and approval.
6. Missed call recovery: track whether a subsequent connected call or outbound callback recovered the missed call; define configurable matching windows and avoid false positives.
7. Recording: show a permission-controlled link or proxy only if provided by the provider, with retention and access logging.
8. Exports: role-controlled CSV/XLSX of filtered reports, using server-side pagination for large datasets.
9. Admin: manage agents, department mappings, DID mappings, roles, integrations health and sync status. Never expose secrets.

## Data model (design migrations with proper keys, indexes and constraints)
- calls: id, provider, parent_provider_call_id, caller_e164, dialed_did, direction, started_at, answered_at, ended_at, final_status, primary_department_id, answering_agent_id, recording_status, ingestion_status.
- call_legs: id, call_id, provider_leg_id, agent_id, department_id, ring_started_at, answered_at, ended_at, disposition, transfer_parent_leg_id.
- call_events: id, call_id, provider_event_id, event_type, event_at, received_at, raw_payload_ref, sequence_hint, dedupe_hash.
- ivr_events: id, call_id, node_id, node_name, dtmf_key, entered_at, exited_at, destination.
- agents: id, provider_agent_id, name, active; departments: id, name; agent_department_memberships: agent_id, department_id, effective_from, effective_to.
- did_department_mappings: did, department_id, effective_from, effective_to.
- call_transfers: id, call_id, source_leg_id, target_leg_id, from_department_id, to_department_id, occurred_at.
- leads: id, provider_lead_id, display_name, created_at, current_stage, current_owner_id, source, last_synced_at.
- lead_owners: id, provider_owner_id, display_name.
- lead_phone_numbers: id, lead_id, normalized_number, raw_number, phone_type.
- call_lead_matches: call_id, lead_id, match_method, match_status, matched_at, lead_stage_at_call, lead_owner_at_call, snapshot_source.
- recordings: id, call_id, provider_recording_id, secure_url_reference, available_at, retention_until.
- integration_events: id, provider, external_event_id, payload, received_at, processed_at, processing_status, error_message.
- sync_jobs: id, provider, job_type, cursor, started_at, completed_at, status, error.
- users, roles, permissions, audit_logs.
Use UTC timestamptz for persistence and Asia/Kolkata for user-facing display. Encrypt sensitive data at rest where feasible. Do not store raw API secrets in the database.

## Data correctness and event processing
- Treat a logical customer call as distinct from its agent-level attempts/legs. Correlate via documented parent call ID, linked leg IDs or verified provider linkage; never merge solely by phone number and time.
- Accept out-of-order, duplicate and delayed webhook events; use idempotency constraints and deterministic reducers.
- Keep original raw payloads and derived normalized events for debugging, with restricted access and retention.
- Support backfill and scheduled reconciliation against provider history. Record last successful sync and show data freshness in UI.
- Model statuses as IN_PROGRESS, ANSWERED, MISSED, ABANDONED, IVR_ONLY, UNKNOWN; derive them from documented evidence and configurable policy. Do not mark an agent-level ring miss as a missed customer call.
- Record provider timestamps, receipt timestamps and normalized UTC timestamps; test timezone offsets and clock skew.
- Preserve lead stage/owner snapshots only when verifiably available; otherwise mark 'current only' instead of claiming historical accuracy.
- Use explicit handling for CRM duplicates, transient errors, API rate limits, pagination, phone formats and invalid numbers.

## API and integration design
Create `AcefoneClient` and `LeadSquaredClient` behind interfaces. Populate real endpoints from user-supplied docs. Implement request timeouts, bounded exponential backoff, rate limiting, structured logs with PII redaction, and health checks. Verify webhook signatures or equivalent documented authentication. Prefer webhooks for low latency; use polling when necessary and show sync delay. Never expose credentials in frontend code. Use `.env.example` with placeholders only.

## Backend endpoints (internal, not vendor endpoints)
- GET /api/v1/metrics/overview
- GET /api/v1/calls (filter, cursor/pagination)
- GET /api/v1/calls/{id}
- GET /api/v1/calls/{id}/journey
- GET /api/v1/calls/{id}/crm
- GET /api/v1/reports/agents
- GET /api/v1/reports/departments
- GET /api/v1/reports/missed-calls
- GET /api/v1/reports/exports
- GET /api/v1/integrations/health
- POST /api/v1/webhooks/acefone (subject to docs)
- WS /api/v1/live
Secure all except verified webhook intake with appropriate authentication, authorization and rate limits.

## UI design
Professional internal BI dashboard, clean typography, dark/light support, responsive layouts. Sidebar: Overview, Live Calls, Call Explorer, Agent Analytics, Departments, LeadSquared Insights, Missed Call Recovery, Exports, Admin. Provide date range, department, agent, DID, outcome, stage and owner filters. Every KPI should have a tooltip defining its denominator and attribution. Detailed call drawer shows vertical timestamped call journey, all agents attempted, final answer agent, CRM lead details, provider IDs and recording controls. Clearly label stale, partial, unknown or unavailable data.

## Security
Internal login with SSO/OIDC if available, otherwise secure sessions and MFA-ready design; roles Admin, Manager, Viewer. Enforce authorization server-side for every report and recording. Store secrets in environment/secret manager; use HTTPS, audit logs, session expiry, CSRF protection where applicable, safe CORS, PII masking for general viewers and data retention rules. Protect recordings and customer numbers.

## Phased development and acceptance gates
Phase 1: Inspect docs, capability matrix, example payloads, edge-case fixtures, mapping of parent/leg IDs. Stop and ask for missing docs when essential.
Phase 2: Scaffold repo, Docker, migrations, auth, seed/demo data, CI checks.
Phase 3: Acefone adapter, webhook intake, historical backfill, idempotent event storage, reconciliation.
Phase 4: Deterministic call correlation and IVR/agent journey, unit tests for multi-agent attempts, transfers and out-of-order events.
Phase 5: LeadSquared lookup, phone normalization, lead ownership/stage enrichment, duplicate handling, snapshots.
Phase 6: React dashboard, real-time updates, agent and department reports, drill-down, export.
Phase 7: Missed-call recovery, recording permissions, operational monitoring and hardening.
Phase 8: Production readiness: load tests, security review, backup/restore drill, observability and deployment documentation.

## Mandatory acceptance tests
A. Three agents do not answer and a fourth answers: one logical call, final ANSWERED, three missed agent attempts, one answered agent leg, zero customer-level missed calls.
B. Customer disconnects in IVR: one IVR_ONLY or ABANDONED call according to documented business rules; no invented missed agent attempts.
C. One call transfers between departments: one logical call; preserve all legs and both departments, with documented attribution.
D. Duplicate and out-of-order webhooks do not inflate totals.
E. Same phone number on two leads produces MULTIPLE_MATCHES, not an arbitrary lead.
F. LeadSquared unavailable: telephony data still works; CRM status shows lookup pending/error and retries.
G. No ring-level events from Acefone: show 'agent attempts unavailable' rather than fake names.
H. A historical record with a provider timestamp offset displays correctly in Asia/Kolkata.
I. Viewer cannot access secrets, unauthorized recordings or admin endpoints.
J. Reconciliation updates stale calls without losing event history.

## Working instructions for the coding agent
1. First show a concise plan and inspect available API docs; identify unknowns.
2. Create a monorepo with `/backend`, `/frontend`, `/infra`, `/docs`, `/tests`.
3. Implement one phase at a time with runnable code, migrations, tests and a short README.
4. Build a mock Acefone/LeadSquared adapter using synthetic fixtures so the UI works before credentials are supplied; label demo data.
5. Never claim a real-time integration works until it has been verified against sandbox/production-safe provider APIs.
6. After each phase, report completed work, tests run, blockers and next actions.
7. Do not request that secrets be pasted into chat or committed to Git; use local environment variables.

## Initial task
Begin with Phase 1. Ask me to attach the Acefone and LeadSquared API documentation, inspect it, produce a verified capability matrix and propose exact event mappings. In parallel, scaffold a demo-only version with synthetic calls demonstrating the four-agent journey and CRM matching. Do not guess undocumented endpoints.
