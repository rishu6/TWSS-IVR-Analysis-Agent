# A-05 — Infrastructure Architecture

Baseline: 2026-10-30 · Status: **As-built draft — review pending**

Proposed responsible function: Operations / Engineering. No named assignment or approval is implied.

## Current topology
| Environment | Application | Persistent data | Entry |
|---|---|---|---|
| Mac internal | Single Python/Uvicorn process, built frontend | .runtime/internal.db and local backups | Loopback port 8001 |
| Synthetic preview | Isolated demo database and static build | Disposable .runtime/dashboard-preview.db | Loopback port 8003 |
| Internal browser fixture | Synthetic named-account installation | Dedicated test SQLite file | Loopback port 8002 |
| Cloud | Docker on Render Free, Singapore configuration | Separate Neon PostgreSQL | twss-ivr.onrender.com over HTTPS |

Render runtime disk is ephemeral; the cloud entrypoint requires PostgreSQL and does not use a persistent paid disk. Neon region and vendor residency obligations must be confirmed from the account/settings/contracts. Singapore hosting is not India-only residency. No WAF, VPN, private VPC connectivity, CDN administration or infrastructure-level failover is established by this repository.

## Startup and failure boundary
Startup validates origin/configuration, acquires a single-process filesystem lock, runs migrations/admin setup/flow rebuild, then starts Uvicorn. A database refusal can fail startup before the web server binds. /healthz checks database access. A running deployment label does not establish user-facing readiness. On 30 October the Neon transfer quota blocked cold startup despite Render not being suspended.

## Operational implications
Mac and cloud are distinct installations. Keep credentials out of images/source, and inspect plan/disk settings before resource creation. render.yaml is a blueprint with initial migration gating and sync disabled until verified migration activation. An existing deployed service's environment can differ from blueprint defaults.

---
Evidence: Dockerfile; render.yaml; scripts/cloud.py; scripts/internal.py; scripts/render_service.py. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
