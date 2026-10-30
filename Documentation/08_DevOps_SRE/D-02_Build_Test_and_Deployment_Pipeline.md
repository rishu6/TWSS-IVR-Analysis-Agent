# D-02 — Build Test and Deployment Pipeline

Baseline: 2026-10-30 · Status: **As-built / proposed guidance — review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

## Implemented release path
Frontend builds with Vite; the backend runs migrations and application checks. Docker builds frontend assets and packages the backend. The repository contains an example CI workflow, but it is not an active GitHub Actions pipeline.

## Procedure and review
Run the documented tests before a release, inspect the diff and push an intentional commit. Render auto-deploy is disabled; an explicit deployment is separate. Do not describe a successful source push as a live release. Keep deployment credentials outside logs and source control.

---
Evidence: README.md; docs/phase-status.md; backend/app; frontend/src; scripts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
