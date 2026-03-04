# Solution Architect Review — AudioCodes AWS Deployment Guide v2.6

## Internal Technical Review Report

**Reviewer Role:** Senior Solution Architect / Enterprise Architect
**Document Under Review:** AudioCodes SBC — Unified Deployment & Configuration Guide v2.6 (13 February 2026)
**Review Date:** 4 March 2026
**Report ID Prefix:** F-SA

---

## 1. Executive Summary

**Overall Rating:** Adequate with Reservations — The architecture is well-articulated for the primary use case (Microsoft Teams Direct Routing with HA SBCs in AWS) but contains several single points of failure, deep vendor lock-in, and significant scalability constraints that should be acknowledged and accepted before proceeding.

The guide demonstrates strong work in network segmentation, HA failover mechanics, and security group design. However, the architecture concentrates critical management functions (Stack Manager, ARM Configurator, OVOC) as single instances with no high availability, creating operational risk. The volume of configuration deferred to "implementation time" is unusually high for a document at version 2.6, suggesting design maturity is lower than the version number implies.

**Top 3 Findings:**

1. **F-SA-001 (High):** ARM Configurator is a single instance with no HA — its failure disables routing policy changes across all regions.
2. **F-SA-005 (High):** US region has no OVOC, ARM Configurator, or Stack Manager — complete dependency on Australian region for management and monitoring.
3. **F-SA-007 (Critical):** Excessive deferral of configuration to "implementation time" — at least 15 distinct configuration areas are undefined, undermining the document's utility as a deployment guide.

**Go/No-Go Recommendation:** Conditional Go — proceed with explicit acknowledgement and risk acceptance of the single-instance management components and cross-region dependency. Develop a supplementary Architecture Decision Register documenting each accepted risk.

---

## 2. Scope of Review

### Sections Examined

| Section | Title | Architectural Focus |
|---------|-------|---------------------|
| 1 | Executive Summary | Scope, constraints, key takeaways |
| 2 | Critical Findings | HA mechanism, API access |
| 3 | Architecture Overview | Topology, VM counts, region layout |
| 4 | Component Specifications | Sizing, instance types, dependencies |
| 5 | AWS Infrastructure Requirements | VPC, subnets, security groups, publishing patterns |
| 9 | SBC Provisioning | HA deployment model, provisioning dependencies |
| 18 | Deployment Methodology | Deployment sequence and methods |
| 19 | High Availability Considerations | HA scope, failover, ARM HA, voice recording |
| 20 | IAM Permissions and Security | IAM policies, VPC endpoints |
| 21 | Cyber Security Considerations | Security architecture, risk assessment |
| 22 | Licensing Considerations | Licensing model dependencies |
| 22A | OVOC Data Analytics | Data retention, ETL architecture |
| Document Control | Version history | Document maturity and evolution |

### Methodology

- End-to-end architecture review assessing coherence, resilience, scalability, and future-proofing
- Single-point-of-failure analysis across all components
- Cross-region dependency mapping
- Vendor lock-in assessment
- Configuration completeness audit

### Reference Standards

- AWS Well-Architected Framework (Reliability, Operational Excellence, Security, Cost Optimisation pillars)
- TOGAF Architecture Decision Records
- ISO/IEC 25010 — Systems and software quality

---

## 3. Strengths Identified

1. **HA Failover Mechanism Design (Sections 2, 19):** The SBC HA architecture is well-designed. The decision for SBCs to directly call AWS APIs for route table manipulation during failover (rather than relying on Stack Manager) eliminates a critical dependency. The HA mechanism is clearly documented with a step-by-step failover sequence (Section 19), prerequisite checklist, and detailed VIP/EIP handling.

2. **Dual External Publishing Patterns (Section 5):** The architecture correctly distinguishes between SBC external publishing (bespoke EIP + Security Group) and OVOC external publishing (cloud firewall + reverse proxy). The design rationale clearly explains why SIP/RTP protocols are incompatible with traditional reverse proxies, demonstrating deep understanding of voice protocol requirements.

3. **Security Group Segmentation (Section 5):** Splitting the single SBC security group into three per-interface groups (HA, Internal, External) with specific rules per ENI is a strong security design. The elimination of 0.0.0.0/0 outbound rules in favour of VPC Endpoints and scoped CIDRs shows security maturity.

4. **VPC Endpoint Architecture (Section 21):** The use of PrivateLink endpoints for AWS API access (EC2, CloudFormation, CloudWatch, STS) keeps API traffic within the AWS network and eliminates NAT Gateway dependency for critical failover operations. The cost estimate (~$73/month per region) provides transparency.

5. **Cloud East-West Firewall (Section 5):** Including internal traffic inspection between the SBC and on-premises infrastructure addresses defence-in-depth requirements and provides security visibility into east-west traffic flows.

