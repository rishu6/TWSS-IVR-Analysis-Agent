# Phase gates

## Current internal Mac milestone — 2026-10-28

User chose Mac-only operation, individual passwords and Local Admin. The authenticated installation is at **http://localhost:8001** with a separate private database. [Deployment and sign-in instructions](internal-deployment.md).

- Both account credentials passed actual read-only requests. Acefone's exact CDR API was located through its official documentation index and verified with HTTP 200. LeadSquared metadata and 1,000-row criteria-search pages were verified.
- Live CDR ingestion/reconciliation preserves call identity and revision history, flags unknown phone evidence, and exposes unavailable ring/leg metrics explicitly. Invalid identity/direction records are quarantined. Department mappings use effective intervals.
- CRM indexing is durable and resumes across restarts. The initial default-scope scan completed with 206,156 indexed leads. Subsequent interrupted refreshes resume from saved pages; the previous complete index stays available. Previous complete indexes remain usable during refresh. Stage/owner are current only, and all matching candidates remain visible.
- Named accounts replace selectable demo roles. First-login password changes are mandatory; server-side RBAC, account lockout, role-change session revocation and last-admin protection are tested. Admin manages staff and department attribution.
- Built frontend is served with the API. Real-mode filters derive from stored account data; the synthetic four-agent showcase is omitted.
- Daily private SQLite backups, 90-day raw-payload retention and expired-session cleanup are implemented. A private backup containing 192 calls and 80,000 staged CRM rows was restored to an isolated file and passed SQLite integrity and foreign-key checks; the running database was not overwritten.
- **64 backend tests passed**, including a 20,000-lead interrupted/resumed scan; **3 frontend tests**, TypeScript/Vite build and an internal-mode Chrome test of the built app passed. The earlier two demo browser tests remain separate evidence for demo mode.

This completes the implemented Mac-local installation, not shared publication or every original provider-dependent feature. Recording playback, exact per-agent attempts/transfer legs, authenticated provider webhooks, OIDC/MFA, shared HTTPS hosting and production load certification remain outside verified scope. The initial default-lead-type CRM scan and live enrichment completed. At verification there were 196 imported call records, including four preserved unknown-caller records; match outcomes included 159 single matches and two multiple-match calls. Custom object types remain outside the verified matching scope. No staff-network or internet deployment was performed.

## Original synthetic milestone — 2026-10-27

Date: 2026-10-27. The attached development brief is the specification; it is not provider API documentation. User confirmed India region and no tenant docs. No agent delegation or external publication was used.

| Phase | Implemented and checked | Status / remaining gate |
|---|---|---|
| 1 — documentation | Official public India webhook/token/portal guides and LeadSquared lookup/search/auth/limits reviewed; capability matrix and internal event mapping; 2 documentation tests | Public review complete; exact live mappings blocked by missing tenant payload/auth/linkage/CDR contracts. |
| 2 — foundation | Monorepo, Alembic migration, local sessions/RBAC/CSRF, demo seed, Compose and CI definitions; 3 foundation tests including migration round trip | Demo foundation complete. Docker/PostgreSQL runtime and production identity unverified. Full requested relational schema remains an extension. |
| 3 — integration storage | Client interfaces, fail-closed live stubs, synthetic paginated history, event deduplication, UTC persistence and reconciliation jobs; 4 ingestion tests | Synthetic path complete; live webhook/history/authentication/rate-limit transport blocked. No real API success claimed. |
| 4 — call journeys | Deterministic reduction, explicit root identity, legs, transfers, chronology, unknown coverage and clock-skew flags; 9 journey tests | Synthetic acceptance complete; provider event mapping still gated. |
| 5 — CRM | Tested phone normalization, all distinct synthetic candidates, current-only metadata, persistent retry schedule, outage isolation; 7 CRM tests | Synthetic complete; tenant-normalized exhaustive lookup and historical snapshots unverified. |
| 6 — UI and reporting | Overview, explorer/dialog, live-call view, agents, departments, CRM, recovery, exports and read-only admin; API/permission/export/WebSocket tests, frontend tests and build | Demo implemented. Browser results recorded below after execution. Large-scale aggregation/exports and editable mappings pending. |
| 7 — recovery and controls | Conservative candidate matching, one-use recovery call matching, recording denial/audit, freshness display; 3 recovery tests | Partial. Real recordings, retention enforcement, alerting and operational hardening pending. |
| 8 — production | Explicit fail-closed mode and deployment/backup checklist | Not complete. No production deployment, load/security certification or backup/restore drill claimed. |

