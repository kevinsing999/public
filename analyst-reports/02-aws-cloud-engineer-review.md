# AWS Cloud Engineer Review — AudioCodes AWS Deployment Guide v2.6

## Internal Technical Review Report

**Reviewer Role:** Senior AWS Cloud Engineer / Infrastructure Architect
**Document Under Review:** AudioCodes SBC — Unified Deployment & Configuration Guide v2.6 (13 February 2026)
**Review Date:** 4 March 2026
**Report ID Prefix:** F-AW

---

## 1. Executive Summary

**Overall Rating:** Conditionally Adequate — The guide provides a sound architectural foundation for deploying AudioCodes voice infrastructure on AWS, but contains material gaps in infrastructure resilience, cost governance, operational automation, and AWS service currency that must be addressed before production deployment.

The document demonstrates strong awareness of AWS networking primitives (VPC Endpoints, Security Groups with least-privilege egress, EIP failover mechanics) and includes a well-considered IAM design for the SBC HA role with resource-scoped ARNs and tag-based conditions. However, the infrastructure layer beneath the AudioCodes application stack — instance families, storage IOPS provisioning, backup strategy, monitoring, tagging, and disaster recovery — receives insufficient attention. Several component specifications reference previous-generation EC2 instance families that are two to three generations behind current offerings, and there is no backup, snapshot, or disaster recovery strategy for any component. The Stack Manager IAM policy grants `ec2:*` and `cloudformation:*` with `Resource: "*"`, which, even with the documented temporal elevation mitigation, represents a significant privilege escalation risk.

**Top 3 Findings:**

1. **F-AW-001 (High):** ARM Configurator and ARM Router specify m4-family instances (Section 4 / Appendix C), which are three generations behind current AWS offerings. m4 instances lack Nitro-based security, enhanced networking by default, and cost-efficient pricing relative to m5/m6i/m7i equivalents.
2. **F-AW-003 (High):** No multi-AZ NAT Gateway resilience documented (Section 5). NAT Gateway is AZ-scoped; if the AZ hosting the NAT Gateway fails, Stack Manager loses AWS API access and SBC HA failover via NAT Gateway becomes unavailable for that AZ.
3. **F-AW-010 (High):** Stack Manager IAM policy grants `ec2:*` and `cloudformation:*` on `Resource: "*"` (Section 20). Even with temporal elevation, this permits creation or deletion of any EC2 resource in the account during the elevation window.

**Go/No-Go Recommendation:** Conditional Go — proceed to non-production deployment with the understanding that the High-severity findings (F-AW-001, F-AW-002, F-AW-003, F-AW-009, F-AW-010) must be resolved or formally risk-accepted before production go-live. The absence of a backup strategy (F-AW-002) and disaster recovery plan (F-AW-014) represent operational risks that should not be carried into production without explicit risk owner sign-off.

---

## 2. Scope of Review

### Sections Examined

| Section | Title | Relevance to Review |
|---------|-------|---------------------|
| 3 | Architecture Overview | Component count, regional topology, VM distribution |
| 4 | Component Specifications | EC2 instance types, storage, compute sizing |
| 5 | AWS Infrastructure Requirements | VPC, subnets, security groups, external publishing |
| 9 | SBC Provisioning | HA provisioning, compute requirements, subnet design |
| 18 | Deployment Methodology | Deployment methods, CloudFormation usage |
| 19 | High Availability Considerations | SBC HA architecture, failover mechanics, prerequisites |
| 20 | IAM Permissions and Security | Stack Manager IAM, SBC IAM, VPC Endpoints, role creation |
| 21 | Cyber Security Considerations | Security architecture, attack surface, compliance |
| 22 | Licensing Considerations | Procurement model, licensing tiers |
| Appendix A | Deployment Checklist | Pre-deployment and integration verification |
| Appendix C | Quick Reference Tables | Instance type summary, port summary |

### Methodology

- Comprehensive review of all AWS-specific configuration, sizing, and security content
- Cross-referencing of instance type specifications against current AWS instance family availability and pricing (as of March 2026)
- Assessment of IAM policies against AWS Security Best Practices and the principle of least privilege
- Evaluation of resilience design against the AWS Well-Architected Framework (Reliability, Security, Cost Optimisation, Operational Excellence pillars)
- Comparison of VPC design and security group rules against AWS networking best practices
- Gap analysis for operational tooling (backup, monitoring, IaC, tagging)

### Reference Standards

- AWS Well-Architected Framework (2025 edition)
- AWS Security Best Practices (IAM, VPC, EC2)
- AWS EC2 Instance Type documentation (current generation families)
- CIS AWS Foundations Benchmark v3.0
- AWS Reliability Pillar — Multi-AZ resilience patterns
- ACSC (Australian Cyber Security Centre) Cloud Security Guidelines

---

## 3. Strengths Identified

1. **VPC Endpoint Architecture (Section 21, lines 2745-2783):** The guide specifies Interface VPC Endpoints for EC2, CloudFormation, CloudWatch, and STS, plus a Gateway Endpoint for S3. This eliminates `0.0.0.0/0` outbound rules from security groups and keeps AWS API traffic within the AWS network. The dedicated VPC Endpoint Security Group with source-scoped inbound rules (SBC HA Subnet CIDR, Stack Manager SG) demonstrates genuine least-privilege thinking at the network layer. The cost estimate (~$73/month per region for 5 endpoints across 2 AZs) is a practical inclusion that aids budgeting.

2. **SBC IAM Policy Design (Section 20, lines 2523-2577):** The SBC HA IAM policy is well-crafted, using three separate statements with resource-scoped ARNs and tag-based conditions. The `AllowReplaceRoute` action is scoped to a specific route table ARN with an `Env` tag condition, and `AllowAssociateAddress` requires both `App` and `Env` tag conditions. The design rationale table (lines 2572-2577) correctly notes that AWS Describe actions do not support resource-level scoping. This is a materially better policy than the unconstrained `ec2:*` seen in many vendor deployment guides.

3. **Temporal IAM Elevation Pattern (Section 20, lines 2505-2521):** The recommendation to detach the Stack Manager IAM policy during normal operations and re-attach only during deployment or Day 2 operations is a pragmatic mitigation for the broad permissions required. The three implementation options (IAM policy toggle, SCP deny, automation runbook) provide flexibility for different organisational maturity levels. The CloudTrail logging callout for attach/detach events supports audit requirements.

4. **Security Group Segmentation (Section 5, lines 359-452):** The split of the SBC into three per-interface security groups (HA, Internal, External) assigned to the respective ENIs is a strong design. Each group contains only the rules relevant to that interface's traffic profile. The elimination of `0.0.0.0/0` outbound rules across all security groups, replaced with specific destination CIDRs and VPC Endpoint security group references, is a genuine improvement over typical deployment guides.

5. **External Publishing Pattern Documentation (Section 5, lines 455-499):** The clear articulation of two distinct publishing patterns — bespoke EIP + Security Group for the SBC (with rationale for why SIP/RTP is incompatible with reverse proxies) versus traditional cloud firewall + reverse proxy for OVOC — demonstrates architectural maturity. The design rationale sections for each pattern provide defensible justification for security review discussions.

