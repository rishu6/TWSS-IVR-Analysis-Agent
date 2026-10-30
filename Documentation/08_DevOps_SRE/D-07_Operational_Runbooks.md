# D-07 — Operational Runbooks

Baseline: 2026-10-30 · Status: **As-built / proposed guidance — review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

## Mac operation and incident handling
Start locally with .venv/bin/python scripts/internal.py from the repository, then open http://localhost:8001. Use the terminal process or the existing managed local session; do not launch duplicate instances against the same SQLite database. Sign in with the assigned account.

## Procedure and review
If cloud will not wake, inspect Render service logs and Neon Usage. The current incident is exhausted Neon monthly network transfer, not simply Render sleep. Do not upgrade without authorization. For stale calls inspect sync state and import scope; for missing CRM matches inspect lookup completion and directory refresh. Never treat a failed lookup as proof that no lead exists.

---
Evidence: README.md; docs/phase-status.md; backend/app; frontend/src; scripts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