6. **OVOC Data Analytics Architecture (Section 22A):** The ETL pipeline design (OVOC → ETL → Data Lake → Power BI) is architecturally sound and correctly identifies the 24-hour data retention constraint as a critical operational risk requiring monitoring and alerting.

---

## 4. Detailed Findings

### F-SA-001: ARM Configurator — Single Instance, No High Availability

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Category** | Architecture / Resilience |
| **Guide Reference** | Section 4 (ARM Specifications), Section 19 (ARM HA Architecture) |
| **Description** | The ARM Configurator is deployed as a single instance with no HA capability. Section 19 explicitly states: "Configurator Mode: Single instance (no HA)" and "Configurator Failure Handling: Routers continue with last known configuration." While ARM Routers operate in Active-Active mode and continue routing with cached policies during Configurator downtime, the Configurator is the sole management interface for all routing policies, dial plans, and number translation rules across both regions. |
| **Risk / Impact** | Configurator failure prevents all routing policy changes, new number assignments, dial plan updates, and ARM configuration management across the entire SBC fleet. During an outage, no new routing rules can be deployed, and any in-progress configuration changes are lost. The embedded database within the Configurator represents a single point of data loss if the instance is terminated or corrupted. |
| **Evidence** | Section 4: "Configurator: Single instance only (centralized in AUS)". Section 19: "Database: Embedded in Configurator". No backup or recovery strategy for the Configurator database is documented. |
| **Recommendation** | Document and accept the ARM Configurator single-instance limitation. Implement compensating controls: (1) Automated daily EBS snapshots of the Configurator instance, (2) AMI backup before any configuration change, (3) Document the recovery procedure including instance rebuild from snapshot and configuration import, (4) Define RTO/RPO targets for Configurator recovery. |
| **Priority** | Pre-Go-Live |

---

### F-SA-002: Stack Manager — Single-Region, Single-Instance Management Plane

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Architecture / Resilience |
| **Guide Reference** | Section 3 (Architecture Overview), Section 4 (Stack Manager Specifications), Section 21 |
| **Description** | A single Stack Manager instance is deployed in the Australian region only, managing SBC HA stacks across both Australian and US regions via cross-region AWS API calls. Section 4 states: "One per environment, hosted in Australian region; manages all regions including US via cross-region AWS API calls." If the Stack Manager instance fails or the Australian region experiences an outage, no Day 2 operations (software updates, stack healing, topology changes) can be performed on any SBC in either region. |
| **Risk / Impact** | While Stack Manager is not in the critical path for SBC call processing or HA failover (SBCs handle failover independently), its loss prevents: software upgrades across all SBCs, stack healing for corrupted resources, topology changes, and configuration backup. Recovery requires rebuilding the Stack Manager and re-establishing trust with all managed SBC stacks. |
| **Evidence** | Section 3: US region has no Stack Manager. Section 4: "Deployment: One per environment, hosted in Australian region". Section 21: "Availability: Low — Not in critical path for call processing." |
| **Recommendation** | Accept the single-instance risk with documented compensating controls: (1) Regular AMI/EBS snapshots of Stack Manager, (2) Documented rebuild procedure with estimated RTO, (3) Consider maintaining a cold-standby Stack Manager AMI in the US region for cross-region resilience, (4) Test the Stack Manager recovery procedure annually. |
| **Priority** | Pre-Go-Live |

---

### F-SA-003: OVOC — Single Instance in Australian Region Only

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Architecture / Resilience |
| **Guide Reference** | Section 3 (Architecture Overview), Section 4 (OVOC Specifications) |
| **Description** | OVOC is deployed as a single instance in the Australian region only (production). The US region has no OVOC instance. All monitoring, QoE analytics, device management, CDR collection, and Teams Call Quality Dashboard integration depends on this single instance. Section 22A documents that the OVOC analytics views retain only the last 24 hours of data, making the daily ETL extraction critical. |
| **Risk / Impact** | OVOC failure causes: loss of centralised monitoring and alerting, loss of QoE data collection, inability to manage SBC configurations via the OVOC portal, and potential permanent data loss if the failure spans more than 24 hours (due to the rolling analytics window). US region SBCs must transmit monitoring data cross-region to the Australian OVOC, adding latency and cross-region dependency. |
| **Evidence** | Section 3: US production VMs = "2x SBC (HA pair), 1x ARM Router" — no OVOC. Section 22A: "If a daily extraction is missed, that day's data is permanently lost." |
| **Recommendation** | Document the single-OVOC risk and implement: (1) Daily EBS snapshots with cross-region copy, (2) ETL job monitoring with escalation on failure, (3) Define RTO/RPO for OVOC recovery (noting the 24-hour data window), (4) Evaluate whether a secondary OVOC in the US region is justified by the monitoring requirements. |
| **Priority** | Pre-Go-Live |