6. **Stack Manager SOE Compatibility (Section 4, lines 256-270):** The documentation of supported operating systems (Ubuntu 18.04-24.04, RHEL 8/9, CentOS 8/Stream 9, Rocky 8/9, AlmaLinux 8/9, Amazon Linux 2/2023) with explicit SOE compatibility notes enables organisations to deploy Stack Manager on their standard hardened OS image rather than requiring a vendor-specific appliance AMI.

---

## 4. Detailed Findings

### F-AW-001: Previous-Generation Instance Families for ARM Components

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Category** | Compute / Cost Optimisation |
| **Guide Reference** | Section 4, lines 296-300 (ARM Specifications table); Section 9.4, lines 931-937 (Compute Requirements Summary); Appendix C, lines 3365-3366 (Instance Type Summary) |
| **Description** | The ARM Configurator specifies `m4.xlarge` (4 vCPU, 16 GiB) and the ARM Router specifies `m4.large` (2 vCPU, 8 GiB). The m4 instance family was launched in 2015 and is now three generations behind the current m7i family (m4 -> m5 -> m6i -> m7i). The guide includes a note at line 300 acknowledging this: "m4 is a previous-generation instance family. If AudioCodes AMI compatibility permits, consider m5 or m6i equivalents for better price-performance." However, this recommendation is not actioned — the specification tables throughout the document consistently list m4 as the required instance type. |
| **Risk / Impact** | **Performance:** m4 instances use the older Xen hypervisor, not the AWS Nitro System. They lack enhanced networking by default, have lower network bandwidth (up to 2 Gbps vs 12.5 Gbps on m5), and do not benefit from Nitro-based hardware security features (dedicated hardware for encryption, network virtualisation). **Cost:** AWS pricing for previous-generation instances is not guaranteed to remain competitive; AWS incentivises migration to current-generation families. m4 instances are not eligible for Savings Plans (Compute or EC2 Instance). **Availability:** AWS may eventually deprecate m4 in specific regions or AZs, creating deployment risk. **Security:** m4 instances lack the NitroTPM and Nitro Enclaves capabilities available on m5+ families. |
| **Evidence** | Section 4, line 297: `Configurator | m4.xlarge | 4 | 16 GiB | 1 (single instance)`; line 298: `Router | m4.large | 2 | 8 GiB | 1+ per region`. Appendix C, line 3365: `ARM Configurator | All | m4.xlarge | 4 | 16 GiB | 100 GB gp3`; line 3366: `ARM Router | All | m4.large | 2 | 8 GiB | 80 GB gp3`. |
| **Recommendation** | Replace m4.xlarge with m5.xlarge (or m6i.xlarge) for the ARM Configurator and m4.large with m5.large (or m6i.large) for the ARM Router. These are drop-in replacements with identical vCPU and memory specifications but deliver approximately 15-25% better price-performance. Validate AudioCodes AMI compatibility with the target instance family before deployment. If the AudioCodes AMI is HVM-based (which all current AMIs should be), m5/m6i compatibility is expected. Update all three locations where these instance types are specified (Section 4, Section 9.4, Appendix C). |
| **Priority** | Immediate |

---

### F-AW-002: No Backup or Snapshot Strategy

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Category** | Operational Resilience / Data Protection |
| **Guide Reference** | Entire document (absence) |
| **Description** | The guide does not define any backup, snapshot, or recovery strategy for any component. There is no mention of EBS snapshots, AMI backups, configuration export schedules, or S3-based config backup for any of the nine production VMs. The Stack Manager's Day 2 operations section (Section 21, line 2664) references "Configuration Backup: Supports configuration backup and recovery operations" but provides no procedure, schedule, or storage target. OVOC contains a PostgreSQL database with call quality data, alarm history, and device configuration — none of which has a documented backup approach. |
| **Risk / Impact** | Without a backup strategy, any component failure requiring instance replacement would result in complete configuration loss. OVOC in particular stores historical QoE data, device configurations, topology, and alarm data. The ARM Configurator holds the centralised routing policy database. The SBC configuration, while re-deployable via Stack Manager, contains runtime state and tuned parameters that may not be captured in Stack Manager's deployment templates. Failure to back up these components violates the AWS Well-Architected Framework Reliability Pillar (REL-9: Back up data) and most organisational data protection policies. |
| **Evidence** | A search for "backup", "snapshot", "AMI backup", "EBS snapshot", or "recovery point" across the document returns no procedural or scheduling content. The only reference is the Stack Manager Day 2 operations bullet point at line 2664: "Configuration Backup: Supports configuration backup and recovery operations". The deployment checklist (Appendix A, lines 3219-3278) does not include any backup verification step. |
| **Recommendation** | Add a dedicated Backup and Recovery section covering: (1) EBS snapshot schedule for all EC2 instances (recommend daily automated snapshots with 14-day retention via AWS Backup or Data Lifecycle Manager); (2) AMI creation procedure for golden image capture after initial configuration; (3) OVOC database backup procedure (pg_dump of the `dbems` database, exported to S3 with versioning and lifecycle rules); (4) SBC configuration export (AudioCodes CLI `copy running-configuration` to TFTP/SCP target, or OVOC-managed config backup); (5) ARM Configurator database backup; (6) Recovery Time Objective (RTO) and Recovery Point Objective (RPO) targets for each component. Add backup verification to the deployment checklist (Appendix A). |
| **Priority** | Pre-Go-Live |

---

### F-AW-003: Single-AZ NAT Gateway Resilience Risk

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Category** | Resilience / High Availability |
| **Guide Reference** | Section 5, lines 342-354 (VPC Configuration); Section 2, lines 113-128 (API Access Requirements); Section 21, lines 2737-2742 (Network Placement) |
| **Description** | The guide references NAT Gateway as an option for AWS API access (lines 124-127: "NAT Gateway (recommended for private subnets)") and as the alternative to VPC Endpoints (line 2741: "Alternative: NAT Gateway egress if VPC Endpoints are not deployed"). However, the guide does not address the AZ-scoped nature of NAT Gateway. A NAT Gateway exists within a single Availability Zone; if that AZ experiences a failure, all resources routing through it lose outbound connectivity. The guide recommends VPC Endpoints as the primary path (which is correct), but the NAT Gateway fallback is documented without multi-AZ resilience guidance. |
| **Risk / Impact** | If the organisation deploys a NAT Gateway as a backup or alternative path for AWS API access, and that NAT Gateway's AZ fails: (1) the Stack Manager (single instance in AU) loses all AWS API access, preventing Day 2 operations; (2) any SBC relying on NAT Gateway for EC2 API access (rather than VPC Endpoints) cannot perform HA failover — the standby SBC would be unable to call `ec2:ReplaceRoute` or `ec2:AssociateAddress`, resulting in a failed failover and service outage. This is particularly critical because the SBC HA architecture spans two AZs, but a single-AZ NAT Gateway creates an asymmetric failure domain. |
| **Evidence** | Section 5, line 352: "Internet Gateway or NAT Gateway | Required | For Stack Manager API access". Section 2, lines 124-127 list NAT Gateway as the recommended option for private subnets. Section 21, line 2741: "Alternative: NAT Gateway egress if VPC Endpoints are not deployed". No mention of NAT Gateway per-AZ deployment or multi-AZ NAT Gateway design anywhere in the document. |
| **Recommendation** | (1) Clarify that VPC Endpoints are the primary and recommended path for all AWS API access (which the guide already does well in Section 21). (2) If NAT Gateway is used as a fallback, document that a NAT Gateway must be deployed in each AZ where SBC instances or the Stack Manager reside, with per-AZ route tables directing traffic to the local AZ's NAT Gateway. (3) Add a note to Section 19 (HA Prerequisites) that the HA subnet's route to AWS API endpoints must be resilient to single-AZ failure — either via VPC Endpoints deployed in multiple AZs or via per-AZ NAT Gateways. (4) Consider adding the EC2 VPC Endpoint ENI placement requirement: Section 21, line 2781 states "Place EC2 endpoint ENI in the HA subnet" — clarify that this must be deployed in both AZs where SBC instances reside for the endpoint to be available during an AZ failure. |
| **Priority** | Pre-Go-Live |

