# Consultant Operational Readiness Review — AudioCodes AWS Deployment Guide v2.6

## Internal Technical Review Report

**Reviewer Role:** Senior Technology Consultant / Deployment Readiness Assessor
**Document Under Review:** AudioCodes SBC — Unified Deployment & Configuration Guide v2.6 (13 February 2026)
**Review Date:** 4 March 2026
**Report ID Prefix:** F-CO

---

## 1. Executive Summary

**Overall Rating:** Not Ready for Deployment — The guide serves as an excellent design reference but is insufficient as a deployment-ready artefact. Critical operational documentation (runbooks, SOPs, monitoring specifications, training plans, RACI matrix) is entirely absent.

The document excels at describing *what* the architecture looks like and *why* design decisions were made. It falls short at describing *how* to deploy, operate, and maintain the solution day-to-day. An implementation team receiving this document would understand the architecture but would be unable to: execute a deployment without significant additional preparation, respond to incidents, perform routine maintenance, or hand off to an operations team.

**Top 3 Findings:**

1. **F-CO-001 (Critical):** No operational runbooks or standard operating procedures — zero defined procedures for routine operations, maintenance, or incident response.
2. **F-CO-005 (Critical):** No monitoring and alerting specification — the guide defines no CloudWatch alarms, no OVOC alert thresholds, no SNMP trap responses, and no escalation paths.
3. **F-CO-007 (High):** No RACI matrix or operational responsibility model — unclear who owns Day 2 operations across voice, cloud, security, and vendor teams.

**Go/No-Go Recommendation:** No-Go for deployment as-is. The guide must be supplemented with an Operations Handbook covering runbooks, monitoring, alerting, incident response, and training before the solution can be deployed into production.

---

## 2. Scope of Review

### Sections Examined

| Section | Title | Operational Focus |
|---------|-------|-------------------|
| 1 | Executive Summary | Scope definition, deployment context |
| 9 | SBC Provisioning | Deployment prerequisites, HA provisioning |
| 10 | Security Controls | Administrative procedures, hardening |
| 17 | Break Glass Accounts | Emergency access procedures |
| 18 | Deployment Methodology | Deployment sequence, methods |
| 19 | High Availability Considerations | Failover procedures, operational impact |
| 20 | IAM Permissions and Security | Temporal elevation procedure |
| 21 | Cyber Security Considerations | Approval checklist, risk assessment |
| 22 | Licensing Considerations | Licensing management |
| 22A | OVOC Data Analytics | ETL operations, monitoring requirements |
| Appendix A | Deployment Checklist | Pre-deployment verification |
| Appendix B | Credentials Reference Template | Credential management |
| Document Control | Version History | Document maturity assessment |
| All Sections | Full document | Operational readiness gap assessment |

### Methodology

- Assessment against the ITIL 4 Service Transition and Service Operation frameworks
- Evaluation of operational readiness across: People, Process, Technology, and Documentation dimensions
- Gap analysis against typical enterprise voice platform deployment requirements
- Review of deployment risk factors including document maturity, team readiness, and operational handoff readiness

### Reference Standards

- ITIL 4 — Service Transition, Service Operation
- ISO 20000-1 — IT Service Management
- AWS Operational Excellence Pillar — Well-Architected Framework
- Microsoft Teams Direct Routing Operations Guide

---

## 3. Strengths Identified

1. **Break Glass Account Procedures (Section 17):** The break glass account documentation is comprehensive and operationally mature. It specifies: naming conventions, password policies (20+ characters, complex), storage requirements, dual-control access, incident ticket requirements, post-use password rotation, and a quarterly/semi-annual review schedule. The account inventory covers all 14 production accounts across both regions with clear secret repository paths.

2. **Deployment Checklist (Appendix A):** The pre-deployment checklist provides a structured verification sequence covering AWS readiness, Entra ID configuration, break glass accounts, component deployment, and integration verification. The checklist format (checkbox items) supports systematic tracking.

3. **Credentials Reference Template (Appendix B):** The separation of credential references from actual credentials, with clear secret repository paths and an explicit note ("Never store actual credentials in this document"), demonstrates security-aware operational documentation.

4. **Temporal IAM Elevation Procedure (Section 20):** The recommended procedure for attaching/detaching the Stack Manager IAM policy during operations shows operational maturity. Three implementation options (IAM policy toggle, SCP, automation) provide flexibility.

5. **OVOC ETL Monitoring Requirement (Section 22A):** The guide correctly identifies ETL job monitoring as critical: "Monitor for failed ETL extractions. A missed extraction means that day's data is permanently lost." This operational awareness is valuable even though the ETL pipeline itself is undefined.