---

### F-SA-004: No Rollback or Blue-Green Deployment Strategy

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Deployment / Operational Risk |
| **Guide Reference** | Section 18 (Deployment Methodology) |
| **Description** | Section 18 defines an 8-phase deployment sequence but provides no rollback strategy for any phase. There is no blue-green deployment approach, no canary testing methodology, and no defined procedure for reverting a failed deployment or configuration change. The deployment method for SBCs ("Via Stack Manager only for HA") uses CloudFormation, which supports rollback, but this capability is not documented or leveraged. |
| **Risk / Impact** | A failed deployment phase (e.g., SBC firmware upgrade, ARM policy change, OVOC update) with no defined rollback procedure can lead to extended outages and manual recovery efforts. Voice infrastructure outages directly impact business communications. |
| **Evidence** | Section 18: Deployment Methods table shows 5 components with deployment methods but no rollback procedures. No mention of "rollback", "blue-green", "canary", or "rollforward" in the document. |
| **Recommendation** | Add a Rollback Strategy section to the deployment methodology: (1) Pre-change AMI/EBS snapshot for each component, (2) CloudFormation stack rollback procedure for SBC deployments, (3) SBC configuration backup and restore procedure, (4) Define rollback criteria (what triggers a rollback vs. forward-fix), (5) Test rollback procedures in non-production before production deployment. |
| **Priority** | Pre-Go-Live |

---

### F-SA-005: US Region — No Management or Monitoring Infrastructure

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Category** | Architecture / Cross-Region Resilience |
| **Guide Reference** | Section 3 (Architecture Overview) |
| **Description** | The US region (us-east-1) contains only 3 VMs: 2x SBC (HA pair) and 1x ARM Router. All management and monitoring functions depend on Australian region infrastructure: Stack Manager (AU) manages US SBCs via cross-region API, OVOC (AU) monitors US SBCs via cross-region SNMP/syslog, ARM Configurator (AU) manages US routing policies. If the Australia-to-US network path fails, the US SBCs continue processing calls but are unmanaged, unmonitored, and unable to receive configuration updates. |
| **Risk / Impact** | Cross-region network failure isolates US SBCs from all management functions. While SBCs continue processing calls with existing configuration, no monitoring, alerting, CDR collection, QoE reporting, software updates, or configuration changes are possible until cross-region connectivity is restored. Cross-region security group rules (All/All for other region VPC CIDR) are a compensating measure but also a security concern (see F-SA-009). |
| **Evidence** | Section 3: "Total US VMs: 3 — 2x SBC (HA pair), 1x ARM Router." Note: "The US region does not have a dedicated Stack Manager." |
| **Recommendation** | Document the US region management dependency on Australia as an accepted architectural decision. Define the operational posture during cross-region connectivity loss (SBCs continue with existing config, no monitoring). Consider deploying a lightweight OVOC probe or monitoring agent in the US region for local health checking. Ensure break glass procedures support US SBC management without Australian infrastructure. |
| **Priority** | Immediate |

---

### F-SA-006: 24-Hour OVOC Data Retention — Architectural Data Loss Risk

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Category** | Data Architecture / Retention |
| **Guide Reference** | Section 22A (OVOC Data Analytics and Reporting) |
| **Description** | The OVOC analytics views retain only the last 24 hours of data. The guide correctly identifies this as a critical risk: "If a daily extraction is missed, that day's data is permanently lost and cannot be recovered from OVOC." However, the ETL architecture to mitigate this risk (OVOC → ETL → Data Lake) is entirely outside the scope of this deployment guide. No ETL platform is specified, no implementation timeline is defined, and no interim data collection mechanism is described. |
| **Risk / Impact** | Until the ETL pipeline is operational, all QoE and CDR data older than 24 hours is permanently lost. If the ETL pipeline fails after deployment (job scheduling error, credential expiry, network issue), data loss occurs silently unless monitoring is configured. The guide specifies no change data capture or cursor-based extraction — full 24-hour window extraction is required daily. |
| **Evidence** | Section 22A: "Default analytics window: Last 24 hours." "Change tracking: None — no CDC, no cursors, no change data capture." "CRITICAL: The analytics views expose a rolling 24-hour window. If a daily extraction is missed, that day's data is permanently lost." |
| **Recommendation** | Treat the ETL pipeline as a mandatory pre-go-live dependency, not a post-deployment enhancement. Define the ETL platform, schedule, monitoring, and alerting as part of the deployment scope. Implement a temporary data extraction script (e.g., pg_dump of views to S3) that runs from day one until the enterprise ETL pipeline is operational. Define clear ownership of the ETL pipeline. |
| **Priority** | Immediate |