## Acceptance A–J

| Case | Test evidence | Scope |
|---|---|---|
| A | test_A_three_misses_fourth_answers | One logical ANSWERED, three missed agent legs, zero customer MISSED |
| B | test_B_ivr_exit_no_invented_misses | IVR_ONLY, no legs |
| C | test_C_transfer_preserves_call_and_departments | Both legs and departments, primary Sales |
| D | test_D_permutations_and_duplicate_storage | 20 event permutations, duplicate storage |
| E | test_E_all_duplicate_candidates_stored | Two stored matches, no arbitrary selection |
| F | test_F_crm_failure_does_not_affect_telephony_and_retries | ERROR, bounded backoff, successful later retry |
| G | test_G_unknown_ring_coverage_is_null | Null attempt metrics, explicit unavailable UI |
| H | test_H_offset_normalizes_to_kolkata and frontend formatter test | Offset normalization to 10:00 IST |
| I | test_I_viewer_cannot_access_numbers_recordings_secrets_or_admin | Masking including nested transfers; 403 restricted resources |
| J | test_J_reconcile_retains_event_history | Stale synthetic call completes without event loss |

These validate internal/synthetic behavior. They do not establish that Acefone or LeadSquared can supply the evidence required for the same results on live calls.

## Executed validation

- Backend: 35 pytest tests passed on Python 3.14 / SQLite, including migration round trip and migration/ORM schema comparison. One non-failing upstream Starlette warning concerns httpx TestClient deprecation.
- Frontend: 3 Vitest tests passed; TypeScript check and Vite production build passed.
- Browser: 2 Playwright tests passed in local headless Google Chrome, covering Manager desktop journey/CRM/export and Viewer mobile masking/admin/export restrictions.
- PostgreSQL Alembic SQL generated offline, including TIMESTAMPTZ. No PostgreSQL server or Docker execution claimed.
- Startup shell syntax and Python compilation checked.

The browser review found and fixed an offscreen accessibility label escaping the table scroll container. API tests found and fixed unmasked phone values in nested transfer evidence. Hourly trend buckets now align with Asia/Kolkata hours rather than UTC hour boundaries.

### Final access checks

The running real-data app passed a localhost check using a random temporary Viewer account: client-selected Admin role did not elevate access, caller/DID and CRM names were masked, and admin/audit/export requests returned 403. The temporary verification account and sessions were removed. Unauthenticated call access returned 401; the frontend returned 200. Credential file, temporary administrator password file and database permissions were confirmed private. Named audit actors, session-revocation handling and user password changes are implemented.

## Detailed call flow and historical capture correction

The initial rolling three-day import did not provide complete prior-date coverage. The earlier flow projection also omitted agent labels/dispositions, the provider's missed-agent summary and Department flow nodes. One checked full-day API range matched the stored total (60 inbound calls), so no universal provider-vs-local count mismatch was claimed.

Implemented corrections:

- Sidebar Detailed Call Flow view with All Calls, Answered and Missed tabs, expandable timelines, names and dial/answer evidence, provider-reported missed agents and filterable participant names. Department nodes now contribute observed department involvement. No ring count, missed timestamp or transfer leg ID is fabricated.
- Call start dates align to CDR date/time when epoch evidence confirms the configured timezone, preserving correct near-midnight date attribution. Durations prefer the documented provider call_duration. Legacy naive API timestamps are interpreted as UTC in presentation.
- Visible calendar range controls and durable per-calendar-day imports query both directions explicitly, respect the returned page size, detect repeated pages, and resume after restart. Completion is shown separately from merely filtering stored records.
- Previously retained CDRs were reprojected without duplicate snapshots. The first 30-calendar-day history job completed successfully: **1,727 unique calls, zero rejected rows**, with 1,420 provider participant records.
- **70 backend tests**, **5 frontend tests**, production build and the extended built-app Chrome test passed. The browser test covers answered/missed tabs, date filtering and expanded agent flows. The live ephemeral-Viewer test also passed nested participant/flow phone masking and denied history writes.

