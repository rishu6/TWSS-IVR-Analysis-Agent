# S-03 — Secure SDLC Policy

Baseline: 2026-10-30 · Status: **Proposed policy — approval pending**

Proposed responsible function: Engineering / Security. No named assignment or approval is implied.

## Current implementation evidence
Backend pytest, frontend Vitest, TypeScript/Vite production build and selected Playwright checks are run locally. A GitHub Actions example exists outside .github/workflows and is not active. No repository evidence establishes enforced review protection, mandatory scanning, external penetration testing or automatic production release approvals.

## Proposed change process
For a code change: identify the affected rule/endpoint, use synthetic fixtures, implement server-side validation/authorization, run appropriate tests and review the diff for secrets/data. For a dependency change: review provenance, compatibility, vulnerability notices and lockfile impact. For an integration change: first validate the official contract and tenant capability; never patch a guessed endpoint into runtime.

## Review checklist
Check roles and CSRF on mutations, masking on read/export paths, exact host validation, retry limits, date/time boundaries, SQL filtering before pagination, and data preservation under replay. Separate synthetic and internal startup. Do not seed demo data in an internal/cloud database. Keep .env.*, .runtime, database files and virtual environments out of commits.

## Proposed release gates
Tests and build should pass; migration and rollback effects should be understood; named owners should review sensitive changes. Add SAST/dependency/container scanning and branch protection only through an authorized repository change. An example pipeline is not proof that these gates currently block merges. Track approvals and open gaps rather than marking unchecked controls complete.

---
Evidence: .github/ci-workflow.example.yml; .gitignore; tests/; frontend/package.json. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