---

### F-SA-007: Excessive Configuration Deferral to Implementation

| Attribute | Detail |
|-----------|--------|
| **Severity** | Critical |
| **Category** | Document Completeness / Design Maturity |
| **Guide Reference** | Multiple sections |
| **Description** | At least 15 distinct configuration areas are deferred to "implementation time" with phrases such as "configured during implementation", "to be determined", placeholder values (XXXX, X.X.X.X), or "refer to implementation worksheet." For a document at version 2.6 with 14 revisions in 8 days, the volume of deferred configuration is unexpectedly high. |
| **Risk / Impact** | Implementation engineers cannot deploy from this guide alone — significant additional design work is required. The deferred configurations include critical parameters (codec settings, routing rules, number manipulation, DSCP marking) that affect call quality and interoperability. Each deferred item represents an implicit design decision that has not been reviewed or approved. |
| **Evidence** | Deferred items include: (1) Codec configuration — Section 13.3, (2) RTP start ports — Section 13.2, (3) SIP listening ports — Section 14.1, (4) All IP addresses — Section 11.4, (5) IP-to-IP routing rules — Section 15.5, (6) Number manipulation rules — Section 15.5, (7) Destination Host in Classification Rules — Section 15.4, (8) Message Manipulation syntax — Section 15.3, (9) DTMF handling — absent, (10) QoS/DSCP policy — absent, (11) CAC settings — absent, (12) Emergency calling config — absent, (13) SBC firmware version — Section 4, (14) VPC/subnet CIDR allocation — Section 5, (15) SIP Provider details — Section 16. |
| **Recommendation** | Create a supplementary SBC Configuration Workbook that resolves all deferred parameters before implementation begins. Categorise deferred items as: (a) site-specific (expected to vary per deployment), (b) design decisions not yet made (require architectural review), (c) vendor-dependent (require AudioCodes consultation). Resolve categories (b) and (c) before implementation. |
| **Priority** | Immediate |

---

### F-SA-008: Deep AudioCodes Vendor Lock-In

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Architecture / Strategic Risk |
| **Guide Reference** | Sections 3, 4, 18, 22 |
| **Description** | The architecture uses five AudioCodes-specific components (Mediant VE SBC, Stack Manager, ARM Configurator, ARM Router, OVOC), all requiring AudioCodes-specific licensing, AudioCodes AMIs from AWS Marketplace, and AudioCodes proprietary management protocols. The Stack Manager is mandatory for HA deployment. ARM uses proprietary routing logic. OVOC uses an AudioCodes-specific analytics schema. Migrating away from AudioCodes would require replacing all five component types. |
| **Risk / Impact** | Vendor lock-in limits negotiating leverage on licensing costs, creates dependency on AudioCodes product roadmap and support lifecycle, and makes alternative SBC evaluation (e.g., Oracle SBC, Ribbon SBC, Microsoft Operator Connect) architecturally prohibitive without full platform replacement. The proprietary Stack Manager for HA deployment means the HA mechanism itself is vendor-locked. |
| **Evidence** | Section 4: All components are AudioCodes products. Section 18: SBC deployment "Via Stack Manager only (required for multi-AZ HA)". Section 22: Three separate licence types required. Section 22A: OVOC-specific analytics schema with proprietary views. |
| **Recommendation** | Document the vendor lock-in as an accepted architectural decision. Negotiate multi-year licensing agreements to mitigate cost risk. Ensure contractual commitments for product support lifecycle, migration assistance, and API documentation. Maintain familiarity with alternative SBC platforms through periodic market review. Consider abstracting routing logic from ARM into an external routing database where feasible. |
| **Priority** | Post-Deployment |

---

### F-SA-009: Cross-Region Security Group Rules — All/All

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Security Architecture |
| **Guide Reference** | Section 5 (Security Groups) |
| **Description** | The SBC Internal Security Group, ARM Security Group, and OVOC Security Group all contain rules permitting `All protocols / All ports` from the other region's VPC CIDR. For example, the SBC Internal Security Group has: "Inbound: All / All / Other Region VPC CIDR — Cross-region SBC-to-SBC and management connectivity." This effectively allows unrestricted network access between regions, negating the per-service port restrictions defined elsewhere. |
| **Risk / Impact** | A compromised instance in either region gains unrestricted network access to all services in the other region. The All/All rules bypass the carefully constructed per-service port restrictions, creating an architectural inconsistency. The stated purpose (cross-region management and SBC-to-SBC connectivity) can be achieved with specific port rules. |
| **Evidence** | Section 5 SBC Internal SG: "Inbound: All / All / Other Region VPC CIDR". Section 5 ARM SG: "Inbound: All / All / Other Region VPC CIDR". Section 5 OVOC SG: "Inbound: All / All / Other Region VPC CIDR". |
| **Recommendation** | Replace All/All cross-region rules with specific port-based rules matching the documented integration points: SIP signalling (TCP/UDP 5060-5061), RTP media (UDP 6000-41999), HTTPS management (TCP 443), SNMP (UDP 161/162), syslog (UDP 514), QoE (TCP 5001). This maintains cross-region functionality while enforcing least-privilege access. |
| **Priority** | Pre-Go-Live |