## Agent outcomes and colour themes — 2026-10-29

- Detailed call flow has separate department, answerer and unique reported missed-agent count columns. Counts describe supplied people, not ringing attempts; missing evidence is labelled.
- Flow display offers **Detailed timeline** and **Call transfer list**. The drawer also includes a Call transfer list tab. This view orders supplied agent dial/answer events and lists missed summaries separately because they lack timestamps. It does not claim direct transfer relationships.
- Answerer projection version 3 uses the latest unambiguous timestamped answer event, resolving an unnamed event only through supplied identity. Ambiguous/missing final event evidence falls back to the labelled CDR answerer. Overall missed outcomes remain unchanged. Startup reprojects retained CDRs without extra provider API requests.
- The top-right Theme picker offers Forest light/dark, Ocean, Midnight, Plum, Amethyst, Sand and Slate. Preferences persist in the browser and the old dark preference migrates. Dark table text and outcome badges use higher-contrast semantic colours.
- Validation: **73 backend tests**, **11 frontend tests**, TypeScript/Vite production build, and Chrome internal-workspace test passed. The browser covered counts, transfer view, answerer source and theme persistence across reloads. A private database backup was created before the local app restart.
- Provider limitation: exact transfer leg links, timestamped missed-agent order and complete ring-attempt counts remain unavailable in the verified Acefone CDR contract. No additional provider endpoints were introduced.

## Missed-call definitions and visible filters — 2026-10-29

- Overview separates **Total missed** (all filtered missed inbound logical calls) from **Customer missed** (the subset with a named Department event in the retained provider call flow). A reporting/DID department label alone and a DTMF value without department evidence do not qualify. These are call counts, so repeat calls from the same number count separately. Recorded routing is the available proxy for department selection; exact keypad-to-department choice is not verified by the contract.
- The Customer missed hourly chart uses the same subset. Original source statuses and total missed counts are preserved.
- A visible filter layer provides an inclusive IST date range, department and call status, applied together. Quick dates and reset are available; applied values persist in the URL and populate on reload. Detailed call flow retains its existing date controls and uses the shared department/status layer.
- Removed the Historical data coverage/import panel from Detailed call flow as requested. Backend import capabilities and stored history remain intact.
- Validation: 74 backend tests, 11 frontend tests, TypeScript/Vite build and Chrome test passed. Fixtures cover department-routed misses, IVR exits, labels without flow evidence, DTMF alone, multiple department events, repeat callers, outbound exclusion, empty ranges and combined filters; browser validation also covers filter persistence.

## Corporate palettes and readability — 2026-10-29

- Added six corporate themes: Corporate navy, Corporate steel, Corporate teal, Corporate burgundy, Graphite dark and Clear white, bringing the picker to 14 palettes. Existing selections remain valid. The menu scrolls within the viewport on smaller screens.
- Increased operational typography: tables and controls use 14px, table supporting text uses 12px, labels/flow timestamps use 13px and the base scale uses 16px. Supporting text uses palette colours for contrast. Responsive navigation retains its compact icon layout; KPI cards wrap earlier to accommodate larger labels.
- Validation: 11 frontend tests, production TypeScript/Vite build and Chrome internal-workspace test passed. Browser checks verified all 14 choices, corporate palette persistence, actual computed 14px table text, and no document-level horizontal overflow at 390px. Synthetic desktop/mobile screenshots were reviewed. No backend or integration behavior changed.

## Soft charcoal dark theme — 2026-10-29

Added Soft charcoal (15 palettes total), with charcoal surfaces, warm off-white text, muted teal accents, subdued amber/green statuses and gentle borders. Chart colours follow the selected palette. The existing larger font sizes remain. Choose Theme → Soft charcoal; existing saved preferences are preserved until changed. Validation: 11 frontend tests, production build and desktop/mobile Chrome checks passed, including saved Soft charcoal selection after reload.

## Simplified agent performance and recorded attempts — 2026-10-29