---

### F-AW-004: No CloudWatch Alarms Defined

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Monitoring / Operational Excellence |
| **Guide Reference** | Section 20, lines 2491-2492 (Stack Manager IAM — `cloudwatch:PutMetricAlarm`, `cloudwatch:DeleteAlarms`); Section 21, lines 2756 (CloudWatch VPC Endpoint) |
| **Description** | The Stack Manager IAM policy includes `cloudwatch:PutMetricAlarm` and `cloudwatch:DeleteAlarms` permissions, and a CloudWatch VPC Endpoint is listed as required. This indicates that CloudWatch alarm integration is architecturally intended. However, the guide does not define any specific CloudWatch alarms, thresholds, or SNS notification targets for any component. There are no alarms for EC2 instance status checks, CPU utilisation, EBS volume health, network throughput, or HA failover events. The deployment checklist (Appendix A, line 3277) includes "Monitoring and alerting configured" but provides no specifics. |
| **Risk / Impact** | Without defined CloudWatch alarms, the operations team has no automated notification of infrastructure-level failures. An SBC instance could enter an impaired state (EC2 system status check failure) without triggering an alert, potentially causing call quality degradation before the HA failover triggers. OVOC disk space exhaustion (2 TB gp3 volume under high QoE data load) could go undetected until the PostgreSQL database fails. Stack Manager failures would only be discovered when a Day 2 operation is attempted. |
| **Evidence** | Section 20, line 2491: `"cloudwatch:DeleteAlarms"` and line 2492: `"cloudwatch:PutMetricAlarm"` in Stack Manager IAM policy. Section 21, line 2703: "Required to configure monitoring alarms for SBC health" in permission justification. No alarm definitions, thresholds, or SNS topic configurations exist anywhere in the document. |
| **Recommendation** | Define a baseline CloudWatch alarm set for each component type. Recommended minimum: **SBC instances:** StatusCheckFailed_System, StatusCheckFailed_Instance (both > 0 for 1 minute), CPUUtilization > 85% sustained 5 minutes, NetworkPacketsIn = 0 sustained 5 minutes (indicates network isolation). **OVOC:** StatusCheckFailed (both), EBS VolumeQueueLength > 10 sustained 5 minutes, disk utilisation via CloudWatch Agent. **Stack Manager:** StatusCheckFailed (both). **All instances:** EBS ImpairedVol status. Define an SNS topic for alert delivery and document the alarm creation procedure (manual or via CloudFormation/Terraform). |
| **Priority** | Pre-Go-Live |

---

### F-AW-005: No Tagging Strategy

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Governance / Cost Management |
| **Guide Reference** | Section 20, lines 2546-2561 (SBC IAM tag conditions — `Env`, `App` tags); Section 21, lines 2717-2735 (Tag-based condition for Stack Manager) |
| **Description** | The SBC IAM policy uses two tags for condition-based access control: `Env` (values: `NonProd_SBC`, `Prod_SBC`) and `App` (value: `Voice`). The Stack Manager security enhancement section suggests a `Project` tag (value: `AudioCodes-Voice`) for potential tag-based IAM scoping. However, these tags are used solely for IAM conditions — there is no comprehensive tagging strategy defined for the deployment. No guidance is provided on mandatory tags for cost allocation, ownership, environment identification, change management, or operational categorisation across the nine production VMs and their associated resources (ENIs, EBS volumes, EIPs, security groups, route tables, VPC Endpoints). |
| **Risk / Impact** | Without a consistent tagging strategy: (1) AWS Cost Explorer and billing reports cannot attribute costs to specific components, environments, or cost centres; (2) Resource lifecycle management (identifying orphaned resources, tracking resource age) is manual and error-prone; (3) Automation scripts (start/stop schedules for non-production, backup policies via AWS Backup tag-based plans) cannot target resources; (4) Security tooling (AWS Config rules, GuardDuty resource grouping) cannot effectively categorise the voice infrastructure; (5) The organisation cannot enforce tagging compliance via AWS Tag Policies or SCPs. |
| **Evidence** | Section 20, line 2548: `"aws:ResourceTag/Env": "<NonProd_SBC|Prod_SBC>"` — only two values defined. Line 2559: `"aws:ResourceTag/App": "Voice"` — single value. Section 21, line 2729: `"ec2:ResourceTag/Project": "AudioCodes-Voice"` — suggested but not mandated. No tagging standard, no mandatory tag list, no tag-based cost allocation guidance. |
| **Recommendation** | Define a mandatory tagging standard for all AudioCodes resources. Recommended minimum tag set: `Environment` (NonProd/Prod), `Application` (AudioCodes-Voice), `Component` (SBC/StackManager/ARM-Configurator/ARM-Router/OVOC), `Region` (AU/US), `CostCentre` (per organisational billing), `Owner` (team or individual), `ManagedBy` (Manual/CloudFormation/StackManager), `BackupPolicy` (Daily/Weekly/None). Document tag application during resource creation and add a tagging verification step to the deployment checklist (Appendix A). Enable AWS Cost Allocation Tags for `Application`, `Environment`, and `CostCentre` in the billing console. |
| **Priority** | Pre-Go-Live |

---

### F-AW-006: VPC Endpoint Multi-AZ Deployment Not Specified

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Resilience / High Availability |
| **Guide Reference** | Section 21, lines 2745-2784 (VPC Endpoints) |
| **Description** | The VPC Endpoints section lists five required Interface Endpoints (EC2, CloudFormation, CloudWatch, STS) and one Gateway Endpoint (S3) but does not specify multi-AZ deployment requirements for the Interface Endpoints. An Interface VPC Endpoint creates an ENI in a specified subnet within an AZ. If the endpoint is deployed in only one AZ and that AZ fails, all resources in the other AZ lose access to the corresponding AWS service via PrivateLink. The cost estimate at line 2783 mentions "2 AZs" ($73/month per region), implying multi-AZ deployment is intended, but this is not stated as a requirement or documented in the configuration steps. |
| **Risk / Impact** | The EC2 Interface Endpoint is explicitly marked as "Critical for HA" (line 2753). If this endpoint is deployed in only one AZ and that AZ fails, the SBC in the surviving AZ cannot reach the EC2 API to perform route table updates during HA failover. This would result in a failed failover — the standby SBC detects the active SBC failure but cannot update the route table or reassign the EIP, causing a complete voice service outage. Line 2781 states "Place EC2 endpoint ENI in the HA subnet" but does not specify that this must be done in the HA subnet of each AZ. |
| **Evidence** | Section 21, line 2753: "EC2 | Interface | ... | **Critical for HA** — must be in HA subnet". Line 2781: "Place EC2 endpoint ENI in the HA subnet to ensure failover API calls do not traverse NAT Gateway." Line 2783: "With 5 required endpoints across 2 AZs: ~$73/month per region" — implies multi-AZ but does not mandate it. No explicit instruction to deploy Interface Endpoints in both AZs. |
| **Recommendation** | Add an explicit requirement that all Interface VPC Endpoints (EC2, CloudFormation, CloudWatch, STS) must be deployed with ENIs in both Availability Zones where SBC instances reside. Amend line 2781 to read: "Place EC2 endpoint ENIs in the HA subnet of each AZ (ap-southeast-2a and ap-southeast-2b) to ensure failover API calls remain available during single-AZ failure." Add this as a prerequisite in Section 19 (HA Prerequisites checklist, line 2259). |
| **Priority** | Pre-Go-Live |