---

### F-SA-010: No Performance Testing Methodology

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Quality Assurance |
| **Guide Reference** | Appendix A (Deployment Checklist) |
| **Description** | The deployment checklist (Appendix A) includes "End-to-end calling tested" and "HA failover tested and documented" but defines no performance testing methodology. There is no mention of load testing, stress testing, soak testing, or concurrent session capacity validation. For a voice platform expected to handle enterprise-scale call volumes across two regions, performance validation is essential. |
| **Risk / Impact** | Without performance testing, the first real load test is production go-live. Undiscovered performance bottlenecks (transcoding capacity, media port exhaustion, SIP message rate limits, OVOC QoE processing throughput) will manifest as call quality degradation or call failures under production load. |
| **Evidence** | Appendix A includes functional tests ("End-to-end calling tested") but no performance tests. No mention of "load test", "stress test", "soak test", "SIPp", "call generator", or "performance" in testing context. |
| **Recommendation** | Define a performance testing methodology: (1) Tool selection (SIPp, Empirix, or AudioCodes SBC load generator), (2) Test scenarios (concurrent call ramp, peak sustained load, failover under load, transcoding load), (3) Success criteria (MOS thresholds, call setup time, media quality metrics), (4) Environment requirements (isolated test environment or production with controlled traffic). |
| **Priority** | Pre-Go-Live |

---

### F-SA-011: Document Maturity Concern — 14 Revisions in 8 Days

| Attribute | Detail |
|-----------|--------|
| **Severity** | Low |
| **Category** | Document Governance |
| **Guide Reference** | Document Control (lines 3535–3556) |
| **Description** | The Document Control section shows 14 revisions (v1.0 through v2.6) published between 5 February 2026 and 13 February 2026 — an average of nearly 2 revisions per day over 8 calendar days. Several revisions made on the same day include major architectural changes (v2.0: 4-ENI to 3-ENI consolidation, v2.1: authentication model change, v2.5: interface remapping). This pace of change suggests the design was still crystallising during documentation, not merely being documented. |
| **Risk / Impact** | Rapid revision pace increases the risk of inconsistencies between sections updated at different times. Architecture decisions made under time pressure may not have received adequate stakeholder review. The authentication model changed from Entra ID (v1.2) to LDAPS (v2.1) to RADIUS (v2.3) across three revisions in three days, suggesting uncertainty in the design. |
| **Evidence** | Document Control: v1.0 (5 Feb) through v2.6 (13 Feb). Same-day revisions: v1.1–v1.6 on 9 Feb (6 versions), v1.7–v1.8 on 10 Feb, v2.0–v2.2 on 11 Feb (3 major versions), v2.3–v2.5 on 12 Feb. Authentication model: v1.2 "Proxy SBC uses Microsoft Entra ID (OAuth 2.0)", v2.1 "Unified to on-premises Active Directory (LDAPS)", v2.3 "Replaced LDAPS to RADIUS with Cisco ISE". |
| **Recommendation** | Conduct a dedicated consistency review pass now that the design has stabilised. Verify that all sections updated in earlier revisions (particularly those touching network interfaces, authentication, and security groups) are consistent with the final v2.6 state. Consider a formal design review gate with stakeholder sign-off before implementation. |
| **Priority** | Immediate |

---

### F-SA-012: No Scalability or Growth Architecture

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Architecture / Future-Proofing |
| **Guide Reference** | Sections 3, 4, 19 |
| **Description** | The architecture is designed for a fixed topology: 2 SBCs per region (HA pair), 1 ARM Router per region, 1 OVOC, 1 ARM Configurator, 1 Stack Manager. There is no discussion of how the architecture scales if: call volumes increase beyond the current SBC capacity, new regions are added, new downstream SBC sites are added, or the number of Teams Direct Routing users grows. The SBC HA model (1+1 Active/Standby within a single VPC) does not support horizontal scaling. |
| **Risk / Impact** | If call volumes exceed the m5n.large SBC's session capacity, the only scaling path is vertical (move to a larger instance type, e.g., c5.2xlarge), which requires downtime and re-deployment via Stack Manager. There is no documented procedure for adding a second HA pair per region to handle overflow traffic. OVOC's single-instance model with 2TB storage has a finite capacity ceiling. |
| **Evidence** | Section 3: Fixed VM counts (5 non-prod, 9 production). Section 4: SBC instance types listed but no capacity planning matrix. Section 19: HA is 1+1 within single VPC — no mention of N+1, horizontal scaling, or multi-pair deployment. |
| **Recommendation** | Add a Scalability Considerations section addressing: (1) SBC vertical scaling procedure (instance type change, licensing impact), (2) SBC horizontal scaling (multiple HA pairs with load distribution via ARM), (3) OVOC capacity limits and scaling path, (4) Regional expansion procedure (new region checklist), (5) Growth triggers (session count thresholds that trigger scaling review). |
| **Priority** | Post-Deployment |

