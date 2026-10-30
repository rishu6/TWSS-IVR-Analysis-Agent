# N-04 — Load and Resilience Test Plan

Baseline: 2026-10-30 · Status: **As-built / proposed guidance — review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

## Proposed test design
Use synthetic calls and leads with realistic duplicate rates and date distributions. Exercise concurrent filtered reports, pagination, exports, imports and synchronization with provider transports stubbed. Never send load traffic to Acefone or LeadSquared.

## Procedure and review
Record dataset size, concurrency, CPU/memory, database bytes, latency percentiles and errors. Test database disconnects, throttled provider responses and resumable imports. Run against isolated infrastructure with an agreed limit; no completed load certification is claimed.

---
Evidence: README.md; docs/phase-status.md; backend/app; frontend/src; scripts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
