# TWSS IVR — Documentation Register
Baseline: **2026-10-30** · Source commit: `9fa87271efd5d69d2d769c519150b032df97bdf9`

## Scope and reading guide
This pack documents the current TWSS IVR implementation. The supplied Documentation.zip from another project was used as a category checklist only; its learning-platform requirements and instructions do not govern this project. Product and architecture chapters describe implemented behaviour; policies, approvals and future plans are explicitly drafts. No document is a signed approval or compliance certificate.

Start with P-01 for the business requirements, U-01 for daily use and D-07 for operations. P-09 defines calculations; A-04 provides the source-derived API contract; A-03 contains the complete ORM data dictionary. Older docs under docs/ preserve historical project evidence; current source takes precedence where a historical statement differs.

**Operational baseline:** the Mac installation is the working fallback. Render/Neon cloud availability is blocked by the exhausted Neon monthly network-transfer allowance as of this date. No paid upgrade is approved. This pack does not migrate data, deploy software or include customer records.

[Offline HTML reader](index.html) · [Word business requirements](TWSS_IVR_Business_Requirements.docx) · [Validation record](validation-results.json)

## Folder structure
```text
Documentation/
├── 01_Product/
├── 02_Architecture/
├── 03_Security/
├── 04_Privacy_Compliance/
├── 05_Audit_Governance/
├── 06_Quality_Evaluation/
├── 07_Performance_Scaling/
├── 08_DevOps_SRE/
├── 10_User_Training/
├── 11_Project_Management/
└── 00_Documentation_Register.md
```
Each folder contains separate Markdown documents for the current TWSS IVR project. The optional HTML reader, Word BRD, generated technical references and illustration assets accompany these source documents. The numbering follows the supplied reference: there is no separate 09 category. The AI applicability assessment is retained under Architecture because this application has no AI feature.

## Document register
| ID | Document | Status | Proposed responsible function |
|---|---|---|---|