---

### F-SA-013: No Disaster Recovery Strategy

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Category** | Architecture / Resilience |
| **Guide Reference** | Sections 3, 19 (absent) |
| **Description** | The guide addresses High Availability (SBC failover within a VPC) but does not address Disaster Recovery. There is no cross-region DR strategy for any component. If the Australian region (ap-southeast-2) experiences a complete failure, all management infrastructure (Stack Manager, OVOC, ARM Configurator) is lost. The US SBCs continue processing calls with existing configuration but are unmanaged. There is no documented RTO/RPO for any component. |
| **Risk / Impact** | Complete loss of the Australian region would impact: all Australian voice services, all management and monitoring for both regions, OVOC analytics data (permanent loss after 24 hours), and ARM configuration management. Recovery would require rebuilding all management infrastructure from scratch. |
| **Evidence** | Section 19: HA scope is "Within single VPC, across two Availability Zones." No mention of "disaster recovery", "DR", "RTO", "RPO", "cross-region recovery", or "backup site" in the context of service recovery. |
| **Recommendation** | Define DR strategy for each component tier: (1) SBC tier: Cross-region SBC pair in US provides geographic voice redundancy (already exists), but formalise Teams Direct Routing failover between regions, (2) Management tier: Daily AMI/snapshot cross-region replication for Stack Manager, OVOC, ARM Configurator, (3) Data tier: OVOC data protected by daily ETL to data lake (cross-region), (4) Define RTO/RPO for each component tier. |
| **Priority** | Pre-Go-Live |

---

### F-SA-014: SBC-to-SBC Proxy Connectivity Model Not Fully Defined

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Architecture / Integration |
| **Guide Reference** | Section 2 (Cross-Region SBC-to-SBC Connectivity note), Section 14.2 (Proxy Set Index 6) |
| **Description** | The Proxy-to-Proxy trunk (AU ↔ US) is documented at a high level: a Proxy Set exists (Index 6), it uses the Internal (LAN) SIP Interface, and SIP OPTIONS keep-alive is enabled. However, the architectural role of this trunk is not fully articulated. What traffic traverses it? When does a call route from AU Proxy to US Proxy? Is it for inter-region call routing, overflow, or failover? The routing rules (Section 15.5) are deferred to implementation, so the Proxy-to-Proxy use cases remain undefined. |
| **Risk / Impact** | Without clear Proxy-to-Proxy routing logic, the inter-region trunk may be deployed but never used, or used in unexpected ways. The guide does not define whether AU-originated calls to US numbers route via AU Proxy → AU SIP Provider (international PSTN) or AU Proxy → US Proxy → US SIP Provider (local PSTN breakout via inter-region SBC trunk). This decision significantly impacts call quality, cost, and regulatory compliance. |
| **Evidence** | Section 2: "Virtual IPs assigned to each regional SBC pair do need to be routable between the AU and US regions for SBC-to-SBC (proxy-to-proxy) signalling and media." Section 14.2 Proxy Set Index 6: "Proxy-to-Proxy — Enables signalling between the two Proxy SBCs for inter-region call routing and failover." Section 15.5: Routing scenario table shows "Proxy SBC (AU) → Proxy SBC (US) and vice versa" but routing rules are deferred. |
| **Recommendation** | Define the Proxy-to-Proxy routing use cases explicitly: (1) Inter-region call routing (AU user calling US number → route via US SIP Provider for local breakout), (2) Inter-region failover (if AU SIP Provider is down, route via US Proxy for PSTN breakout), (3) Proxy-to-Proxy call scenarios (AU internal extension calling US internal extension). Document the routing decision criteria and number patterns for each use case. |
| **Priority** | Pre-Go-Live |

---