6. **Voice Recording Decision Matrix (Section 19):** The structured comparison of five voice recording options with pros/cons, cost, complexity, and security approval likelihood provides excellent decision-support documentation for stakeholders.

---

## 4. Detailed Findings

### F-CO-001: No Operational Runbooks or Standard Operating Procedures

| Attribute | Detail |
|-----------|--------|
| **Severity** | Critical |
| **Category** | Operational Readiness / Process |
| **Guide Reference** | Entire document (absent) |
| **Description** | The guide contains no runbooks or SOPs for any routine operational task. The following operational procedures are entirely absent: SBC firmware upgrade procedure, SBC configuration backup and restore, HA failover testing procedure, Stack Manager Day 2 operations (referenced in Section 4 but no procedures provided), OVOC maintenance and upgrade, ARM Configurator/Router maintenance, Certificate renewal procedure (certificates expire — renewal is not addressed), RADIUS shared secret rotation, Client secret rotation for Entra ID app registrations, VPC Endpoint health verification, ETL pipeline failure recovery, Break glass account testing procedure (Section 17 states "Annually: Full break glass procedure test" but provides no test script). |
| **Risk / Impact** | Operations teams cannot perform routine maintenance without developing their own procedures. Each maintenance window becomes a research exercise. Inconsistent procedures across team members introduce configuration drift and operational risk. Knowledge is trapped in individual engineers rather than documented processes. |
| **Evidence** | Search for "runbook", "SOP", "procedure", "step-by-step", "how to" in operational context returns zero results. Section 4 mentions "Day 2 Operations: software updates, stack healing, configuration changes" but provides no procedures. |
| **Recommendation** | Develop an Operations Handbook containing runbooks for each routine operational task. At minimum, create runbooks for: (1) SBC firmware upgrade (via Stack Manager), (2) HA failover test, (3) Certificate renewal, (4) Break glass account test, (5) RADIUS shared secret rotation, (6) Entra ID client secret renewal, (7) OVOC backup and restore, (8) Configuration backup and restore, (9) ETL pipeline failure recovery, (10) Stack Manager IAM elevation procedure. |
| **Priority** | Immediate |

---

### F-CO-002: Document Length and Structure Inappropriate for Operational Use

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Document Usability |
| **Guide Reference** | Entire document (3,559 lines) |
| **Description** | At 3,559 lines, the document attempts to serve as both a design document and a deployment guide. It combines architectural decisions, component specifications, detailed SBC configuration tables, firewall rules, security analysis, licensing information, and deployment methodology in a single file. This makes it difficult for any single role (voice engineer, cloud engineer, security analyst, operations) to find relevant information quickly. The document has no audience-based navigation or role-specific reading paths. |
| **Risk / Impact** | During an incident or urgent maintenance window, engineers cannot quickly locate the relevant configuration or procedure. The document's length discourages reading and increases the likelihood that critical information is missed. Different teams will read different parts, creating knowledge silos. |
| **Evidence** | 3,559 lines, 23 sections plus 4 appendices, 26 diagrams. Single markdown file with no audience-based navigation. Table of Contents (lines 12–41) lists all sections linearly without role-based grouping. |
| **Recommendation** | Restructure the documentation into a documentation suite: (1) Architecture Design Document (Sections 1–5, 19, 21 — for architects and reviewers), (2) SBC Configuration Guide (Sections 9–16 — for voice engineers), (3) Deployment Runbook (Section 18 + Appendix A — for implementation engineers), (4) Operations Handbook (new — for operations teams), (5) Security Controls Document (Sections 10, 17, 20, 21 — for security teams), (6) Quick Reference Card (Appendix C — for all roles). At minimum, add role-based reading guides at the top of the document. |
| **Priority** | Post-Deployment |

---

