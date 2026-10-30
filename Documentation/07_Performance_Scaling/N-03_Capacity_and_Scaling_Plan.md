# N-03 — Capacity and Scaling Plan

Baseline: 2026-10-30 · Status: **As-built / proposed guidance — review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

## Current capacity boundary
Local SQLite is suitable for one Mac process. PostgreSQL enables the cloud worker arrangement, but no certified maximum user count or data size exists. Render Free and Neon Free are quota-bound infrastructure choices.

## Procedure and review
Measure first. Consider compact pagination, indexed queries and bounded synchronization before increasing workers. Do not share SQLite across multiple processes as a scaling strategy. Any paid hosting or capacity change requires a separate cost decision; none is approved by this documentation.

---
Evidence: README.md; docs/phase-status.md; backend/app; frontend/src; scripts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