### F-SA-015: No Integration Testing Strategy

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Quality Assurance |
| **Guide Reference** | Appendix A (Deployment Checklist), Section 15.5 |
| **Description** | The deployment checklist includes high-level integration verification items ("OAuth authentication working", "End-to-end calling tested") but defines no integration testing strategy. Section 15.5 notes that "The routing logic is validated during integration testing with all connected systems" but provides no test plan, test cases, or acceptance criteria. The number of integration points in this architecture (Teams, 2x SIP Providers, Downstream SBCs, 3rd Party PBX, radio systems, ATAs, OVOC, ARM, Stack Manager) demands a structured test approach. |
| **Risk / Impact** | Ad-hoc integration testing may miss edge cases such as: call transfer between different trunk types, conference scenarios, voicemail deposit/retrieve, hold/resume across trunk types, HA failover during active calls, cross-region routing scenarios, and emergency calling. |
| **Evidence** | Appendix A: 8 integration verification checkboxes but no test plan reference. Section 15.5: "Validated during integration testing" — no test case definitions, no acceptance criteria. |
| **Recommendation** | Develop a comprehensive Integration Test Plan covering: (1) Per-trunk call test matrix (each source → each destination), (2) Call feature tests (transfer, hold, conference, voicemail), (3) HA failover test under load, (4) Cross-region routing tests, (5) Emergency calling tests, (6) Codec negotiation verification per trunk, (7) DTMF verification per trunk, (8) QoE data verification in OVOC, (9) CDR accuracy verification, (10) Acceptance criteria (MOS > 3.5, call setup < 3s, zero call drops during failover). |
| **Priority** | Pre-Go-Live |

---

## 5. Risk Matrix

| Finding ID | Title | Severity | Likelihood | Impact | Risk Rating |
|------------|-------|----------|------------|--------|-------------|
| F-SA-001 | ARM Configurator single instance | High | Medium | High | High |
| F-SA-002 | Stack Manager single-region SPOF | Medium | Low | Medium | Medium |
| F-SA-003 | OVOC single instance | Medium | Medium | High | High |
| F-SA-004 | No rollback/blue-green deployment | Medium | Medium | High | High |
| F-SA-005 | US region no management infra | High | Medium | High | High |
| F-SA-006 | 24-hour OVOC data retention risk | High | Medium | High | High |
| F-SA-007 | Excessive config deferral | Critical | High | High | Critical |
| F-SA-008 | Deep AudioCodes vendor lock-in | Medium | High | Medium | Medium |
| F-SA-009 | Cross-region All/All SG rules | Medium | Medium | Medium | Medium |
| F-SA-010 | No performance testing methodology | Medium | Medium | High | High |
| F-SA-011 | 14 revisions in 8 days maturity | Low | High | Low | Low |
| F-SA-012 | No scalability architecture | Medium | Medium | Medium | Medium |
| F-SA-013 | No disaster recovery strategy | High | Low | Critical | High |
| F-SA-014 | Proxy-to-Proxy model undefined | Medium | Medium | Medium | Medium |
| F-SA-015 | No integration testing strategy | Medium | Medium | High | High |

---

## 6. Gap Analysis

| Architecture Domain | Guide Coverage | Gap |
|---------------------|----------------|-----|
| High Availability — SBC | Comprehensive | None significant |
| High Availability — Management | SPOFs acknowledged | No HA for ARM Configurator, OVOC, Stack Manager |
| Disaster Recovery | Not addressed | No cross-region DR strategy, no RTO/RPO |
| Scalability | Not addressed | No horizontal scaling, no growth architecture |
| Performance Testing | Not addressed | No load testing, no capacity validation |
| Integration Testing | Mentioned but undefined | No test plan, no acceptance criteria |
| Deployment Rollback | Not addressed | No rollback procedures |
| Data Retention | Risk identified (22A) | No implementation plan for ETL pipeline |
| Vendor Strategy | Not addressed | No vendor lock-in risk assessment |
| Document Maturity | Version history provided | 14 revisions in 8 days raises consistency concerns |
| Cross-Region Resilience | Basic topology | US region fully dependent on AU for management |
| Security Architecture | Well covered | All/All cross-region rules contradict least-privilege |

---

## 7. Recommendations Summary

### Immediate (Before Design Finalisation)

1. Define US region operational posture during AU connectivity loss (F-SA-005)
2. Treat ETL pipeline as mandatory pre-go-live dependency (F-SA-006)
3. Create Configuration Workbook resolving deferred parameters (F-SA-007)
4. Conduct consistency review after rapid revision cycle (F-SA-011)

### Pre-Go-Live (Before Production Deployment)

5. Implement compensating controls for ARM Configurator SPOF (F-SA-001)
6. Document Stack Manager recovery procedure (F-SA-002)
7. Define OVOC recovery procedure with RTO/RPO (F-SA-003)
8. Develop rollback procedures for each deployment phase (F-SA-004)
9. Replace All/All cross-region SG rules with specific ports (F-SA-009)
10. Define performance testing methodology (F-SA-010)
11. Define disaster recovery strategy per component tier (F-SA-013)
12. Clarify Proxy-to-Proxy routing use cases (F-SA-014)
13. Develop integration test plan (F-SA-015)

