# Operations and production gates

## Local data lifecycle

Alembic creates the foundation schema. The seed command replays synthetic events idempotently and enriches fixtures; it intentionally simulates one CRM outage. The UI's **Simulate CRM recovery** action switches those lookups to successful synthetic results. This never contacts LeadSquared.

Celery beat schedules the synthetic reconciliation task every 60 seconds in Compose. The task replays fixture history, keeps original events and retries eligible CRM errors, at most five attempts with a capped backoff. Its runtime requires Redis/PostgreSQL and has not been exercised in this environment. Local zero-service mode does not require a worker; the frontend polls every 30 seconds and API tests exercise backfill/reconciliation directly.

`/api/v1/demo/events` is an Admin-only internal synthetic intake, requires CSRF header and rejects non-demo root IDs. It is not a vendor webhook. `/api/v1/webhooks/acefone` always returns 503 to authenticated Admins and accepts no provider events. Live adapters refuse construction. APP_MODE other than demo aborts startup.

WebSocket connections authenticate with a 30-second one-use ticket in the first frame plus the existing session cookie. No ticket appears in query strings. Connections send invalidations only, check session expiry each cycle, and close after about one minute; the UI falls back to polling. It does not claim live provider connectivity.

Database SyncJob records expose last successful replay. Admin raw-event access and exports are audited. Uvicorn access logging is disabled in run commands to avoid PII-bearing filter query logs. Nginx access logging should also be disabled or redacted before any real data is used. Do not log request bodies, credentials or raw provider responses in ordinary logs.

## Storage and schema limits

The migration uses timezone-aware DateTime (TIMESTAMPTZ on PostgreSQL), foreign keys, provider/event and provider/call uniqueness and lookup indexes. SQLite stores UTC values without an offset; the boundary explicitly normalizes incoming timestamps before persistence. Original timestamp strings remain in restricted payload history. Only synthetic JSON is stored unencrypted locally.

Calls/events/legs/leads/phones/matches/sync/integration/session/ticket/audit tables are implemented. IVR/transfer evidence currently lives in immutable events and projections. Effective-dated agent memberships, DID/queue mappings, normalized owners, recording records and production users/roles/permissions need additional migrations and management UI. Do not interpret the demo schema as completion of the full requested model.

Report filtering/pagination uses SQL, and exports fetch calls in chunks of 250. Overview/report aggregation currently materializes the filtered demo set. XLSX workbook output is buffered in memory. These need volume testing, keyset pagination, snapshot-consistent export jobs and streaming/object storage for large production datasets. Process-local HTTP rate limits are suitable only for this local prototype; WebSocket admission and distributed quotas need hardening.

## Production work still required

1. Obtain and validate India tenant API contracts, webhook authentication, root/leg IDs, per-agent coverage and history pagination. Capture redacted real fixtures and contract-test sandbox adapters with timeouts, quota handling, jittered bounded retry, Retry-After handling and reconciliation checkpoints. Do not enable generic guessed endpoints.
2. Validate all LeadSquared Phone/Mobile formats/object types and enumerate every page of candidate results; preserve lookup errors and ambiguity. Validate historical stage/owner evidence separately. Keep lead creation disabled; adding it requires a feature flag and explicit approval.
3. Replace selectable demo roles with OIDC/SSO or secure production identity and MFA, user provisioning, session revocation and permissions. Require HTTPS, Secure cookies and exact production origin. Audit all sensitive access, apply distributed rate limits and review WebSocket resource limits.
4. Configure managed PostgreSQL encrypted storage and backups; secrets manager and key rotation; raw payload/recording retention, purge and access policies. Verify provider-supplied recording URLs and retention before implementing controlled playback.
5. Test PostgreSQL migrations, concurrent duplicate/out-of-order writes, Redis/Celery retries and failure recovery in a disposable environment. Add telemetry, PII-redacted structured logs, dead-letter handling, sync freshness alerts and capacity limits.
6. Run a representative load test, dependency audit and security review. CI definitions alone do not certify production readiness.

## Backup / restore drill (not yet performed)

Use an isolated PostgreSQL destination. Take an encrypted `pg_dump` custom-format backup, restore with `pg_restore` into the isolated database, then verify schema revision, call/event/leg counts, referential integrity and API results A–J. Confirm no production jobs or webhooks can target the restored environment. Record elapsed recovery time, backup age, RPO/RTO and application replay behavior before signing off. No backup or restore operation has been run by this implementation.

## Current verification limits

Local checks use Python 3.14 and SQLite. CI targets Python 3.12. Docker is not installed here; Compose/Nginx/PostgreSQL/Redis/Celery startup and HTTPS are unverified. Live vendor transport, production scale, identity, provider recordings and retention remain unverified or unimplemented as identified above.