---

### F-AW-007: OVOC 2 TB gp3 Without IOPS Provisioning Analysis

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Storage / Performance |
| **Guide Reference** | Section 4, lines 310-313 (OVOC Specifications); Section 9.4, lines 935 (Compute Requirements Summary); Appendix C, line 3368 (Instance Type Summary) |
| **Description** | The OVOC High Profile specifies m5.4xlarge with "2 TB GP3 SSD" storage. gp3 volumes provide a baseline of 3,000 IOPS and 125 MiB/s throughput regardless of volume size, with the ability to provision up to 16,000 IOPS and 1,000 MiB/s independently. The guide recommends gp3 but does not specify whether additional IOPS provisioning is required. For a 2 TB volume hosting a PostgreSQL analytics database (OVOC `dbems`) that ingests call detail records, QoE metrics, alarm data, and device telemetry from all managed SBCs, the baseline 3,000 IOPS may be insufficient during peak ingestion or when the daily ETL pipeline (Section 22A) executes concurrent queries against six database views. |
| **Risk / Impact** | Under-provisioned IOPS on the OVOC volume would manifest as increased PostgreSQL query latency, slow CDR ingestion, delayed QoE reporting, and potential ETL pipeline timeouts. Section 22A documents that the analytics views expose a rolling 24-hour window; if the ETL extraction is delayed or times out due to slow disk I/O, that day's data is "permanently lost" (line 2918). The OVOC also runs the Device Manager, alarm processing engine, and web application server on the same volume, compounding the I/O demand. |
| **Evidence** | Section 4, line 313: "High Profile | m5.4xlarge | 16 | 64 GiB | 2 TB GP3 SSD". Section 9.4, line 935: "AWS EBS: GP3 SSD 2 TB". Line 338: "All AWS instances should be deployed with appropriate EBS volume types and IOPS provisioning based on workload requirements. GP3 SSD is recommended as the baseline storage tier." This note acknowledges that IOPS provisioning should be considered but provides no sizing guidance. |
| **Recommendation** | Conduct an IOPS sizing analysis for the OVOC volume based on: (1) expected number of managed SBCs and their CDR/QoE reporting rate; (2) ETL query concurrency and scan volume; (3) PostgreSQL WAL write rate during peak ingestion. As a starting point, provision the gp3 volume with at least 6,000 IOPS (2x baseline) for production deployments managing more than 10 SBCs. Monitor `VolumeQueueLength` and `VolumeReadOps`/`VolumeWriteOps` CloudWatch metrics during initial deployment and adjust. Document the provisioned IOPS in the component specifications table. gp3 IOPS provisioning is cost-effective: increasing from 3,000 to 6,000 IOPS adds approximately US$18/month. |
| **Priority** | Pre-Go-Live |

---

### F-AW-008: No Infrastructure-as-Code Templates for Non-SBC Components

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Operational Excellence / Automation |
| **Guide Reference** | Section 18, lines 2211-2220 (Deployment Methods by Component) |
| **Description** | The deployment methodology table shows that all non-SBC components are deployed manually via "AWS EC2 Console / CLI" or "AWS EC2 Console using AudioCodes AMI". Only the Mediant VE SBC is deployed via Infrastructure-as-Code (CloudFormation, orchestrated by Stack Manager). The Stack Manager, ARM Configurator, ARM Router, and OVOC are all manual deployments. This means that five of the nine production VMs have no repeatable, version-controlled deployment template. |
| **Risk / Impact** | Manual deployment introduces configuration drift between environments (NonProd vs Prod), increases deployment time, raises the risk of human error during provisioning (wrong instance type, incorrect security group attachment, missing IAM role), and makes disaster recovery slower (manual recreation of instances). In a cross-region deployment (AU and US), manual provisioning must be repeated for each region with region-specific parameters, compounding the error risk. Without IaC, there is no audit trail of infrastructure changes beyond CloudTrail API logs, which do not capture intent or design rationale. |
| **Evidence** | Section 18, lines 2215-2219: "Stack Manager | AWS EC2 Console / CLI"; "ARM Configurator | AWS EC2 Console using AudioCodes AMI"; "ARM Router | AWS EC2 Console using AudioCodes AMI"; "OVOC | AWS EC2 Console using AudioCodes AMI". Only line 2216 (Mediant VE SBC) references CloudFormation via Stack Manager. |
| **Recommendation** | Develop CloudFormation or Terraform templates for all non-SBC components. At minimum, create templates for: (1) VPC infrastructure (subnets, route tables, security groups, VPC Endpoints) — this is the foundation and should be codified first; (2) Stack Manager EC2 instance with IAM role attachment; (3) ARM Configurator and ARM Router instances; (4) OVOC instance with gp3 volume and IAM role (if applicable). Templates should accept environment-specific parameters (region, VPC ID, subnet IDs, AMI ID, instance type, tags) and output resource ARNs for cross-stack references. Store templates in version control alongside the deployment guide. |
| **Priority** | Post-Deployment (before second environment build) |

---