### Post-Deployment (Operational Improvements)

14. Document vendor lock-in risk and mitigation strategy (F-SA-008)
15. Develop scalability planning and growth triggers (F-SA-012)
16. Establish architecture review cadence (annual) for this platform

---

## 8. Action Items Register

| # | Action | Owner | Priority | Target Date | Status |
|---|--------|-------|----------|-------------|--------|
| 1 | Define US region operational independence posture | Solution Architect | Critical | Design phase | Open |
| 2 | Confirm ETL pipeline as pre-go-live scope | Project Manager + Data Engineering | Critical | Immediate | Open |
| 3 | Create SBC Configuration Workbook | Voice Engineering + Solution Architect | Critical | Pre-implementation | Open |
| 4 | Conduct v2.6 consistency review | Technical Writer + Voice Engineering | High | Before design sign-off | Open |
| 5 | Implement ARM Configurator backup/recovery | Cloud Engineering | High | Pre-go-live | Open |
| 6 | Document Stack Manager recovery procedure | Cloud Engineering | Medium | Pre-go-live | Open |
| 7 | Define OVOC RTO/RPO and recovery procedure | Cloud Engineering + Voice Engineering | High | Pre-go-live | Open |
| 8 | Develop deployment rollback procedures | Voice Engineering + Cloud Engineering | High | Pre-go-live | Open |
| 9 | Tighten cross-region security group rules | Cloud Engineering + Security | High | Pre-go-live | Open |
| 10 | Define performance testing approach | Voice Engineering + QA | Medium | Pre-go-live | Open |
| 11 | Define DR strategy per component tier | Solution Architect + Cloud Engineering | High | Pre-go-live | Open |
| 12 | Document Proxy-to-Proxy routing use cases | Voice Engineering + Solution Architect | Medium | Design phase | Open |
| 13 | Develop integration test plan | Voice Engineering + QA | Medium | Pre-go-live | Open |
| 14 | Document vendor lock-in risk assessment | Solution Architect + Procurement | Low | Post-go-live | Open |
| 15 | Develop scalability planning document | Solution Architect | Low | Post-go-live | Open |

---

## 9. Appendix: Sections Reviewed

| Section | Lines | Architectural Focus |
|---------|-------|---------------------|
| 1. Executive Summary | 45–76 | Scope, key takeaways, constraints |
| 2. Critical Findings | 78–128 | HA mechanism, API requirements |
| 3. Architecture Overview | 131–161 | Topology, VM counts, regional layout |
| 4. Component Specifications | 163–339 | Instance types, sizing, component dependencies |
| 5. AWS Infrastructure Requirements | 342–521 | VPC, subnets, security groups, publishing patterns |
| 9. SBC Provisioning | 801–946 | HA deployment model, prerequisites |
| 18. Deployment Methodology | 2205–2221 | 8-phase sequence, deployment methods |
| 19. High Availability Considerations | 2223–2468 | SBC HA, ARM HA, SIP trunk HA, voice recording |
| 20. IAM Permissions and Security | 2476–2605 | IAM policies, roles, VPC endpoints |
| 21. Cyber Security Considerations | 2608–2843 | Security architecture, risk assessment |
| 22. Licensing Considerations | 2846–2875 | Licensing model dependencies |
| 22A. OVOC Data Analytics | 2877–3156 | Data retention, ETL, audit considerations |
| Document Control | 3535–3556 | Version history, revision pace |
| Appendix A | 3219–3277 | Deployment checklist completeness |

---

## 10. Appendix: Standards and References

| Standard / Reference | Relevance |
|---------------------|-----------|
| AWS Well-Architected Framework — Reliability Pillar | HA, DR, fault tolerance assessment |
| AWS Well-Architected Framework — Operational Excellence Pillar | Deployment, monitoring, incident response |
| AWS Well-Architected Framework — Security Pillar | IAM, network security, data protection |
| AWS Well-Architected Framework — Cost Optimisation Pillar | Instance selection, Reserved Instances |
| TOGAF 10 — Architecture Decision Records | Decision documentation and traceability |
| ISO/IEC 25010 — Systems and Software Quality | Quality attributes assessment framework |
| AudioCodes Mediant VE SBC Installation Manual v7.6 | Component deployment reference |
| AudioCodes Stack Manager User's Manual v7.6 | Stack Manager capabilities and limitations |
| Microsoft Teams Direct Routing Planning Guide | Integration requirements |
| AWS VPC Endpoint Documentation | PrivateLink architecture reference |
| AWS CloudFormation Best Practices | Stack rollback and change management |

---

*End of Solution Architect Review Report*