### F-CO-003: No Troubleshooting Guide

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Category** | Operational Readiness / Supportability |
| **Guide Reference** | Entire document (absent) |
| **Description** | The guide contains no troubleshooting section covering common failure scenarios, diagnostic commands, log locations, or resolution procedures. Voice infrastructure troubleshooting requires specific knowledge of SBC debug tools, SIP trace analysis, RTP media analysis, and AudioCodes-specific CLI commands that are not documented. |
| **Risk / Impact** | When call quality issues or service disruptions occur, operations teams must rely on vendor support or individual engineer knowledge. Mean Time to Resolution (MTTR) increases significantly without documented troubleshooting procedures. Voice outages have immediate business impact (calls cannot be made or received). |
| **Evidence** | No section titled "Troubleshooting", "Diagnostics", or "Common Issues." No mention of AudioCodes debug commands (e.g., `debug sip`, `show sip sessions`, `show ha status`), SIP trace analysis, pcap capture, syslog analysis procedures, or OVOC diagnostic features. |
| **Recommendation** | Create a Troubleshooting Guide covering: (1) Common failure scenarios (one-way audio, no audio, call drops, registration failures, HA failover failures, Teams connectivity loss), (2) Diagnostic commands (AudioCodes CLI, AWS CLI, SIP trace), (3) Log locations and analysis (SBC syslog, OVOC logs, CloudTrail, VPC Flow Logs), (4) Escalation matrix (when to escalate to AudioCodes TAC, Microsoft support, AWS support), (5) Health check procedures (SIP OPTIONS verification, SNMP polling, CloudWatch metrics). |
| **Priority** | Pre-Go-Live |

---

### F-CO-004: No Training Plan or Knowledge Transfer Strategy

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Category** | People / Knowledge Management |
| **Guide Reference** | Entire document (absent) |
| **Description** | The guide does not define any training requirements, knowledge transfer plan, or competency assessment for the teams who will deploy and operate the solution. The architecture spans multiple technology domains (AudioCodes SBC administration, AWS cloud infrastructure, Microsoft Teams administration, Cisco ISE RADIUS configuration, voice engineering) requiring cross-functional expertise that may not exist within the organisation. |
| **Risk / Impact** | Without trained personnel, the organisation depends on the original design team or vendor professional services for all operational activities. Staff turnover creates knowledge loss risk. The break glass procedures (Section 17) assume trained personnel are available — but the guide does not define what "trained" means. |
| **Evidence** | No mention of "training", "knowledge transfer", "certification", "competency", or "skills" in the document. No training prerequisites listed in Appendix A Deployment Checklist. |
| **Recommendation** | Develop a Training and Knowledge Transfer Plan: (1) Required certifications/training per role (AudioCodes SBC administration, AWS Solutions Architect, Teams Administrator), (2) Vendor training schedule (AudioCodes professional services, Microsoft FastTrack), (3) Knowledge transfer sessions from design team to operations team, (4) Competency assessment criteria (hands-on lab exercises covering common operational tasks), (5) Ongoing training schedule (annual refresher, post-upgrade training). |
| **Priority** | Pre-Go-Live |

---

### F-CO-005: No Monitoring and Alerting Specification

| Attribute | Detail |
|-----------|--------|
| **Severity** | Critical |
| **Category** | Operational Readiness / Monitoring |
| **Guide Reference** | Sections 19, 20, 21, 22A |
| **Description** | Despite deploying a production voice platform across two regions with 9 VMs, the guide defines no monitoring or alerting specification. Section 20 grants CloudWatch alarm permissions (`cloudwatch:PutMetricAlarm`) but defines no alarms. Section 21 mentions CloudTrail logging but no operational alerting. OVOC provides native monitoring capabilities, but no SNMP trap thresholds, syslog alert rules, or QoE alarm thresholds are specified. The Appendix A checklist includes "Monitoring and alerting configured" as a checkbox but provides no specification for what to monitor or alert on. |
| **Risk / Impact** | Without defined monitoring, the operations team cannot proactively detect: SBC resource exhaustion (CPU, memory, session count approaching limits), HA failover events, certificate expiry approaching, RADIUS server unreachable, NTP synchronisation loss, call quality degradation (MOS below threshold), trunk registration failures, or ETL pipeline failures. Issues will be detected reactively — typically by end users reporting call problems. |
| **Evidence** | Section 20: `cloudwatch:PutMetricAlarm` permission but no alarm definitions. Appendix A: "Monitoring and alerting configured" checkbox with no specification. Section 22A: "Configure alerting on ETL job failures" — no alert definition provided. |
| **Recommendation** | Define a comprehensive Monitoring and Alerting Specification covering: (1) AWS CloudWatch alarms: EC2 instance status checks, CPU utilisation, EBS IOPS, network throughput per SBC/OVOC/ARM/Stack Manager, (2) OVOC alerts: SBC unreachable, QoE MOS below threshold (e.g., < 3.5), alarm count spike, CDR ingestion failure, (3) SBC alerts: HA failover event (immediate page), registration failure, certificate expiry < 30 days, session count > 80% capacity, (4) Infrastructure alerts: NAT Gateway health, VPC Endpoint health, Direct Connect status, (5) ETL pipeline alerts: extraction failure, zero-row extraction, latency exceeding window, (6) Escalation paths: L1 → L2 → L3 → vendor for each alert category. |
| **Priority** | Immediate |

