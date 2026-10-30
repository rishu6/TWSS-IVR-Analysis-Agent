# A-02 — Architecture Decision Records

Baseline: 2026-10-30 · Status: **As-built draft — review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

| ADR | Decision / rationale | Current consequence |
|---|---|---|
| 001 | React + TypeScript + Vite, FastAPI + SQLAlchemy | Single repository and built static frontend |
| 002 | Separate synthetic/internal modes | Demo never needs provider access; internal uses named accounts |
| 003 | SQLite for the Mac installation | Simple single-machine persistence and backup |
| 004 | PostgreSQL for Render Free | Render's ephemeral filesystem cannot retain the working database |
| 005 | Read-only documented provider contracts | No CRM creation, call placement or guessed endpoints |
| 006 | Provider call ID is the identity boundary | No phone/time-based merging |
| 007 | Preserve candidate sets and missing evidence | Multiple matches and unknown attempts remain explicit |
| 008 | In-process single-instance scheduling | No production Redis/Celery dependency; distributed scheduling remains future work |
| 009 | Independent PostgreSQL CRM and call workers | A long index refresh does not hold the next call poll |
| 010 | Per-route filters and row preferences | Sidebar navigation restores each analytical tab independently |
| 011 | Department rate and all-answered CRM defaults have different scopes | Card captions and optional subsets must identify denominators |
| 012 | No paid hosting selected | Free quota and sleep limitations must be operated explicitly |
| 013 | Limit repeated cloud reads after quota incident | Read only visible reports and changed CRM call projections |

These records summarize source/session decisions; they are not newly signed architecture approvals. Reconsider a decision only with its data-migration, access-control, cost and rollback effects recorded. Actual meeting minutes, formal approver signatures and procurement approvals are not available in the repository.

---
Evidence: docs/phase-status.md; render.yaml; backend/app/cdr.py; frontend/src/main.tsx. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