### F-AW-009: Cross-Region "All/All" Security Group Rules

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Category** | Security / Network Segmentation |
| **Guide Reference** | Section 5, lines 390, 397, 407, 412, 421, 424, 441 (Security Group tables for SBC Internal, SBC External, ARM, OVOC) |
| **Description** | Multiple security groups contain `All | All | Other Region VPC CIDR` rules for cross-region connectivity. Specifically: the SBC Internal Security Group has inbound `All/All` from Other Region VPC CIDR (line 390) and outbound `All/All` to Other Region VPC CIDR (line 397); the SBC External Security Group has inbound `All/All` from Other Region VPC CIDR (line 407) and outbound `All/All` to Other Region VPC CIDR (line 412); the ARM Security Group has inbound `All/All` from Other Region VPC CIDR (line 421) and outbound `All/All` to Other Region VPC CIDR (line 424); and the OVOC Security Group has inbound `All/All` from Other Region VPC CIDR (line 441). These rules effectively permit any protocol and any port between the two regional VPCs, negating the per-port/per-protocol specificity applied to all other rules in these security groups. |
| **Risk / Impact** | The `All/All` cross-region rules create a security group bypass for any traffic sourced from the other region's VPC CIDR. If one region's VPC is compromised, the attacker has unrestricted network access to all voice infrastructure in the other region. This contradicts the careful least-privilege egress design applied to other rules in the same security groups (e.g., Teams Direct Routing CIDRs scoped to specific ports, Microsoft Graph API scoped to specific CIDRs). The Security Group Design Notes at line 446 state "No 0.0.0.0/0 outbound rules. All egress is restricted to specific destinations following the principle of least privilege" — but the `All/All` cross-region rules effectively grant unrestricted access to the entire remote VPC CIDR. |
| **Evidence** | SBC Internal SG, line 390: `Inbound | All | All | Other Region VPC CIDR | Cross-region SBC-to-SBC and management connectivity`. SBC Internal SG, line 397: `Outbound | All | All | Other Region VPC CIDR | Cross-region SBC-to-SBC connectivity`. SBC External SG, line 407: `Inbound | All | All | Other Region VPC CIDR | Cross-region SBC connectivity`. ARM SG, line 421: `Inbound | All | All | Other Region VPC CIDR | Cross-region SBC and ARM Router connectivity`. OVOC SG, line 441: `Inbound | All | All | Other Region VPC CIDR | Cross-region SBC connectivity`. |
| **Recommendation** | Replace `All/All` cross-region rules with specific port and protocol rules for the actual cross-region traffic flows. Based on the guide's documented cross-region requirements, these should be: **SBC-to-SBC (Proxy-to-Proxy):** TCP/UDP 5060-5061 (SIP signalling), UDP 6000-19999 (RTP media) on the Internal interface. **ARM Router cross-region:** TCP 443 (HTTPS management), TCP 8080 (JMS). **OVOC cross-region:** TCP 443 (Device Management), UDP 162 (SNMP traps), TCP 5001 (QoE). If precise port enumeration is not feasible for all flows, consider using a separate "Cross-Region" security group with documented justification for each permitted protocol/port, rather than embedding `All/All` rules in the per-interface security groups. |
| **Priority** | Immediate |

---

### F-AW-010: Stack Manager IAM Policy — ec2:* and cloudformation:*

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Category** | Security / Identity and Access Management |
| **Guide Reference** | Section 20, lines 2482-2501 (Stack Manager IAM Policy); Section 21, lines 2676-2735 (IAM Permissions Required, Permission Justification, Scope Limitation) |
| **Description** | The Stack Manager IAM policy grants `ec2:*` and `cloudformation:*` with `Resource: "*"`. The guide acknowledges this is broad (line 2503: "AudioCodes confirms these broad permissions... are required for Stack Manager to function") and proposes temporal elevation as the primary mitigation. However, during the elevation window, the Stack Manager (or anyone with access to it) can: create or terminate any EC2 instance in the account; modify any security group, route table, or VPC; create or delete any CloudFormation stack; and pass IAM roles to newly created instances (via `iam:PassRole`). The tag-based condition enhancement suggested at lines 2720-2735 includes a caveat that "Not all EC2 actions support tag-based conditions" and that "CloudFormation stack creation may fail if tag conditions block required actions on untagged resources." |
| **Risk / Impact** | During the temporal elevation window, the Stack Manager has effective administrative control over all EC2 and CloudFormation resources in the AWS account. If the Stack Manager instance is compromised during this window (e.g., via an unpatched vulnerability in the Stack Manager application or OS), the attacker gains broad infrastructure control. The `iam:PassRole` permission compounds this risk — a compromised Stack Manager could launch new EC2 instances with arbitrary IAM roles. Even with temporal elevation, deployment operations may last hours (initial SBC HA deployment, software upgrades), providing a substantial attack window. The `iam:CreateServiceLinkedRole` permission (line 2496) allows creation of service-linked roles, which could be abused to enable AWS services not intended for this account. |
| **Evidence** | Section 20, lines 2488-2497: `"ec2:*"`, `"cloudformation:*"`, `"cloudwatch:DeleteAlarms"`, `"cloudwatch:PutMetricAlarm"`, `"iam:PassRole"`, `"iam:ListInstanceProfiles"`, `"iam:CreateServiceLinkedRole"` — all with `"Resource": "*"`. Section 21, line 2701: "Cannot be reduced (AudioCodes confirmed). Mitigate via temporal IAM elevation." |
| **Recommendation** | (1) Accept that `ec2:*` and `cloudformation:*` are a vendor requirement and implement temporal elevation as documented. (2) Add a Permission Boundary to the Stack Manager IAM role to cap the maximum permissions even when the policy is attached. The boundary should deny: `ec2:DeleteVpc`, `ec2:DeleteSubnet`, `iam:CreateUser`, `iam:CreateRole` (except the SBC role), and any action outside `ec2:*`, `cloudformation:*`, and the specified CloudWatch/IAM actions. (3) Scope `iam:PassRole` to only the SBC IAM role ARN, not all roles: add a `Resource` condition restricting PassRole to `arn:aws:iam::<ACCOUNT_ID>:role/AudioCodes-SBC-Role`. (4) Enable CloudTrail alerting (via EventBridge + SNS) for any API call made by the Stack Manager IAM role outside the approved change window. (5) Deploy the Stack Manager in a dedicated AWS account (voice infrastructure account) if organisational architecture permits, to blast-radius the `ec2:*` scope to voice resources only. |
| **Priority** | Immediate |

---

### F-AW-011: No Auto-Scaling or Elasticity Consideration

| Attribute | Detail |
|-----------|--------|
| **Severity** | Low |
| **Category** | Scalability / Architecture |
| **Guide Reference** | Section 3, lines 131-161 (Architecture Overview); Section 19, lines 2223-2284 (HA Considerations) |
| **Description** | All components are deployed as fixed-count, statically-sized EC2 instances. The architecture uses 5 VMs in non-production and 9 VMs in production with no auto-scaling groups, launch templates, or elasticity mechanisms. The SBC HA model is 1+1 Active/Standby (not Active/Active), meaning the standby instance consumes resources but handles no traffic during normal operation. The ARM Router is described as "1+ per region" (Section 4, line 298) suggesting potential for scaling, but no scaling trigger or procedure is documented. |
| **Risk / Impact** | The static architecture cannot respond to unexpected load increases (e.g., a surge in concurrent calls during an emergency event, or a spike in OVOC QoE data ingestion during a major incident). The 1+1 SBC HA model means 50% of SBC compute capacity is idle during normal operation. While this is standard for SBC HA (and appropriate for the voice use case), the guide does not discuss capacity planning, load testing thresholds, or scaling procedures for any component. If call volumes grow beyond the m5n.large SBC's capacity, the only scaling option is manual instance type change with downtime. |
| **Evidence** | Section 3, lines 137-160: Fixed VM counts (5 NonProd, 9 Prod). Section 19, lines 2228-2229: "Mode | 1+1 Active/Standby". Section 4, line 298: "Router | m4.large | 2 | 8 GiB | 1+ per region" — the "1+" implies potential scaling but no mechanism is documented. No mention of Auto Scaling Groups, Launch Templates, or capacity planning thresholds anywhere in the document. |
| **Recommendation** | Document the capacity limits and scaling procedures for each component. For the SBC: document the maximum concurrent sessions for the m5n.large instance type (per AudioCodes licensing and performance testing), the procedure for vertical scaling (instance type change), and the expected downtime during scaling. For the ARM Router: document when to add a second router instance and how to configure load distribution. Consider placing the Stack Manager in an Auto Scaling Group (min=0, max=1, desired=0) that can be scaled up on demand for Day 2 operations, reinforcing the temporal elevation pattern. |
| **Priority** | Post-Deployment |