---

### F-CO-006: No SLA or KPI Definitions

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Service Management |
| **Guide Reference** | Entire document (absent) |
| **Description** | The guide defines no Service Level Agreements (SLAs), Key Performance Indicators (KPIs), or Service Level Objectives (SLOs) for the voice platform. There are no targets for: availability (e.g., 99.99%), call setup success rate, call quality (MOS), HA failover time, Mean Time to Recovery (MTTR), or capacity utilisation thresholds. |
| **Risk / Impact** | Without defined SLAs/KPIs, there is no objective measure of whether the platform is performing adequately. Operations teams cannot prioritise issues, management cannot assess platform health, and vendor performance cannot be measured. Contractual SLAs with the SIP providers and Microsoft cannot be validated against the platform's own performance. |
| **Evidence** | No mention of "SLA", "KPI", "SLO", "availability target", "uptime", or "service level" in the document. Section 19 describes HA failover behaviour but defines no failover time target. |
| **Recommendation** | Define platform SLAs and KPIs: (1) Availability target: 99.99% for voice service (translates to ~52 minutes downtime per year), (2) Call Setup Success Rate: > 99.5%, (3) Call Quality: MOS > 3.5 for 95% of calls, (4) HA Failover Time: < 30 seconds, (5) MTTR targets: P1 < 1 hour, P2 < 4 hours, P3 < 24 hours, (6) Capacity thresholds: Alert at 70%, action at 80%, refuse at 90% of licensed sessions, (7) Certificate renewal: > 30 days before expiry. |
| **Priority** | Pre-Go-Live |

---

### F-CO-007: No RACI Matrix or Operational Responsibility Model

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Category** | Governance / Accountability |
| **Guide Reference** | Entire document (absent) |
| **Description** | The guide does not define who is responsible for operating each component of the solution. The architecture spans multiple teams: Voice Engineering (SBC configuration, routing), Cloud Engineering (AWS infrastructure, IAM, VPC), Security (firewall rules, IAM policies, certificate management), Microsoft 365 Administration (Teams policies, app registrations), Network Engineering (Direct Connect, east-west firewall), and Vendor Management (AudioCodes licensing, support). Without a RACI matrix, responsibility boundaries are undefined. |
| **Risk / Impact** | Undefined responsibilities lead to: tasks falling between teams ("I thought they were doing that"), duplicate effort, delays in incident response, and lack of accountability for ongoing maintenance (certificate renewals, password rotations, patching). |
| **Evidence** | No RACI matrix, no responsibility model, no operational ownership table. Section 17 mentions "Two authorized personnel required to retrieve credentials" but does not define who those personnel are or which team they belong to. |
| **Recommendation** | Create a RACI matrix covering all operational activities: SBC patching (Voice Eng), AWS infrastructure changes (Cloud Eng), certificate renewal (Security + Voice Eng), IAM policy management (Cloud Eng + Security), Entra ID app registration management (M365 Admin), firewall rule changes (Network + Security), OVOC management (Voice Eng), break glass account management (Security), SIP provider liaison (Voice Eng + Vendor Mgmt), licensing renewal (Vendor Mgmt + Procurement). |
| **Priority** | Pre-Go-Live |

---

