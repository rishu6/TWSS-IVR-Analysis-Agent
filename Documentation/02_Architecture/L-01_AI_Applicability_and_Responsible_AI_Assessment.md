# L-01 — AI Applicability and Responsible AI Assessment

Baseline: 2026-10-30 · Status: **As-built / proposed guidance — review pending**

Proposed responsible function: Engineering / business owner. No named assignment or approval is implied.

## Applicability decision
TWSS IVR currently uses deterministic normalization, database queries, matching and charts. It does not run an LLM, RAG pipeline, embeddings, AI scoring, transcription or automated model decisions. No customer data is sent to a model provider by the application.

## Procedure and review
The reference project sections for prompt management, model evaluation, RAG lineage, model monitoring, model release and AI incident response are therefore not applicable. If AI is proposed later, define purpose, privacy authorization, evaluation, human review, vendor terms, costs and rollback before implementation. No AI controls are claimed as implemented.

---
Evidence: README.md; docs/phase-status.md; backend/app; frontend/src; scripts. Source baseline: `9fa87271efd5d69d2d769c519150b032df97bdf9`.

[Documentation register](../00_Documentation_Register.md)
