# TWSS IVR — Acefone India & LeadSquared Analytics

A Mac-local internal dashboard for analysing Acefone call history alongside LeadSquared leads. Built with React, TypeScript, FastAPI and SQLite. Provider integrations are read-only.

## Features

- Business overview with call totals, answered/missed trends and sortable agent charts.
- Separate Answered calls, Missed calls, Best agent and Worst agent tabs. Best/worst rankings exclude Support calls and the configured failover-agent name.
- Detailed call journeys with IVR/department events, reported missed-agent counts and recorded dial/answer activity. Includes a **Missed after department selection** filter.
- LeadSquared insights with unique callers, repeat calls, existing lead matches, lead creation dates, current stages and resolved lead owner names.
- Date, department, status and search filters, CSV/XLSX call exports, and shared rows-per-page choices: 10, 25, 50, 100 or All.
- Individual password accounts, Admin/Manager/Viewer permissions, mandatory first-login password change, Viewer masking and audit logs.
- TWSS vector branding and compact Light/Dark appearance controls.
- Resumable historical imports and CRM indexing, local backups and raw-data retention.

## Run the internal app on a Mac

Requires Python 3.12+ and Node.js 22.12+ (Node.js 24 recommended).

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
npm --prefix frontend ci
npm --prefix frontend run build
cp .env.integrations.example .env.integrations
chmod 600 .env.integrations
```

Fill in `.env.integrations` locally with your Acefone API token, LeadSquared API host, access key and secret key. Do not commit or share this file.

```bash
.venv/bin/python scripts/internal.py
```

Open **http://localhost:8001**. On a fresh installation, the temporary Local Admin sign-in details are generated in **`.runtime/first-login.txt`**. A password change is required before accessing account data. Existing accounts are preserved on restart.

The app creates its private SQLite database, runtime files and backups under `.runtime/`. These files, integration credentials, virtual environments and generated frontend builds are excluded from Git. Cloning this repository does not copy an existing installation's call data, staff accounts or API credentials.

See [internal installation and operations](docs/internal-deployment.md) for staff accounts, department mappings, backups and recovery.

## Render deployment

See [Render Free + Neon Free deployment](docs/render-deployment.md) for cloud configuration and migration of an existing Mac installation. The free deployment needs a separate persistent PostgreSQL database; local SQLite files cannot survive Render Free restarts.

## Synthetic demo

The demo uses fictional data and does not load provider credentials:

```bash
bash scripts/dev.sh
```

Open **http://localhost:5173**. The demo password is `synthetic-demo-only`; its selectable roles are for inspecting synthetic examples. Keep the demo separate from real customer data. The internal app uses individual accounts instead.

## Validation

```bash
.venv/bin/python -m pytest -q
npm --prefix frontend test
npm --prefix frontend run build
```

Internal browser checks use Google Chrome and an isolated synthetic database:

```bash
# Terminal 1: creates/resets the browser fixture on port 8002
.venv/bin/python scripts/browser_test_internal.py

# Terminal 2
cd frontend
npx playwright test workspace.spec.ts --config playwright.internal.config.ts
```

Stop and restart the fixture before running `pagination.spec.ts` instead of `workspace.spec.ts`. Each check starts from the fixture's temporary-password state; separate runs also preserve the app's request limits. Fixture passwords are fictional test values. A GitHub Actions configuration is included in `.github/ci-workflow.example.yml`. It is saved as an example because the current GitHub login cannot upload active workflow files. With explicit workflow authorization, it can be moved into `.github/workflows/ci.yml` to enable backend tests, migrations, frontend tests and the production build without provider credentials.

## Data and deployment boundaries

The Mac entrypoint binds to localhost. The cloud entrypoint is deployed at **https://twss-ivr.onrender.com** on Render Free with persistent Neon PostgreSQL data and HTTPS. It requires individual staff sign-in; credentials and customer records are not included in this repository. Free hosting can sleep when idle. Corporate SSO/MFA and production load certification remain separate work. The root Dockerfile has been deployed on Render; the separate Docker Compose/Redis/Celery setup remains unverified.

- Exact provider ring-attempt counts and transfer links are not verified. The app distinguishes recorded events from unavailable evidence and does not infer a missed attempt from a dial alone.
- LeadSquared matches indicate caller numbers found in the saved default-lead-type index. They do not prove call-activity logging, call-driven lead creation or historical stage/owner values.
- Owner names use LeadSquared's documented user directory and a local hourly cache. Failed refreshes retain previously resolved names.
- Provider webhooks and recording playback remain gated on verified access/authentication and retention requirements. No lead-creation or call-placement API is implemented.

See the [capability matrix](docs/integration-capability-matrix.md), [phase status](docs/phase-status.md) and [operations guide](docs/operations.md) for detailed evidence and remaining limitations.
