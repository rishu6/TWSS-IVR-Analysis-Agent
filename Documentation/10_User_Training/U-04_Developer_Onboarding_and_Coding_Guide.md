# U-04 — Developer Onboarding and Coding Guide

Baseline: 2026-10-30 · Status: **As-built / proposed guidance — review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

## Local development
Use Python 3.12+ and Node 22.12+ as specified by the repository; the production container uses Python 3.12 and Node 24 build tooling. Install backend and frontend dependencies from their manifests and follow README commands. Use synthetic fixtures for development.

## Procedure and review
Backend code is under backend/app, tests under tests, and React code under frontend/src. Preserve source identity, explicit absence/unknown states, IST bounds and permission checks. Run backend and frontend tests for behaviour changes. Do not modify .venv package files to change the application. Rebuild this pack with scripts/build_documentation.py after updating authored content.

---
Evidence: README.md; docs/phase-status.md; backend/app; frontend/src; scripts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