- Agent performance now shows only Agent, Missed call count, Answered call count, Answered by attempt and Missed by attempt. Removed ring totals, talk time, response, transfer and partial-coverage columns from this panel. Legacy report fields remain available for compatibility.
- Counts represent distinct calls per named agent within current report filters. Includes missed-only agents, all evidenced answerers (including earlier answerers in a transfer flow), and a CDR answerer fallback. An agent can appear in both counts for one call. Repeated provider events and duplicate summary entries do not inflate totals.
- Attempt categories refer to positions among recorded agent dial events for each call, rather than verified complete provider ring attempts. A single unambiguous preceding dial can locate an answer; missing/repeated/simultaneous evidence remains unknown. Provider missed summaries have no per-attempt linkage, so their count is shown under Attempt unknown. No failure is inferred from a Dialed event alone. Synthetic explicit leg outcomes can retain a known missed position.
- Validation: 81 backend tests, 11 frontend tests, TypeScript/Vite build and Chrome internal-workspace test passed. Added coverage for missed-only agents, repeated calls, event deduplication, simultaneous/repeated dials, multiple answerers, CDR fallback, exact synthetic leg association, and combined filters. Browser checks verify the five-column panel and recorded answer position #2.

## Agent ratios replace attempt columns — 2026-10-29

- Replaced the two rightmost attempt breakdown columns with Missed call ratio and Answered call ratio. Existing missed/answered count columns remain. Each percentage includes its numerator and denominator beneath it.
- Denominator is each named agent's distinct involved calls under the active filters, using recorded dials, answers and reported misses. A call with both missed and answered evidence contributes once to the denominator, and once to each applicable numerator. Ratios can therefore overlap; dial-only calls can leave both outcomes zero. No dial is inferred to be missed.
- Backend retains attempt metadata for compatibility; UI explanation now describes ratios. No new provider API requests or stored-data changes were introduced.
- Validation: 83 backend tests, 11 frontend tests and production build passed. Added ratio checks for overlapping outcomes, dial-only calls and empty reports. Chrome checks verify the replacement headings, percentages and count/total display alongside existing filters and themes.

## Navigation cleanup — 2026-10-29

Removed Call explorer and Missed call recovery from the sidebar and their standalone frontend views. Old /calls and /recovery links redirect to Detailed call flow while preserving query filters; Overview's View all calls now opens Detailed call flow. Call history and backend reporting endpoints remain intact. Validation: 11 frontend tests, production build and Chrome checks passed, including absent navigation entries and both redirects.

## LeadSquared caller analytics — 2026-10-29

- Replaced the generic LeadSquared call table with a dedicated report using the existing date, department, status and search filters. A department-flow evidence checkbox defaults on; the Answered department calls shortcut applies answered status. The report defaults to inbound direction unless explicitly supplied.
- Global metrics cover selected logical calls, distinct normalized caller numbers, repeat calls, callers matched in the saved index, clean no-matches, unresolved lookups, matched call records, callers with older leads, later-created leads, multiple-match callers and unknown-caller calls. Totals span the entire filtered report rather than the visible page. Unknown numbers are never grouped into a fictitious unique caller.
- One row per known caller preserves all matching lead IDs, lead creation timestamps and latest saved Lead current stages, with per-lead and per-match synchronization times. Rows link to each underlying call. Multiple matches are never arbitrarily reduced to one. A lead created after the first selected call is labelled accordingly; no causal creation claim is made. Viewer phone/name masking is enforced server-side.
- Added the application endpoint GET /api/v1/reports/leadsquared; no provider endpoint was added and no provider data is written. It reads retained call and CRM evidence, with batched current-lead lookups. LeadSquared default-lead-type scope and unresolved/stale match limitations are displayed.
- Capability boundary: caller-phone matching indicates a saved lead match, not verified Acefone call-activity ingestion into LeadSquared. Historical lead-stage snapshots and whether a call caused lead creation remain unverified.
- Validation: 87 backend tests, 11 frontend tests, production TypeScript/Vite build and Chrome internal-workspace check passed. Tests cover repeat callers, current stage overriding older call snapshots, multiple matches, unknown callers, missing matches vs failed lookups, date/department/status combinations, pagination, department toggle and Viewer masking. Browser validation confirms both date boundaries, matched unique caller counts, creation date and current stage. Synthetic report screenshot reviewed.

