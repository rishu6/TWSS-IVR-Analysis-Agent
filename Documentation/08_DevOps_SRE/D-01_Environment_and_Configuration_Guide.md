# D-01 — Environment and Configuration Guide

Baseline: 2026-10-30 · Status: **As-built / proposed guidance — review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

## Environment boundaries
Local internal mode uses .runtime/internal.db and loopback port 8001. Synthetic preview uses its own database and port 8003. Browser fixtures use a separate test database. Cloud requires PostgreSQL and an exact HTTPS origin.

## Procedure and review
Keep integration values in private ignored environment files. Never copy .env files into source, container images or documentation. Use .env examples for variable names only. Mac and cloud databases are independent after migration; verify which environment you are inspecting.

---
Evidence: README.md; docs/phase-status.md; backend/app; frontend/src; scripts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