---

### F-AW-012: No Cost Optimisation Analysis

| Attribute | Detail |
|-----------|--------|
| **Severity** | Low |
| **Category** | Cost Management |
| **Guide Reference** | Section 4, lines 163-338 (Component Specifications); Appendix C, lines 3358-3369 (Instance Type Summary) |
| **Description** | The guide specifies instance types and storage but provides no cost analysis, cost optimisation strategy, or recommendations for Reserved Instances, Savings Plans, or Spot usage. The production environment runs 9 VMs continuously (6 in AU, 3 in US), representing a significant annual compute cost. The non-production environment runs 5 VMs that may not require 24/7 operation. No guidance on non-production scheduling (stop/start outside business hours) or purchasing commitments is provided. |
| **Risk / Impact** | Without cost optimisation, the organisation pays on-demand pricing for all instances. Rough estimate for production on-demand pricing (as of March 2026, ap-southeast-2): 2x m5n.large SBC (~US$139/month each), 1x t3.medium Stack Manager (~US$30/month), 1x m5.4xlarge OVOC (~US$557/month), 1x m4.xlarge ARM Configurator (~US$146/month), 1x m4.large ARM Router (~US$73/month), plus US region instances. Total estimated on-demand cost: approximately US$1,500-2,000/month for production AU alone. A 1-year Compute Savings Plan at "No Upfront" typically provides 20-30% savings, representing US$4,000-7,000/year in avoidable cost across both regions. |
| **Evidence** | No content related to Reserved Instances, Savings Plans, Spot Instances, cost estimation, or non-production scheduling exists in the document. The Section 21 cost estimate for VPC Endpoints (~$73/month per region, line 2783) is the only cost-related content in the entire guide. |
| **Recommendation** | Add a Cost Optimisation section covering: (1) Annual cost estimate for all environments (NonProd + Prod AU + Prod US) at on-demand pricing; (2) Savings Plan or Reserved Instance recommendation for production instances that run 24/7 (SBCs, OVOC, ARM); (3) Non-production scheduling — implement start/stop automation using AWS Instance Scheduler or EventBridge + Lambda to run non-production VMs only during business hours (e.g., 07:00-19:00 AEST weekdays), reducing non-production compute cost by approximately 65%; (4) Stack Manager cost note — t3.medium at ~$30/month is already low-cost, but could be stopped when not in use (aligned with temporal IAM elevation pattern); (5) EBS snapshot cost consideration for the backup strategy (F-AW-002). |
| **Priority** | Post-Deployment |

---

### F-AW-013: r4.large Listed as Instance Option — Previous Generation

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Compute / Cost Optimisation |
| **Guide Reference** | Section 4, lines 176-181 (Recommended EC2 Instance Types table) |
| **Description** | The SBC instance type recommendations table includes `r4.large` as an option for "Without Transcoding (Higher capacity)". The r4 family is a previous-generation memory-optimised instance type, superseded by r5 (2018), r6i (2021), and r7i (2023). The guide includes a parenthetical note at line 179: "r4 is previous-generation; consider r5 or r6i for better price-performance" — the same pattern seen with the m4 instances in F-AW-001. However, unlike the ARM components where m4 is the only specified option, the r4 entry is one of four SBC instance type options. |
| **Risk / Impact** | The risks are identical to F-AW-001 (older Xen hypervisor, no Nitro security features, potential Savings Plan ineligibility, future deprecation risk). Since r4.large is listed as an alternative option rather than the primary recommendation, the impact is lower — but its presence in the guide could lead an implementation team to select it without understanding the implications. The guide already recommends m5n.large as the primary SBC instance type in the Compute Requirements Summary (Section 9.4, line 933), creating an inconsistency between the "Recommended" table and the "Compute Requirements" table. |
| **Evidence** | Section 4, line 179: "Without Transcoding (Higher capacity) | r4.large | 2 | 15.25 GiB | Memory optimized (r4 is previous-generation; consider r5 or r6i for better price-performance)". Section 9.4, line 933: "VM for Mediant VE Proxy SBC (HA Pair) | AWS | m5n.large | 8 GiB | 20 GB | 2 vCPU" — no r4 mentioned in the definitive compute table. |
| **Recommendation** | Replace `r4.large` with `r5.large` or `r6i.large` in the Recommended EC2 Instance Types table (Section 4). If the r4.large entry exists because the AudioCodes AMI historically required it, validate AMI compatibility with r5/r6i and update accordingly. Alternatively, remove the r4 entry entirely if the m5n.large recommendation in Section 9.4 is the definitive sizing for this deployment. Ensure the Recommended Instance Types table and the Compute Requirements Summary table are consistent. |
| **Priority** | Immediate |

---

### F-AW-014: No Disaster Recovery Strategy

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Resilience / Business Continuity |
| **Guide Reference** | Section 3, lines 131-161 (Architecture Overview); Section 19, lines 2223-2284 (High Availability Considerations) |
| **Description** | The guide documents HA within a single VPC across two AZs for the SBC pair but does not address disaster recovery (DR) for any component. There is no cross-region failover strategy for the management components (Stack Manager, OVOC, ARM Configurator), which are all single instances deployed in the Australian region only. If the entire ap-southeast-2 region becomes unavailable: (1) the Stack Manager cannot perform Day 2 operations for the US SBC pair; (2) OVOC monitoring, QoE data collection, and device management is lost for all regions; (3) the ARM Configurator (centralised routing policy engine) is unavailable, though ARM Routers continue with last-known configuration. Section 19, line 2282 notes: "Configurator Failure Handling | Routers continue with last known configuration" — this is resilience, not DR. |
| **Risk / Impact** | A full region failure is a low-probability event, but the impact is significant: complete loss of voice management, monitoring, and routing policy updates. The US SBC pair would continue to route calls (using cached ARM routing tables and existing HA configuration), but no configuration changes, software updates, or alarm processing would be possible until the AU region recovers. OVOC data loss is compounded by the 24-hour analytics window — any outage exceeding 24 hours results in permanent QoE data loss (as per Section 22A, line 2918). The guide explicitly states cross-region SBC HA is not supported (line 849), which is an accepted architectural constraint, but management component DR is not discussed. |
| **Evidence** | Section 2, line 102-106: "We are NOT implementing: Cross-VPC HA, Cross-region HA for SBCs, AWS Transit Gateway for Virtual IP routing between VPCs." Section 3, lines 147-158: OVOC, ARM Configurator, and Stack Manager are single instances in AU only. Section 19, line 2282: "Configurator Failure Handling | Routers continue with last known configuration." No DR section, no RTO/RPO definitions, no cross-region recovery procedures. |
| **Recommendation** | Add a Disaster Recovery section covering: (1) RTO and RPO definitions for each component; (2) Cross-region AMI copy procedure — maintain current AMIs for Stack Manager, OVOC, and ARM Configurator in the US region for rapid re-deployment; (3) OVOC database backup replication to the US region (S3 cross-region replication for pg_dump exports); (4) ARM Configurator routing policy export and cross-region storage; (5) Documented recovery procedure: if ap-southeast-2 fails, deploy management stack in us-east-1 from backup AMIs and database exports; (6) Annual DR test procedure. For OVOC specifically, consider whether a warm standby in the US region is justified by the 24-hour data retention constraint. |
| **Priority** | Pre-Go-Live |