## Business overview agent chart — 2026-10-29

Removed Recent conversations and Every outcome matters from Overview. Call-volume trend now spans the available width. Added a graphical list of all agents with separate answered/missed bars and exact call counts, sorting by answered or missed counts in either ascending or descending order (default: answered, highest first). Bars share a common scale, include accessible numerical values, and adapt to mobile widths. The chart uses existing agent-report counts and the overview's inbound date/department/status filters; no provider API or database changes were made.

Validation: 11 frontend tests, production TypeScript/Vite build and Chrome internal-workspace check passed. Browser checks cover both removed panels, numerical bars, ranking direction and metric, filter-driven counts and mobile document width. Synthetic screenshot reviewed.

## Individual agent overview tabs — 2026-10-29

Split the overview agent comparison into Answered calls, Missed calls and Best agent tabs. Each count tab now shows only its corresponding bars and retains ascending/descending sorting. Best agent ranks by highest answered-call count under the current filters, displays all tied leaders, and shows no winner when the selection contains no answered calls. Tabs support arrow/Home/End keyboard navigation. Existing backend counts are unchanged.

Validation: 11 frontend tests, production TypeScript/Vite build and Chrome internal-workspace test passed. Browser checks cover separate meters, sorting, filtered missed counts, highest-answer leader, zero-answer state, tied leaders, keyboard activation and mobile width.

## Failover exclusion and worst-agent tab — 2026-10-29

Per user instruction, Vadant is excluded from Best agent and the new Worst agent overview tab because he also serves as the failover destination. The ranking exclusion recognizes case-insensitive, trimmed Vadant/Vadnt/Vadat spellings used in the conversation. Best uses the highest answered-call count; Worst uses the highest reported missed-call count, with no rate or quality inference. All tied eligible leaders are displayed; all-zero eligible selections show no winner. Ordinary answered/missed charts, stored calls, agent reports and totals continue to include him.

Validation: 11 frontend tests, production build and Chrome check passed. The browser fixture gives Vadant higher answered and missed counts than every other agent and verifies that he is excluded from both ranked cards while remaining visible in the ordinary missed chart; tied eligible leaders and the no-answer state are also checked.

## Support exclusion from agent rankings — 2026-10-29

Support department calls are excluded from Best agent and Worst agent comparisons, alongside the existing Vadant exclusion. The application agent-report endpoint accepts a ranking-only department exclusion and calculates a separate ranking_items result after removing calls whose primary or involved department is Support (trimmed/case-insensitive). Thus agents working across departments retain counts from eligible calls. Normal call charts, agent reports and records remain complete. No provider API changes or data deletion were performed.

Validation: 88 backend tests, 11 frontend tests, production build and Chrome check passed. Backend coverage verifies exclusion before aggregation, including calls involving Support after an earlier department and mixed-case names. Browser coverage verifies that a Support-only agent with larger counts is absent from best/worst cards and that the standard charts retain their full data.

## Agent rankings in LeadSquared insights — 2026-10-29

Added a Best and worst agents panel above the LeadSquared caller table, with Best agent and Worst agent tabs. It uses the same complete report selection (including date, department, call status, search, direction and department-flow checkbox), independent of pagination. Counts include all selected calls, whether or not the caller has a LeadSquared match. Support calls are removed before aggregation and Vadant remains excluded from ranked cards. Criteria and ties match Overview: most answered calls and most reported missed calls, respectively. Existing LeadSquared statistics and caller rows remain intact.

The local LeadSquared analytics endpoint now returns ranking_items from the selected calls. Shared department-exclusion logic is reused by both overview and CRM report rankings. No provider API endpoints, credentials or provider records were changed.

Validation: 89 backend tests, 11 frontend tests, production TypeScript/Vite build and Chrome internal-workspace check passed. Added coverage for ranking totals across pages, Support exclusion, department-flow toggle and status filters. Browser checks verify both CRM ranking tabs and expected counts, alongside existing overview exclusions, ties and keyboard controls.

## Lead owner column — 2026-10-29

