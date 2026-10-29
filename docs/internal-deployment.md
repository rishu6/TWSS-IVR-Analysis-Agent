# Internal Mac installation

Target chosen by the user: run on this Mac, with individual password accounts and Local Admin. This installation is separate from the synthetic demo.

## Start and sign in

```bash
.venv/bin/python scripts/internal.py
```

Open **http://localhost:8001**. Username: **localadmin**. The initial temporary password is in **`.runtime/first-login.txt`**, readable only by the Mac owner. Do not send it to chat. First sign-in requires a new password of at least 12 characters before any customer data is accessible. Delete the temporary-password file after successful setup.

The start command runs Alembic migrations, preserves existing accounts, acquires a single-process lock, serves the production frontend build and starts read-only synchronization. It does not seed demo records. The private SQLite database is `.runtime/internal.db`; `.runtime/` is excluded from Git. No API credentials are stored in that database or frontend assets. Provider recording URLs are stripped before raw payload persistence.

Only loopback is bound. This version is usable on this Mac; it is not published to the internet or available on other staff devices. For shared access, choose a hostname/server and configure HTTPS before changing the binding. Internal mode rejects plain HTTP origins outside localhost and requires Secure cookies on HTTPS. No domain, firewall, DNS, VPN or public hosting change was made.

## Staff and mappings

Admin → Staff accounts creates individual Admin, Manager or Viewer accounts. New users must change their temporary password. Admin can change roles or disable accounts; changes revoke active sessions. The last active administrator cannot be disabled or demoted. Five failed password attempts lock an account for 15 minutes; HTTP login rate limits also apply. Sessions expire after one hour. No self-registration or role selection is available in internal mode.

Admin → Department mappings assigns a DID or exact provider department name to an internal department, effective from a chosen timestamp in IST. Ending a mapping preserves its prior interval. Attribution changes immediately apply to matching stored calls and subsequent reconciliations; provider routing is never modified. Overlapping mappings are rejected.

Forgotten password recovery is an offline Mac-owner action:

```bash
.venv/bin/python scripts/reset_internal_password.py
```

The script asks for username and a hidden temporary password, revokes sessions and requires a password change on the next login.

## Real integrations and correctness limits

- Acefone: official `GET https://api.acefone.in/v1/call/records`, found through its official documentation index and verified with the saved account token (HTTP 200). Query parameters are documented from_date, to_date, page and limit. Initial history defaults to three days, then a daily overlap reconciles delayed records. Source timezone is explicitly configured as Asia/Kolkata; epoch timestamps take precedence. Verify portal timezone if date-based fallback warnings appear.
- CDR `call_id` is the identity boundary. No calls merge by phone/time. Repeated records are deduplicated and changed CDR snapshots preserve restricted history. Unknown/unparseable caller or DID values remain null with explicit warnings; identified calls are preserved. Records with unsupported direction or conflicting root identity are quarantined and keep health PARTIAL; they are not silently counted as missed or answered.
- Exact ring-attempt counts, leg IDs and transfer linkage are not established by the verified contract. The tenant does supply Agent dial/answer events and missed_agents names/numbers; Detailed Call Flow shows that evidence, with missed-agent summary timestamps explicitly unavailable. Attempt metrics remain unavailable. Final-answer calls can be attributed using the documented agent_name; this is not a count of answered legs. First response and talk metrics remain unavailable without timestamp/leg evidence. Portal call_flow entries are shown without inventing transitions.
- LeadSquared: documented read-only `POST /v2/LeadManagement.svc/Leads.Get` enumerates Phone/Mobile candidates using 1-based pages of 1000. The verified initial default-scope index contains 206,156 leads. Pages are durably staged and resume across interruption, then atomically promoted to the phone index. During the initial scan, CRM lookup is PENDING; the app never asserts a unique match from an incomplete index. Every distinct matching lead in the default LeadSquared lead-type scope is preserved; custom object types remain unverified and are explicitly labelled outside this scope. The scan is best effort against a changing remote dataset, not a transactional provider snapshot.
- A completed CRM index refreshes approximately every 15 minutes, in bounded resumable batches. Previous complete data remains available during refresh. Stage/owner are current only. Owner IDs resolve to names using the documented LeadSquared user directory, cached locally and refreshed hourly; unresolved names are labelled unavailable.
- Provider transport uses fixed official hosts, HTTPS headers, disabled redirects/proxy inheritance, timeouts, conservative pacing, bounded retry and capped Retry-After handling. It never creates leads, places calls or changes provider configuration.
- Webhooks and recording playback stay disabled until authentication, delivery linkage, URL access/expiry and retention are verified. The live-call page does not claim real-time provider connectivity; this release is CDR polling.

## Freshness, backup and retention

Admin displays provider state, last success, scan progress and partial/quarantined record counts. Call polling runs every minute; an ongoing CRM index continues in bounded batches. A sync lock prevents concurrent jobs. A separate system health entry reports configuration/maintenance failures.

Every successful maintenance cycle creates one private, integrity-checked SQLite backup per UTC day under `.runtime/backups/`; automatic backups older than seven days expire. Take an additional manual backup before upgrades:

```bash
.venv/bin/python scripts/backup_internal.py
```

Raw integration payloads expire after 90 days. Call-event identity, ordering, dedupe hash and derived journeys remain; expired raw call-event payloads are cleared. Expired sessions/tickets are removed. This local retention policy is implemented in `app/maintenance.py`; adapt it to the organization's approved policy before broader deployment. Database backups contain customer data and need the same protection as the source database.

For restore: stop the app, copy the current database to a separate recovery file, restore a chosen backup into `.runtime/internal.db`, run `PRAGMA integrity_check` and foreign-key checks, then restart. Never restore over a running SQLite connection. A clean-database backup/restore test is automated; an additional private live-backup restore check is recorded in phase status. Backups on the same Mac are not off-device disaster recovery.

## Publication boundary

This is a local authenticated installation with live read-only account access. Shared hosting, HTTPS certificate issuance, corporate SSO/MFA, external penetration testing and representative production load certification remain separate deployment work. Do not describe those as completed. PostgreSQL/Redis/Celery Compose definitions remain available for a future server rollout; this Mac installation intentionally uses one application process and SQLite.

## Detailed Call Flow and older dates

Open **http://localhost:8001/flows** or use the Detailed Call Flow sidebar item. All Calls, Answered and Missed tabs use the same search, participant, department and lead filters. Expand a row for the full supplied flow and participant evidence; use the arrow for the CRM/detail drawer.

The calendar controls filter already-stored records. Admin/Manager can additionally choose **Import selected dates from Acefone** to fetch missing dates within the last 90 days. Imported calendar days use Asia/Kolkata boundaries, with the current day clamped to request time. Each page and direction checkpoint is saved. Queued/running/completed/failed states and processed/rejected counts are visible; failed jobs can be resumed. Empty filtered results do not assert that the provider had no calls.

An initial 30-calendar-day import completed with 1,727 unique calls and zero rejected records. Coverage expands only after successful import. Records older than the supported live window require a separately verified archive import; no undocumented archive API is used.