| P-01 | [Business Requirements Document](01_Product/P-01_Business_Requirements_Document.md) | As-built draft — review pending | Business owner / Product |
| P-02 | [Product Walkthrough](01_Product/P-02_Product_Walkthrough.md) | As-built draft — review pending | Product / Design |
| P-03 | [Product Requirements Specification](01_Product/P-03_Product_Requirements_Specification.md) | As-built draft — review pending | Product / Engineering |
| P-04 | [Personas and Journey Maps](01_Product/P-04_Personas_and_Journey_Maps.md) | As-built draft — review pending | Product / Operations |
| P-05 | [User Workflow Specifications](01_Product/P-05_User_Workflow_Specifications.md) | As-built draft — review pending | Product / Operations |
| P-06 | [Roles and Permissions Matrix](01_Product/P-06_Roles_and_Permissions_Matrix.md) | As-built draft — review pending | Security / Product |
| P-07 | [UI UX Specification and Design System](01_Product/P-07_UI_UX_Specification_and_Design_System.md) | As-built draft — review pending | Design / Frontend |
| P-08 | [Reporting Content and Data Presentation Guide](01_Product/P-08_Reporting_Content_and_Data_Presentation_Guide.md) | As-built draft — review pending | Product / Data |
| P-09 | [Business Rules Specification](01_Product/P-09_Business_Rules_Specification.md) | As-built draft — review pending | Product / Data / Engineering |
| P-10 | [Product Roadmap and Backlog](01_Product/P-10_Product_Roadmap_and_Backlog.md) | As-built draft — review pending | Business owner / Engineering |
| P-11 | [Glossary](01_Product/P-11_Glossary.md) | As-built draft — review pending | Product / Support |
| A-01 | [Software Architecture Document](02_Architecture/A-01_Software_Architecture_Document.md) | As-built draft — review pending | Engineering / business owner |
| A-02 | [Architecture Decision Records](02_Architecture/A-02_Architecture_Decision_Records.md) | As-built draft — review pending | Engineering / business owner |
| A-03 | [Data Model ERD and Data Dictionary](02_Architecture/A-03_Data_Model_ERD_and_Data_Dictionary.md) | As-built draft — review pending | Engineering / Database |
| A-04 | [API Specification and Standards](02_Architecture/A-04_API_Specification_and_Standards.md) | As-built draft — review pending | Backend engineering |
| A-05 | [Infrastructure Architecture](02_Architecture/A-05_Infrastructure_Architecture.md) | As-built draft — review pending | Operations / Engineering |
| A-06 | [Provider Integration Specifications](02_Architecture/A-06_Provider_Integration_Specifications.md) | As-built draft — review pending | Backend / Integrations |
| A-07 | [Analytics and Reconciliation Engine Specification](02_Architecture/A-07_Analytics_and_Reconciliation_Engine_Specification.md) | As-built draft — review pending | Engineering / Data |
| A-08 | [Telephony and CRM Data Contracts](02_Architecture/A-08_Telephony_and_CRM_Data_Contracts.md) | As-built draft — review pending | Integrations / Data |
| S-01 | [Security Architecture and Threat Model](03_Security/S-01_Security_Architecture_and_Threat_Model.md) | As-built draft — review pending | Security / Engineering |
| S-02 | [Information Security Policies](03_Security/S-02_Information_Security_Policies.md) | Proposed policy — approval pending | Security / Business owner |
| S-03 | [Secure SDLC Policy](03_Security/S-03_Secure_SDLC_Policy.md) | Proposed policy — approval pending | Engineering / Security |
| S-04 | [Analytics Integrity Specification](03_Security/S-04_Analytics_Integrity_Specification.md) | As-built draft — review pending | Data / QA / Engineering |
| S-05 | [Vulnerability Management and Pen Test Plan](03_Security/S-05_Vulnerability_Management_and_Pen_Test_Plan.md) | Proposed plan — review pending | Security / QA |
| S-06 | [Incident Response Plan](03_Security/S-06_Incident_Response_Plan.md) | Proposed plan — approval pending | Operations / Security / Legal |
| C-01 | [Privacy and DPDP Compliance Assessment](04_Privacy_Compliance/C-01_Privacy_and_DPDP_Compliance_Assessment.md) | Draft — business review pending | Engineering / business owner |
| C-02 | [Internal Privacy Notice and Acceptable Use](04_Privacy_Compliance/C-02_Internal_Privacy_Notice_and_Acceptable_Use.md) | Draft — business review pending | Engineering / business owner |
| C-03 | [Processing Authorization and Consent Specification](04_Privacy_Compliance/C-03_Processing_Authorization_and_Consent_Specification.md) | Draft — business review pending | Engineering / business owner |
| C-04 | [Data Inventory Classification and Processing Register](04_Privacy_Compliance/C-04_Data_Inventory_Classification_and_Processing_Register.md) | Draft — business review pending | Engineering / business owner |
| C-05 | [Retention Deletion and Data Rights Procedure](04_Privacy_Compliance/C-05_Retention_Deletion_and_Data_Rights_Procedure.md) | Draft — business review pending | Engineering / business owner |
| C-06 | [Licensing and Intellectual Property Register](04_Privacy_Compliance/C-06_Licensing_and_Intellectual_Property_Register.md) | Draft — business review pending | Engineering / business owner |
| C-07 | [Vendors and Subprocessors Register](04_Privacy_Compliance/C-07_Vendors_and_Subprocessors_Register.md) | Draft — business review pending | Engineering / business owner |
| C-08 | [Accessibility Conformance Assessment](04_Privacy_Compliance/C-08_Accessibility_Conformance_Assessment.md) | Draft — business review pending | Engineering / business owner |
| G-01 | [Audit Logging Specification](05_Audit_Governance/G-01_Audit_Logging_Specification.md) | Draft — business review pending | Engineering / business owner |
| G-02 | [Analytics Definition and Version Governance](05_Audit_Governance/G-02_Analytics_Definition_and_Version_Governance.md) | Draft — business review pending | Engineering / business owner |
| G-03 | [Change Management Procedure](05_Audit_Governance/G-03_Change_Management_Procedure.md) | Draft — business review pending | Engineering / business owner |
| G-04 | [Access Review Procedure](05_Audit_Governance/G-04_Access_Review_Procedure.md) | Draft — business review pending | Engineering / business owner |
| Q-01 | [Test Strategy and Coverage](06_Quality_Evaluation/Q-01_Test_Strategy_and_Coverage.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| Q-02 | [User Acceptance and Signoff Plan](06_Quality_Evaluation/Q-02_User_Acceptance_and_Signoff_Plan.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| Q-03 | [Data Quality and Reconciliation Plan](06_Quality_Evaluation/Q-03_Data_Quality_and_Reconciliation_Plan.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| Q-04 | [Business KPI Framework](06_Quality_Evaluation/Q-04_Business_KPI_Framework.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| Q-05 | [Product Analytics and Telemetry Plan](06_Quality_Evaluation/Q-05_Product_Analytics_and_Telemetry_Plan.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| N-01 | [Nonfunctional Requirements and Service Objectives](07_Performance_Scaling/N-01_Nonfunctional_Requirements_and_Service_Objectives.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| N-02 | [Performance and Network Optimization Guide](07_Performance_Scaling/N-02_Performance_and_Network_Optimization_Guide.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| N-03 | [Capacity and Scaling Plan](07_Performance_Scaling/N-03_Capacity_and_Scaling_Plan.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| N-04 | [Load and Resilience Test Plan](07_Performance_Scaling/N-04_Load_and_Resilience_Test_Plan.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| D-01 | [Environment and Configuration Guide](08_DevOps_SRE/D-01_Environment_and_Configuration_Guide.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| D-02 | [Build Test and Deployment Pipeline](08_DevOps_SRE/D-02_Build_Test_and_Deployment_Pipeline.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| D-03 | [Branching Versioning and Release Procedure](08_DevOps_SRE/D-03_Branching_Versioning_and_Release_Procedure.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| D-04 | [Infrastructure as Code Assessment](08_DevOps_SRE/D-04_Infrastructure_as_Code_Assessment.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| D-05 | [Observability and Alerting Guide](08_DevOps_SRE/D-05_Observability_and_Alerting_Guide.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| D-06 | [Backup Disaster Recovery and Business Continuity](08_DevOps_SRE/D-06_Backup_Disaster_Recovery_and_Business_Continuity.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| D-07 | [Operational Runbooks](08_DevOps_SRE/D-07_Operational_Runbooks.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| D-08 | [Support Model and Service Level Proposal](08_DevOps_SRE/D-08_Support_Model_and_Service_Level_Proposal.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| L-01 | [AI Applicability and Responsible AI Assessment](02_Architecture/L-01_AI_Applicability_and_Responsible_AI_Assessment.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| U-01 | [Business User Guide and FAQ](10_User_Training/U-01_Business_User_Guide_and_FAQ.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| U-02 | [Manager and Analyst Handbook](10_User_Training/U-02_Manager_and_Analyst_Handbook.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| U-03 | [Administrator Manual](10_User_Training/U-03_Administrator_Manual.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| U-04 | [Developer Onboarding and Coding Guide](10_User_Training/U-04_Developer_Onboarding_and_Coding_Guide.md) | As-built / proposed guidance — review pending | Engineering / business owner |
| M-01 | [Project Charter and Responsibility Matrix](11_Project_Management/M-01_Project_Charter_and_Responsibility_Matrix.md) | Draft — business review pending | Engineering / business owner |
| M-02 | [Delivery Timeline and Budget Register](11_Project_Management/M-02_Delivery_Timeline_and_Budget_Register.md) | Draft — business review pending | Engineering / business owner |
| M-03 | [Risk Issue and Dependency Register](11_Project_Management/M-03_Risk_Issue_and_Dependency_Register.md) | Draft — business review pending | Engineering / business owner |
| M-04 | [Decision Log and Open Decisions](11_Project_Management/M-04_Decision_Log_and_Open_Decisions.md) | Draft — business review pending | Engineering / business owner |

63 documents across 10 categories. AI-specific lifecycle plans are assessed as not applicable in L-01 because no model feature is implemented.

## Maintenance
Edit authored content in scripts/build_documentation.py, then run `.venv/bin/python scripts/build_documentation.py` and `.venv/bin/python scripts/validate_documentation.py`. Regeneration derives routes and tables from source without opening tenant databases. Update the date and operational baseline when circumstances change.