Added Lead owner beside creation date/current stage in the LeadSquared caller report. Every matched lead retains its own owner and is identified separately when multiple leads match. The report uses the current saved Lead owner rather than an older call snapshot. Missing values show Not available; UUID-shaped values are explicitly labelled Owner ID · name not available. The verified live scan currently imports OwnerId, so no undocumented owner-name resolution endpoint or guessed name was introduced.

Validation: 5 CRM analytics backend tests, 11 frontend tests, production build and Chrome internal-workspace check passed. Existing CRM test coverage now verifies that the latest owner overrides an older call snapshot, and the browser checks the new header and fictional owner value.

## Verified LeadSquared owner names — 2026-10-29

Verified the official read-only GET /v2/UserManagement.svc/Users.Get contract at https://apidocs.leadsquared.com/get-users/ and successfully called it on the existing validated tenant host with header credentials. The account returned 24 named users. The locally cached directory resolves all 16 distinct owner IDs attached to matched call leads at verification. Only ID/name mappings are retained; emails, roles and other directory fields are omitted.

The live sync checks the directory hourly and retries failed refreshes after five minutes, independently of the large lead scan. Failures preserve the last successful names. Lookup uses the documented ID/FirstName/LastName fields, including names supplied for inactive users. The original lead owner ID remains unchanged for matching/filtering, while the report exposes current_owner_name and displays only the name. Unresolved owners show Name not available and no owner ID is rendered in the column.

Validation: the full backend suite passed 91 tests before the final report-resolution test was added; all 8 focused owner/CRM tests then passed. Eleven frontend tests, production build and Chrome internal-workspace check passed. Coverage includes documented GET method/auth without credential URL parameters, cache expiry/retry behavior, retaining names on outages, case-insensitive IDs and report-level name resolution. Browser uses a fictional lead with a stored Owner ID and verifies its resolved name is visible and the ID is absent. Counts-only live verification confirmed all matched-call lead owners resolve.

## TWSS IVR branding and department-missed button — 2026-10-29

Renamed the visible platform to TWSS IVR in the staff/demo login screens, sidebar, footer, browser title and API application title. Existing credentials, sessions, saved preferences and stored records are preserved.

Added Missed after department selection to Detailed call flow, alongside All calls, Answered and Missed. Its count and records require a missed call outcome and a named department in the retained call flow, excluding IVR exits and reporting-only department labels. Source records are filtered before pagination; CSV/XLSX exports honor the same selection. The selection is saved in the URL, clears when another outcome is chosen, and the button wraps on small screens. Existing date, department, agent and search filters apply.

Validation: 93 backend tests, 11 frontend tests, production build and Chrome check passed. The focused missed-department test was additionally extended and passed for CSV export. Browser validates TWSS IVR title, the new tab's count/selection, switching outcomes and existing mobile layout. No provider endpoints or API fields were invented.

## Shared rows-per-page selector — 2026-10-29

Added Rows per page with 10, 25, 50, 100 and All options to Detailed call flow, LeadSquared insights, Live calls and the staff administration audit log. Existing non-paginated lists already show all records. The shared browser preference persists across tabs and reloads; changing it resets the current page to 1. Detailed-flow expansions close on size changes.

Local calls, CRM analytics and audit endpoints support an explicit show_all option while retaining the existing page_size validation and role checks. All applies to the current filtered records and disables Next. CRM totals and agent rankings still cover the complete selection independently of page size. No provider APIs or stored customer records were changed.

Validation: 96 backend tests, 11 frontend tests and production TypeScript/Vite build passed. Added coverage for paginated vs All results, unchanged CRM summary totals, Viewer masking and audit sizes. Focused Chrome pagination check passed for page reset, complete lists, disabled Next and preference persistence across report/admin/live tabs. The expanded combined browser run hit the existing request limit; the new pagination scenario was isolated in pagination.spec.ts and rerun with a fresh scripts/browser_test_internal.py fixture. Run workspace.spec.ts and pagination.spec.ts with separately reset fixtures, preserving the application's production request limit and temporary-password workflow.

## TWSS logo and two-mode appearance — 2026-10-29

Created a custom vector TWSS monogram and TWSS / IVR wordmark, replacing the workflow symbol in the sidebar and both login views. The mark uses palette-aware colours and scales cleanly in the compact sidebar. A matching SVG browser icon is bundled under Vite assets so the existing internal static route serves it correctly. Reusable source: frontend/src/assets/twss-mark.svg; UI component: frontend/src/Brand.tsx.