---

### F-AW-015: SBC IAM Role — Resource: * for Describe Actions

| Attribute | Detail |
|-----------|--------|
| **Severity** | Low |
| **Category** | Security / IAM |
| **Guide Reference** | Section 20, lines 2531-2539 (SBC IAM Policy — AllowDescribeActions); lines 2572-2574 (Design Rationale) |
| **Description** | The SBC IAM policy's `AllowDescribeActions` statement grants `ec2:DescribeAddresses`, `ec2:DescribeNetworkInterfaceAttribute`, and `ec2:DescribeNetworkInterfaces` with `Resource: "*"`. The guide correctly explains at line 2574: "AWS Describe actions do not support resource-level scoping; required for SBC to query its own network state." This is factually accurate — these three EC2 Describe actions indeed require `Resource: "*"` as per AWS IAM documentation. However, the guide does not document the risk implication: these permissions allow the SBC role to enumerate all Elastic IPs, all ENIs, and all ENI attributes across the entire AWS account. |
| **Risk / Impact** | The risk is informational/low. The SBC role can read (but not modify) network configuration for all EC2 resources in the account. This provides network topology visibility to anyone with access to the SBC instance's IAM credentials (via instance metadata). In a shared account with other workloads, this could expose network architecture details to the SBC application or any process running on the SBC instance. However, since the Describe actions are read-only and the SBC role has no write permissions beyond the specifically-scoped `ReplaceRoute` and `AssociateAddress`, the practical risk is limited to information disclosure. |
| **Evidence** | Section 20, lines 2533-2538: Three Describe actions with `"Resource": "*"`. Line 2574: "AWS Describe actions do not support resource-level scoping." |
| **Recommendation** | No change to the IAM policy is required (AWS does not support resource-level scoping for these actions). However, add a security note documenting that these permissions provide account-wide read access to EC2 network configuration. This ensures the risk is visible in security reviews and audit assessments. If the organisation uses a dedicated AWS account for voice infrastructure (as recommended in F-AW-010), the blast radius of this information disclosure is limited to voice resources only. Additionally, consider adding an IAM policy condition using `aws:SourceVpc` or `ec2:Vpc` to constrain the Describe actions to the voice VPC (note: not all Describe actions support VPC-based conditions — test before deploying). |
| **Priority** | Post-Deployment |

---

## 5. Risk Matrix

| Finding ID | Title | Severity | Likelihood | Impact | Risk Rating |
|------------|-------|----------|------------|--------|-------------|
| F-AW-001 | Previous-gen instances (m4) for ARM | High | High | Medium | **High** |
| F-AW-002 | No backup/snapshot strategy | High | Medium | High | **High** |
| F-AW-003 | Single-AZ NAT Gateway risk | High | Low | High | **High** |
| F-AW-004 | No CloudWatch alarms defined | Medium | High | Medium | **Medium** |
| F-AW-005 | No tagging strategy | Medium | High | Low | **Medium** |
| F-AW-006 | VPC Endpoint multi-AZ deployment not specified | Medium | Low | High | **Medium** |
| F-AW-007 | OVOC gp3 without IOPS provisioning | Medium | Medium | Medium | **Medium** |
| F-AW-008 | No IaC templates for non-SBC components | Medium | High | Medium | **Medium** |
| F-AW-009 | Cross-region All/All security group rules | High | Medium | High | **High** |
| F-AW-010 | Stack Manager IAM ec2:* and cloudformation:* | High | Low | Critical | **High** |
| F-AW-011 | No auto-scaling or elasticity | Low | Low | Medium | **Low** |
| F-AW-012 | No cost optimisation analysis | Low | High | Low | **Low** |
| F-AW-013 | r4.large listed as option — previous gen | Medium | Medium | Low | **Medium** |
| F-AW-014 | No disaster recovery strategy | Medium | Low | High | **Medium** |
| F-AW-015 | SBC IAM Describe Resource: * | Low | Low | Low | **Low** |

---

## 6. Gap Analysis — AWS Best Practices

| AWS Best Practice Area | Guide Coverage | Gap Assessment |
|------------------------|----------------|----------------|
| **IAM Least Privilege** | Partial — SBC IAM role is well-scoped; Stack Manager IAM is acknowledged as broad with mitigations | Stack Manager policy is a vendor-imposed constraint; mitigations are documented but could be strengthened with Permission Boundaries and scoped `iam:PassRole` |
| **Multi-AZ Resilience** | Partial — SBC HA spans two AZs; VPC Endpoints costed for 2 AZs | NAT Gateway multi-AZ not documented; VPC Endpoint multi-AZ not mandated; management components (OVOC, ARM Configurator, Stack Manager) are all single-instance, single-AZ |
| **Backup and Recovery** | Not covered | No EBS snapshots, AMI backups, database exports, or RTO/RPO definitions for any component |
| **Monitoring and Alerting** | Minimal — IAM permissions and VPC Endpoint for CloudWatch exist; no alarms defined | CloudWatch infrastructure exists architecturally but is empty — no alarms, no dashboards, no alerting targets |
| **Tagging Governance** | Minimal — Two IAM condition tags (Env, App) defined; no comprehensive strategy | No mandatory tag set, no cost allocation tags, no tag enforcement policy |
| **Infrastructure as Code** | Partial — SBC deployed via CloudFormation (Stack Manager); all other components manual | Five of nine production VMs have no IaC template; VPC infrastructure is manual |
| **Cost Optimisation** | Not covered | No Savings Plan analysis, no non-production scheduling, no cost estimation |
| **Security Group Design** | Strong for per-service rules; weak for cross-region rules | Per-interface SBC security groups are well-designed; cross-region `All/All` rules undermine the otherwise strong posture |
| **Disaster Recovery** | Not covered | No cross-region recovery strategy for management components; no RTO/RPO; no DR testing procedure |
| **Encryption at Rest** | Not mentioned | No guidance on EBS encryption (default or CMK), no mention of AWS KMS for volume encryption or secret management |
| **Logging and Audit** | Partial — CloudTrail mentioned for IAM audit; VPC Flow Logs mentioned in Section 22A | No guidance on enabling VPC Flow Logs for the voice VPC; no AWS Config rules; no GuardDuty integration |
| **Secrets Management** | Partial — Break glass accounts reference a "secure secret repository" | No specific AWS Secrets Manager or Systems Manager Parameter Store integration for RADIUS shared secrets, database credentials, or API keys |
| **Instance Lifecycle** | Not covered | No patching strategy for EC2 instances; no AMI update pipeline; no Systems Manager integration |

---

## 7. Recommendations Summary

### Immediate (Before Non-Production Deployment)

| Priority | Finding | Action |
|----------|---------|--------|
| 1 | F-AW-001 | Replace m4.xlarge/m4.large with m5.xlarge/m5.large (or m6i equivalents) for ARM components across all specification tables |
| 2 | F-AW-013 | Replace r4.large with r5.large or r6i.large in the SBC Recommended Instance Types table, or remove the entry if m5n.large is the definitive sizing |
| 3 | F-AW-009 | Replace cross-region `All/All` security group rules with specific port/protocol rules for documented cross-region traffic flows |
| 4 | F-AW-010 | Scope `iam:PassRole` to the SBC role ARN; add Permission Boundary to Stack Manager IAM role; enable CloudTrail alerting for Stack Manager API calls |

