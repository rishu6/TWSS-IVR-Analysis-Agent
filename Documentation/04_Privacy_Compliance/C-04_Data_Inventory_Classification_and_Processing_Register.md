# C-04 — Data Inventory Classification and Processing Register

Baseline: 2026-10-30 · Status: **Draft — business review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

## Data inventory
Restricted: caller and DID numbers, provider event payloads, lead identifiers, lead phone numbers, stage, owner, staff accounts and exports. Secret: provider tokens, database URLs, session credentials and bootstrap passwords. Operational: import checkpoints, aggregate metrics and audit entries; combinations can still identify people.

## Procedure and review
Flow: Acefone HTTPS reads → raw events and logical-call projections → reports; LeadSquared HTTPS reads → lead/phone index and owner directory → caller matches. Render and Neon host cloud processing; the Mac holds its own SQLite records and backups. Record the business purpose, recipient, storage region and retention for each category before approval.

---
Evidence: README.md; docs/phase-status.md; backend/app; frontend/src; scripts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