Replaced the large palette menu with a compact two-button Light/Dark appearance switch. Light uses Corporate navy; Dark uses Soft charcoal. Earlier saved palettes migrate to their corresponding light/dark mode, preserving user preferences and larger text sizes. No API, authentication or stored-data changes were made.

Validation: 12 frontend tests, production TypeScript/Vite build and full workspace Chrome browser check passed. Browser checks verify the TWSS logo, exactly two appearance buttons, preference persistence after reload, computed table font sizes and mobile layout. Synthetic light desktop and dark mobile screenshots were visually reviewed.

## Live Render Free deployment — 2026-10-29

Deployed to https://twss-ivr.onrender.com using the user's Render workspace and dedicated Neon Free PostgreSQL database. The user rejected paid hosting; no paid service or persistent disk was created. Existing Mac data and accounts were migrated from a consistent private SQLite snapshot using transactional PostgreSQL COPY with table-count checks and sequence reseeding. Old browser sessions were not copied. Password hashes/roles matched exactly after import. Source Mac data remains available for recovery.

Imported snapshot: 1,745 calls, 206,243 leads, 1 staff account, 1,305 call/lead matches, 1,434 call participants and the retained CRM index progress. Live HTTPS login and customer-data masking were verified with an ephemeral Viewer removed afterward; admin/audit/export/history-write restrictions remained enforced. Chrome verified real sign-in rendering. Render API confirmed Free plan; readiness and live frontend checks passed. Provider synchronization is enabled, with Acefone HEALTHY and CRM refresh resuming.

Current validation: 99 backend tests and 12 frontend tests passed, production frontend build passed, real PostgreSQL migrations/import/reports and live HTTPS/Chrome checks passed. Free-plan idle sleep/usage limits still apply, and independent production load/security certification is not claimed. See docs/render-deployment.md.

### Cloud sync follow-up — 29 October 2026

Live diagnosis confirmed a free-instance shutdown/restart and a long interval between successful Acefone jobs while the sequential CRM index was running. PostgreSQL deployments now poll Acefone independently of the CRM worker, retaining the local SQLite serial behavior. CRM call projections use short per-call row locks to avoid overwriting newer CDR evidence. Scheduler failures retry instead of terminating the task. The banner shows provider sync state and warns after five minutes without a successful import; a browser connection no longer implies fresh provider data. Render Free still pauses all background work while asleep.

Validation: 101 backend tests (including a blocked-CRM/nonblocking-call regression and scheduler retry test), 12 frontend tests and the production frontend build passed.

### LeadSquared caller checks and clearer report — 29 October 2026

Fixed delayed positive matches by joining unmatched callers to the saved phone index and running a separate bounded caller check alongside full indexing. A live read-only provider check recovered four unique callers across six calls. Phone and Mobile searches use the documented criteria API, normalize complete numbers, preserve multiple leads and retry incomplete checks. A newer direct phone result survives an older index refresh.

The LeadSquared tab now uses plain status labels, short summaries, lead creation date/stage and owner names. Technical IDs, per-row sync notes and repeated explanations were removed; the remaining caveats are under “How to read this report.” Pending checks never say “No lead found.”

Validation: existing 101 backend tests plus four phone-matching regressions passed; 12 frontend tests and production build passed.

### Call details cleanup and owner names — 29 October 2026

Removed the call drawer's notice boxes, repeated CRM caveats, sync notes and technical call/lead IDs. Call detail, journey and CRM endpoints now resolve the current saved lead owner through the LeadSquared user directory, so the drawer shows a name instead of the stored identifier. Unknown directory entries display “Owner name unavailable.” Existing Viewer lead-name masking is preserved.

Validation: three owner-directory tests (including all three detail endpoints, current-owner changes and missing names), twelve frontend tests and the production frontend build passed.

### Executive analysis dashboard — 29 October 2026

