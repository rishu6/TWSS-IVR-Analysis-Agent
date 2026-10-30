# N-01 — Nonfunctional Requirements and Service Objectives

Baseline: 2026-10-30 · Status: **As-built / proposed guidance — review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

## Proposed objectives
Target understandable responsive reports, durable approved storage and clear sync failure states. Current single-process operation and free-tier quotas constrain availability. No contractual uptime or measured latency percentile has been established.

## Procedure and review
Before approving service objectives, measure representative data volumes, cold starts, concurrent users and provider throttling. Define request latency, error rate, recovery time and data freshness separately. A 60-second polling interval is not a guarantee that all data is at most one minute old.

---
Evidence: README.md; docs/phase-status.md; backend/app; frontend/src; scripts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