### Pre-Go-Live (Before Production Deployment)

| Priority | Finding | Action |
|----------|---------|--------|
| 5 | F-AW-002 | Develop and document backup strategy: EBS snapshots (daily, 14-day retention), OVOC database backup, SBC config export, AMI golden images |
| 6 | F-AW-003 | Document multi-AZ NAT Gateway requirement (if used) or mandate VPC Endpoints as the sole API access path with multi-AZ endpoint deployment |
| 7 | F-AW-006 | Add explicit requirement for VPC Endpoint ENIs in both AZs; update HA prerequisites checklist |
| 8 | F-AW-004 | Define baseline CloudWatch alarms for all component types with SNS notification targets |
| 9 | F-AW-005 | Define mandatory tagging standard; enable cost allocation tags; add tagging verification to deployment checklist |
| 10 | F-AW-007 | Conduct OVOC gp3 IOPS sizing analysis; provision minimum 6,000 IOPS for production; document in component specifications |
| 11 | F-AW-014 | Define RTO/RPO for each component; establish cross-region AMI copy and database backup replication; document recovery procedures |

### Post-Deployment (Continuous Improvement)

| Priority | Finding | Action |
|----------|---------|--------|
| 12 | F-AW-008 | Develop CloudFormation/Terraform templates for VPC infrastructure and non-SBC components before second environment build |
| 13 | F-AW-012 | Conduct cost optimisation analysis; implement Savings Plans for production; implement non-production scheduling |
| 14 | F-AW-011 | Document capacity limits and scaling procedures for each component; consider ASG for Stack Manager |
| 15 | F-AW-015 | Add security note documenting account-wide Describe visibility; evaluate dedicated AWS account for voice infrastructure |

---

## 8. Action Items Register

| Item | Finding | Action | Owner | Priority | Target Date |
|------|---------|--------|-------|----------|-------------|
| 1 | F-AW-001 | Validate AudioCodes AMI compatibility with m5/m6i; update ARM instance types in guide | Cloud Engineering | High | 14 March 2026 |
| 2 | F-AW-013 | Replace r4.large with r5.large or remove from SBC instance type table | Cloud Engineering | High | 14 March 2026 |
| 3 | F-AW-009 | Enumerate cross-region port/protocol requirements; replace All/All rules | Network Security | High | 21 March 2026 |
| 4 | F-AW-010 | Add Permission Boundary; scope iam:PassRole; configure CloudTrail alerting | Security Engineering | High | 21 March 2026 |
| 5 | F-AW-002 | Design backup strategy; implement AWS Backup policies; document procedures | Cloud Engineering | High | 28 March 2026 |
| 6 | F-AW-003 | Document multi-AZ NAT GW or mandate VPC Endpoints; update HA prerequisites | Cloud Engineering | High | 28 March 2026 |
| 7 | F-AW-006 | Specify multi-AZ VPC Endpoint deployment; update Section 21 and HA checklist | Cloud Engineering | Medium | 28 March 2026 |
| 8 | F-AW-004 | Define CloudWatch alarm set; create SNS topic; document alarm procedures | Cloud Operations | Medium | 4 April 2026 |
| 9 | F-AW-005 | Define tagging standard; create tag policy; update deployment checklist | Cloud Governance | Medium | 4 April 2026 |
| 10 | F-AW-007 | Conduct OVOC IOPS analysis; update gp3 provisioning in guide | Cloud Engineering | Medium | 4 April 2026 |
| 11 | F-AW-014 | Define DR strategy; implement cross-region AMI copy; document procedures | Cloud Engineering | Medium | 18 April 2026 |
| 12 | F-AW-008 | Develop IaC templates for VPC and non-SBC components | Cloud Engineering | Medium | 30 April 2026 |
| 13 | F-AW-012 | Conduct cost analysis; implement Savings Plans; implement non-prod scheduling | Cloud FinOps | Low | 30 May 2026 |
| 14 | F-AW-011 | Document capacity limits and scaling procedures | Cloud Engineering | Low | 30 May 2026 |
| 15 | F-AW-015 | Document Describe action scope risk; evaluate dedicated account model | Security Engineering | Low | 30 June 2026 |

---

## Appendix A: Sections Reviewed

| Section | Lines | Key Content Assessed |
|---------|-------|---------------------|
| 1. Executive Summary | 45-75 | Scope and key takeaways |
| 2. Critical Findings | 78-128 | Stack Manager requirements, API access, HA scope |
| 3. Architecture Overview | 131-161 | VM counts, regional topology |
| 4. Component Specifications | 163-338 | Instance types, storage, compute sizing, IAM roles |
| 5. AWS Infrastructure Requirements | 342-499 | VPC, subnets, security groups, publishing patterns |
| 9. SBC Provisioning | 801-945 | HA provisioning, compute requirements |
| 18. Deployment Methodology | 2205-2220 | Deployment methods per component |
| 19. High Availability Considerations | 2223-2368 | SBC HA architecture, failover, ARM HA, SIP trunk HA |
| 20. IAM Permissions and Security | 2476-2604 | Stack Manager IAM, SBC IAM, VPC Endpoints, role creation steps |
| 21. Cyber Security Considerations | 2608-2843 | Security architecture, attack surface, Stack Manager risk assessment, compliance |
| 22. Licensing Considerations | 2846-2874 | Procurement models |
| 22A. OVOC Data Analytics | 2877-3156 | PostgreSQL access, ETL, audit |
| Appendix A | 3219-3278 | Deployment checklist completeness |
| Appendix C | 3314-3369 | Instance type summary, port summary |

---

## Appendix B: Standards and References

| Standard / Reference | Version | Relevance |
|----------------------|---------|-----------|
| AWS Well-Architected Framework | 2025 | Primary assessment framework — Reliability, Security, Cost Optimisation, Operational Excellence pillars |
| AWS Security Best Practices — IAM | Current | IAM policy evaluation, least privilege assessment |
| AWS EC2 Instance Types | Current (March 2026) | Instance family currency and capability comparison |
| CIS AWS Foundations Benchmark | v3.0 | Security configuration baseline for VPC, IAM, CloudTrail, monitoring |
| AWS VPC Security Best Practices | Current | Security group design, VPC Endpoint architecture, NAT Gateway resilience |
| AWS Reliability Pillar Whitepaper | 2025 | Multi-AZ design patterns, backup and recovery, disaster recovery |
| AWS Cost Optimisation Pillar Whitepaper | 2025 | Savings Plans, Reserved Instances, right-sizing, scheduling |
| ACSC Cloud Security Guidelines | 2025 | Australian Government cloud security requirements (relevant for AU-hosted infrastructure) |
| AWS EBS User Guide — gp3 Performance | Current | gp3 baseline IOPS (3,000), provisioned IOPS sizing |
| AWS IAM User Guide — Actions, Resources, and Condition Keys for EC2 | Current | Resource-level permission support for EC2 Describe actions |
| AudioCodes Mediant VE SBC for AWS Installation Manual | v7.4 / v7.6 | Vendor-specified instance types and deployment requirements |
| AudioCodes Stack Manager User's Manual | v7.4 / v7.6 | Stack Manager IAM requirements and deployment model |

---

**End of Report**