Replaced the overview with six clickable KPIs, hourly/daily stacked call traffic (bar/line toggle), an answer-coverage donut, busiest-hour and agent highlights, sortable department volume/outcome bars, and the existing answered/missed/best/worst agent tabs. KPI and department counts open filtered inbound call lists; customer-missed links retain the department-routing requirement. Support and Vadant remain excluded from best/worst rankings. Charts and percentages use actual filtered counts; other missed calls are separate from missed department calls, avoiding double counting. Backend additions provide distinct known caller numbers and actual missed department totals instead of deriving misses as total minus answered.

Verified empty data, sparse-hour zero filling, India-date aggregation, outcome totals, both themes, mobile width, chart controls and call drilldowns with synthetic data. 107 backend tests, 16 frontend tests and a Chrome end-to-end dashboard test passed; the production build passed. Browser previews are local synthetic artifacts and are not deployed data.

### Department-only answer rate — 29 October 2026

The dashboard answer rate now equals answered inbound department calls divided by all inbound calls with a named department event, within the selected filters. Both numerator and denominator exclude callers without recorded department routing, including calls with only a reporting label. The card shows the two department counts, and the outcome donut uses the same scope. A zero denominator returns null (“—”). The answer-rate drilldown and its outcome tabs retain the department-selection filter; reset filters clears it. Overall inbound totals remain available separately.

Validation: 109 backend tests, 16 frontend tests, production build and the Chrome dashboard/drilldown test passed. Regression cases cover repeated calls, no selection, labels without routing evidence, zero department calls and filtered pagination/counts.

### Independent filters per analytical tab — 30 October 2026

Sidebar navigation now restores the destination tab's own query instead of copying the current tab's filters into every destination. The workspace remembers each tab during navigation, while the current URL still supports refresh, direct links and browser history. Filter forms remount per route so unsaved dates/departments do not spill into another tab. Rows-per-page preferences are stored per route. Reset/clear affects only the active tab; intentional dashboard-to-call drilldowns still pass their selected scope.

Validation: 16 frontend tests and production build passed. Two Chrome tests passed, covering all six analytical tabs, independent date/department/status/search filters, per-tab resets, rows-per-page persistence and existing department-only dashboard drilldowns. No backend or provider API changes were required.

### Answered calls by default in LeadSquared insights — 30 October 2026

LeadSquared insights now defaults to answered calls while retaining the department-only default. The shared status selector, summary totals, caller rows and report requests use that default consistently. The total is labelled “Answered calls.” Explicit other statuses and “All statuses” remain available; reset/clear returns to the answered default. The shortcut is hidden while answered department calls are already selected. Filter drafts synchronize from actual applied fields rather than unrelated query changes.

Validation: 16 frontend tests, production build and three Chrome checks passed (answered summary against the API, explicit all-status selection/reset/refresh, independent tabs and dashboard drilldowns). Browser checks were isolated as needed to respect the preview server's request budget. No provider APIs or backend contracts changed.

### All answered calls in LeadSquared insights — 30 October 2026

Reconciliation for 29 October IST found 16 answered inbound calls, of which 13 had a recorded department event. The department-only checkbox, rather than missing captured calls, excluded the other three. LeadSquared insights now defaults to all answered calls with this optional checkbox off. Enabling it labels the total “Answered department calls” instead of implying an account-wide answered total. No department routing was inferred for the three records without that event. The Overview department-based answer rate is unchanged.

Validation: 16 frontend tests, production build and the Chrome LeadSquared regression passed. Browser assertions verify the default API request includes department_selected=false, all-status override/reset, department-only toggle and labels. Counts were checked against the live database without displaying caller records.

### Weekly call patterns tab — 30 October 2026

Added Call patterns with busiest weekday, busiest hour and peak weekday/hour highlights, seven-day volume bars, a selectable weekday hourly chart and an interactive 7×24 heatmap. Counts use the existing filtered inbound hourly report and Asia/Kolkata time, including all recorded call outcomes by default. Ties are retained, empty data has no invented winner, and records without start times are excluded with a count when applicable. This week uses Monday through today; Last week uses the previous complete Monday–Sunday week. Date, department, call status and search filters remain independent from other tabs.

Validation: 20 frontend tests, production build and a Chrome test passed. Coverage includes India-day boundaries, multiple weeks, tied leaders, aggregate consistency, hour/weekday focus, calendar-week shortcuts, empty results, independent navigation, both themes and mobile width. No external API endpoints or database changes were introduced.
