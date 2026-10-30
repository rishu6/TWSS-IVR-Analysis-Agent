# D-05 — Observability and Alerting Guide

Baseline: 2026-10-30 · Status: **As-built / proposed guidance — review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

## Existing signals
Health checks perform a database query. Integration state tracks attempts, success and progress. Audit events record selected sensitive actions. Cloud startup performs database work before binding, so a database outage can prevent HTTP health from becoming available.

## Procedure and review
No staffed alert rota or external monitoring SLA is established. Review database quota and provider errors alongside application logs. Avoid logging full URLs containing credentials, session cookies or raw customer payloads. A connected browser does not by itself prove provider synchronization succeeded.

---
Evidence: README.md; docs/phase-status.md; backend/app; frontend/src; scripts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
