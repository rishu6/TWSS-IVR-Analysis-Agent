# C-07 — Vendors and Subprocessors Register

Baseline: 2026-10-30 · Status: **Draft — business review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

## Service inventory
Acefone India supplies call history; LeadSquared supplies CRM leads and user names; GitHub hosts source; Render hosts the cloud process; Neon hosts cloud PostgreSQL. A Mac is the current operational fallback. No OpenAI or other model provider is used by the application.

## Procedure and review
The account owner must verify contractual role, actual region, access controls, retention, terms and incident contacts for each service. Free-tier availability is constrained: [Render Free](https://render.com/docs/free) can sleep; [Neon network transfer](https://neon.com/docs/introduction/network-transfer) can stop database availability when exhausted. No paid upgrade is authorized.

---
Evidence: README.md; docs/phase-status.md; backend/app; frontend/src; scripts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