### F-CO-008: No Bill of Materials or Cost Estimate

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Commercial / Planning |
| **Guide Reference** | Sections 4, 22 |
| **Description** | The guide specifies instance types and licensing requirements but provides no bill of materials (BOM) or cost estimate. There is no summary of: AWS compute costs (9 production VMs across 2 regions), EBS storage costs (including OVOC's 2TB gp3), VPC Endpoint costs (~$73/month per region as noted in Section 21), data transfer costs (cross-region, internet egress), AudioCodes licensing costs (SBC BYOL/PAYG, ARM, OVOC, Analytics API), TLS certificate costs, Cisco ISE licensing impact, or professional services costs. |
| **Risk / Impact** | Without a BOM, project budgeting is incomplete. Ongoing operational costs (AWS monthly, licensing renewals, certificate renewals) cannot be forecast. Cost optimisation opportunities (Reserved Instances, Savings Plans, right-sizing) are not identified. |
| **Evidence** | Section 4: Instance types listed. Section 22: Licensing types described qualitatively. Section 21: VPC Endpoint cost ~$73/month per region. No consolidated BOM or cost estimate. |
| **Recommendation** | Create a Bill of Materials with: (1) AWS monthly cost estimate per component (compute, storage, data transfer, VPC Endpoints), (2) AudioCodes licensing cost breakdown (one-time + annual maintenance), (3) Third-party costs (TLS certificates, Cisco ISE licences), (4) Professional services estimate (AudioCodes deployment assistance, Microsoft FastTrack), (5) Annual Total Cost of Ownership (TCO), (6) Cost optimisation recommendations (Reserved Instances for stable workloads). |
| **Priority** | Immediate |

---

### F-CO-009: No Incident Response Procedure for Voice Infrastructure

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Category** | Operational Readiness / Incident Management |
| **Guide Reference** | Sections 17, 19 (partial) |
| **Description** | The guide describes HA failover behaviour (Section 19) and break glass access (Section 17) but does not define incident response procedures for voice service incidents. There is no severity classification specific to voice (P1: total voice outage, P2: degraded quality, P3: single site affected), no escalation matrix, no communication plan, and no war room procedure. |
| **Risk / Impact** | When a voice outage occurs, the incident response is ad-hoc. Without defined severity levels and escalation paths, critical incidents may not receive appropriate urgency. Communication to business stakeholders is inconsistent. Recovery actions depend on individual engineer knowledge rather than documented procedures. |
| **Evidence** | Section 17 defines break glass access but not incident response. Section 19 describes failover but not incident management. No mention of "incident response", "severity", "escalation", "war room", or "incident commander." |
| **Recommendation** | Develop a Voice Platform Incident Response Plan: (1) Severity classification (P1–P4 with voice-specific criteria), (2) Escalation matrix (L1 → Voice Eng → AudioCodes TAC → Microsoft, with timeframes), (3) Communication plan (stakeholder notification templates, status page updates), (4) Diagnostic checklist per severity level, (5) Recovery procedures (referencing runbooks from F-CO-001), (6) Post-incident review process, (7) Integration with organisational ITSM tool. |
| **Priority** | Pre-Go-Live |

---

### F-CO-010: Password Rotation Procedures Lack Automation

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Security Operations |
| **Guide Reference** | Section 17 (Break Glass), Section 10.4 (RADIUS), Section 6 (Entra ID) |
| **Description** | The guide defines several password rotation requirements but provides no automation: (1) Break glass passwords — semi-annual rotation plus after each use (Section 17), (2) RADIUS shared secrets — "Use unique shared secrets per SBC or per site" (Section 10.4), (3) Entra ID client secrets — "24 months with calendar reminder" (Section 6), (4) SBC local passwords — "configure password validity period" (Section 10.3). All of these are manual processes dependent on human memory or calendar reminders. |
| **Risk / Impact** | Manual password rotation is error-prone and frequently missed. Expired Entra ID client secrets will cause OVOC and ARM authentication failures with no warning until the service breaks. RADIUS shared secrets that are never rotated become a persistent attack vector. Calendar-based reminders are unreliable when the person who set them leaves the organisation. |
| **Evidence** | Section 6: "Expiry: Select appropriate expiry (recommend 24 months with calendar reminder)". Section 17: "Semi-Annually: Rotate all break glass passwords" — manual schedule. Section 10.4: No rotation schedule defined for RADIUS shared secrets. |
| **Recommendation** | Implement automated credential management: (1) Entra ID client secrets: Use Azure Key Vault with automated rotation or implement a monitoring alert when secrets are within 60 days of expiry, (2) Break glass passwords: Integrate with a Privileged Access Management (PAM) solution that enforces rotation schedules, (3) RADIUS shared secrets: Define rotation schedule (annual) and procedure, (4) TLS certificates: Implement certificate expiry monitoring with 60/30/7-day alerts, (5) SBC local passwords: Define rotation schedule and document the procedure. |
| **Priority** | Pre-Go-Live |

---

### F-CO-011: Deployment Checklist Lacks Sequencing and Dependencies

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Deployment Planning |
| **Guide Reference** | Appendix A (Deployment Checklist), Section 18 (Deployment Methodology) |
| **Description** | The deployment checklist (Appendix A) contains 29 checkbox items across 4 categories (Pre-Deployment, Entra ID, Break Glass, Component Deployment, Integration Verification) but does not indicate sequencing, dependencies, or estimated duration for each item. Section 18 shows an 8-phase deployment sequence diagram but the relationship between the diagram and the checklist is not established. Some checklist items have implicit dependencies (e.g., "SBC HA failover tested" depends on "SBC HA pair deployed") but these are not explicit. |
| **Risk / Impact** | Implementation engineers may execute checklist items out of order, causing failures (e.g., deploying SBCs before Stack Manager, configuring OAuth before app registrations). Without duration estimates, project scheduling is guesswork. |
| **Evidence** | Appendix A: 29 items with no sequence numbers, no dependency arrows, no duration estimates. Section 18: 8-phase diagram but no mapping to Appendix A items. |
| **Recommendation** | Enhance the deployment checklist with: (1) Explicit sequencing (numbered steps within each phase), (2) Dependencies (prerequisite items clearly identified), (3) Estimated duration per item or phase, (4) Responsible role per item, (5) Verification criteria (how to confirm each item is complete), (6) Map each item to the Section 18 deployment phase. |
| **Priority** | Immediate |

---

### F-CO-012: No Change Management Process Defined

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Governance / Change Management |
| **Guide Reference** | Section 20 (temporal IAM elevation mentions change management) |
| **Description** | Section 20 states: "Ensure the temporal elevation process is documented in the organisation's change management procedures." This is the only reference to change management in the entire document. No change management process is defined for: SBC configuration changes, routing rule updates, firewall rule modifications, security group changes, firmware upgrades, or certificate deployments. |
| **Risk / Impact** | Voice infrastructure changes without a change management process risk unplanned outages. Configuration changes applied during business hours can drop active calls. Changes without rollback plans and testing create service disruption risk. |
| **Evidence** | Single reference to change management in Section 20. No change advisory board (CAB) process, no change classification (standard/normal/emergency), no maintenance window definition, no change testing requirements. |
| **Recommendation** | Define change management procedures for voice infrastructure: (1) Change classification (standard: pre-approved low-risk changes; normal: require CAB review; emergency: break-fix during outage), (2) Maintenance window schedule (e.g., Sundays 02:00–06:00 AEST), (3) Change testing requirements (non-prod testing before production), (4) Rollback criteria and procedures, (5) Post-change verification procedures, (6) Change notification process for affected users. |
| **Priority** | Pre-Go-Live |

---

### F-CO-013: No Vendor Support and Escalation Model

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Support / Vendor Management |
| **Guide Reference** | Section 23 (References — product links only) |
| **Description** | The guide provides AudioCodes product page links and documentation URLs (Section 23) but does not document: AudioCodes support contract details, TAC (Technical Assistance Centre) contact procedures, case severity levels and response time SLAs, escalation procedures to AudioCodes engineering, Microsoft support escalation for Teams Direct Routing issues, AWS support plan and escalation, or SIP provider support contacts and escalation. |
| **Risk / Impact** | During a critical voice outage, operations teams waste time finding support contact information, determining appropriate severity levels, and navigating vendor support processes. This delays MTTR and extends the business impact of outages. |
| **Evidence** | Section 23: Documentation links only. No support contract references, no TAC contact information, no SLA definitions, no escalation matrix. |
| **Recommendation** | Create a Vendor Support Reference document: (1) AudioCodes TAC: contact method, case submission process, severity definitions, response time SLAs, escalation contacts, (2) Microsoft: Teams Direct Routing support process, case submission via M365 Admin Centre, escalation path, (3) AWS: Support plan level, case submission process, severity definitions, (4) SIP Providers (AU and US): technical support contacts, escalation matrix, SLA for trunk issues, (5) Cisco ISE: support contacts for RADIUS authentication issues. |
| **Priority** | Pre-Go-Live |

---

### F-CO-014: No Capacity Management Process

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Operational Readiness / Capacity |
| **Guide Reference** | Sections 4, 13.2 |
| **Description** | The guide defines initial capacity (instance types, Media Realm session legs) but establishes no ongoing capacity management process. There are no capacity thresholds, no growth forecasting methodology, no periodic capacity review schedule, and no capacity reporting requirements. The OVOC QoE data could be used for capacity trending but this use case is not documented. |
| **Risk / Impact** | Without capacity management, the platform may gradually approach capacity limits without detection. Call quality degrades before call failures occur — users experience poor quality before the operations team is aware of a capacity issue. SBC session licensing requires lead time to procure — discovering a capacity shortfall during a peak period leaves no time to procure additional licences. |
| **Evidence** | Section 4: Instance types and session counts defined. Section 13.2: Media Realm session legs allocated. No capacity management process, thresholds, or review schedule defined. |
| **Recommendation** | Define a capacity management process: (1) Monthly capacity reporting (concurrent session peaks, CPU/memory utilisation trends, media port utilisation), (2) Capacity thresholds (70% alert, 80% action, 90% critical), (3) Quarterly capacity review meeting, (4) Annual capacity forecast aligned with business growth projections, (5) Lead time awareness (licensing procurement lead time, AWS instance change procedure). |
| **Priority** | Post-Deployment |

---

### F-CO-015: 14 Revisions in 8 Days — Design Stability Concern

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Deployment Risk / Document Maturity |
| **Guide Reference** | Document Control (lines 3535–3556) |
| **Description** | The version history shows 14 revisions between 5 February and 13 February 2026. Major architectural changes occurred on the same day: v2.0 (4-ENI to 3-ENI consolidation), v2.1 (LDAPS to replace Entra ID for SBCs), v2.3 (LDAPS replaced by RADIUS). The authentication model changed three times in three days (Entra ID → LDAPS → RADIUS). This pace suggests the design was being evolved through the documentation process rather than documented from a stable design. |
| **Risk / Impact** | From a deployment readiness perspective, the rapid design evolution raises the question: has the design stabilised? Are there further changes pending? Implementation against a design that is still evolving wastes effort and creates rework risk. The rapid revision pace also increases the risk of internal inconsistencies within the document. |
| **Evidence** | Document Control: 14 versions, 8 days. Authentication model changed 3 times: v1.2 (Entra ID), v2.1 (LDAPS), v2.3 (RADIUS). Interface model changed: v1.8 (4-ENI), v2.0 (3-ENI), v2.5 (interface remapping). |
| **Recommendation** | Obtain formal stakeholder sign-off confirming the v2.6 design is stable and no further architectural changes are anticipated. Conduct a design freeze: any changes after sign-off must go through a formal change request process. The design freeze should be a prerequisite for implementation commencement. |
| **Priority** | Immediate |

---

## 5. Risk Matrix

| Finding ID | Title | Severity | Likelihood | Impact | Risk Rating |
|------------|-------|----------|------------|--------|-------------|
| F-CO-001 | No operational runbooks/SOPs | Critical | High | Critical | Critical |
| F-CO-002 | Document too long for operational use | Medium | High | Medium | Medium |
| F-CO-003 | No troubleshooting guide | High | High | High | Critical |
| F-CO-004 | No training plan | High | High | High | Critical |
| F-CO-005 | No monitoring/alerting specification | Critical | High | Critical | Critical |
| F-CO-006 | No SLA/KPI definitions | Medium | Medium | Medium | Medium |
| F-CO-007 | No RACI matrix | High | High | High | Critical |
| F-CO-008 | No bill of materials | Medium | Medium | Medium | Medium |
| F-CO-009 | No incident response procedure | High | Medium | High | High |
| F-CO-010 | Password rotation lacks automation | Medium | High | Medium | High |
| F-CO-011 | Checklist lacks sequencing | Medium | Medium | Medium | Medium |
| F-CO-012 | No change management process | Medium | Medium | High | High |
| F-CO-013 | No vendor support model | Medium | Medium | Medium | Medium |
| F-CO-014 | No capacity management process | Medium | Medium | Medium | Medium |
| F-CO-015 | 14 revisions in 8 days | Medium | Medium | Medium | Medium |

---

## 6. Gap Analysis

| Operational Domain | Guide Coverage | Gap |
|-------------------|----------------|-----|
| Runbooks / SOPs | Not present | Full runbook suite for all operational tasks |
| Monitoring & Alerting | Permissions granted, no specification | Complete monitoring spec with thresholds and alerts |
| Incident Response | Break glass only | Voice-specific incident response procedure |
| Troubleshooting | Not present | Diagnostic guide with common scenarios and commands |
| Training | Not present | Training plan, competency framework, knowledge transfer |
| RACI / Ownership | Not present | Operational responsibility matrix across all teams |
| Change Management | Mentioned once | Full change management process for voice infrastructure |
| Capacity Management | Initial sizing only | Ongoing capacity review process and thresholds |
| SLA / KPI | Not present | Service level definitions and performance targets |
| Vendor Support | Product links only | Support contract details, escalation matrix |
| Bill of Materials | Instance types only | Full cost estimate with TCO |
| Certificate Management | Deployment steps only | Renewal procedures, expiry monitoring |
| Document Structure | Single large document | Role-based documentation suite |
| Deployment Sequencing | Phase diagram + flat checklist | Sequenced, dependent, estimated checklist |
| Design Stability | 14 revisions in 8 days | Design freeze and stakeholder sign-off |

---

## 7. Recommendations Summary

### Immediate (Before Implementation Starts)

1. Develop operational runbooks for top 10 procedures (F-CO-001)
2. Define monitoring and alerting specification (F-CO-005)
3. Create RACI matrix for all operational activities (F-CO-007)
4. Create bill of materials with cost estimate (F-CO-008)
5. Sequence deployment checklist with dependencies (F-CO-011)
6. Obtain design freeze sign-off (F-CO-015)

### Pre-Go-Live (Before Production Deployment)

7. Create troubleshooting guide (F-CO-003)
8. Develop and execute training plan (F-CO-004)
9. Define SLA/KPI targets (F-CO-006)
10. Develop incident response procedure (F-CO-009)
11. Implement credential expiry monitoring (F-CO-010)
12. Define change management process (F-CO-012)
13. Document vendor support and escalation model (F-CO-013)

### Post-Deployment (Operational Maturity)

14. Restructure documentation into role-based suite (F-CO-002)
15. Implement capacity management process (F-CO-014)
16. Conduct first operational readiness review (30 days post go-live)
17. Schedule recurring operational maturity assessments (quarterly)

---

## 8. Action Items Register

| # | Action | Owner | Priority | Target Date | Status |
|---|--------|-------|----------|-------------|--------|
| 1 | Develop operational runbooks (top 10 procedures) | Voice Engineering + Cloud Engineering | Critical | Before implementation | Open |
| 2 | Define monitoring and alerting specification | Voice Engineering + Cloud Engineering | Critical | Before implementation | Open |
| 3 | Create RACI matrix | Project Manager + all team leads | Critical | Before implementation | Open |
| 4 | Create bill of materials | Project Manager + Finance | High | Immediate | Open |
| 5 | Sequence deployment checklist | Voice Engineering + Project Manager | High | Immediate | Open |
| 6 | Obtain design freeze sign-off | Solution Architect + Stakeholders | High | Immediate | Open |
| 7 | Create troubleshooting guide | Voice Engineering | High | Pre-go-live | Open |
| 8 | Develop and execute training plan | Project Manager + Vendor | High | Pre-go-live | Open |
| 9 | Define SLA/KPI targets | Service Management + Voice Engineering | Medium | Pre-go-live | Open |
| 10 | Develop incident response procedure | Voice Engineering + Service Management | High | Pre-go-live | Open |
| 11 | Implement credential expiry monitoring | Security + Cloud Engineering | High | Pre-go-live | Open |
| 12 | Define change management process | Service Management | Medium | Pre-go-live | Open |
| 13 | Document vendor support model | Vendor Management | Medium | Pre-go-live | Open |
| 14 | Restructure into documentation suite | Technical Writer | Low | Post-go-live | Open |
| 15 | Implement capacity management process | Voice Engineering + Service Management | Medium | Post-go-live (30 days) | Open |

---

## 9. Appendix: Sections Reviewed

| Section | Lines | Operational Focus |
|---------|-------|-------------------|
| 1. Executive Summary | 45–76 | Deployment scope and context |
| 9. SBC Provisioning | 801–946 | Deployment prerequisites (operational dependencies) |
| 10. Security Controls | 949–1097 | Administrative procedures, hardening, RADIUS config |
| 17. Break Glass Accounts | 2116–2203 | Emergency access procedures, rotation schedule |
| 18. Deployment Methodology | 2205–2221 | Deployment sequence and methods |
| 19. HA Considerations | 2223–2468 | Failover operational impact, voice recording options |
| 20. IAM Permissions | 2476–2605 | Temporal elevation procedure |
| 21. Cyber Security | 2608–2843 | Approval checklist, risk assessment |
| 22. Licensing | 2846–2875 | Licensing management requirements |
| 22A. OVOC Analytics | 2877–3156 | ETL operations, monitoring, audit requirements |
| Appendix A | 3219–3277 | Deployment checklist |
| Appendix B | 3281–3311 | Credentials management template |
| Document Control | 3535–3556 | Version history, revision pace |

---

## 10. Appendix: Standards and References

| Standard / Reference | Relevance |
|---------------------|-----------|
| ITIL 4 — Service Transition | Deployment readiness, knowledge transfer, release management |
| ITIL 4 — Service Operation | Incident management, problem management, event management |
| ISO 20000-1 — IT Service Management | Service level management, capacity management, change management |
| AWS Well-Architected — Operational Excellence | Operational procedures, monitoring, incident response |
| COBIT 2019 — IT Governance | RACI matrices, accountability frameworks |
| AudioCodes Mediant VE SBC Administrator's Guide | Operational commands and procedures reference |
| Microsoft Teams Direct Routing Operations Guide | Teams-specific operational guidance |
| Cisco ISE Administration Guide | RADIUS server operational procedures |
| PMI PMBOK — Project Management | Deployment planning, stakeholder management |
| NIST SP 800-53 — Security Controls | Incident response, audit logging, change management |

---

*End of Consultant Operational Readiness Review Report*
