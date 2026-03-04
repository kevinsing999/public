# Cross-Cutting Findings — AudioCodes AWS Deployment Guide v2.6

## Findings That Appear Across Multiple Analyst Reports

**Date:** 4 March 2026
**Source Reports:** 5 Analyst Review Reports (Cybersecurity, AWS Cloud, SBC Engineer, Solution Architect, Consultant)

---

## Overview

This document consolidates findings that were independently identified by two or more analyst reports, indicating systemic issues that transcend any single discipline. Cross-cutting findings carry higher architectural significance because they affect multiple stakeholder perspectives and require coordinated remediation across teams.

**Total cross-cutting themes identified:** 10

---

## CC-01: Unencrypted Internal SIP Signalling

| Reports Identifying | Finding IDs |
|---------------------|-------------|
| Cybersecurity Analyst | F-CS-003 |
| SBC Engineer | F-SB-005, F-SB-011 |
| Solution Architect | F-SA-009 (related — cross-region All/All rules) |

**Consensus:** Internal SIP signalling between Proxy and Downstream SBCs uses unencrypted UDP (port 5060) with no SRTP for media. This contradicts the guide's own firewall recommendation (Section 16.1) that TLS is recommended for inter-device SIP trunks. The Proxy-to-Proxy trunk (AU ↔ US) traverses international WAN links without encryption. All three reports independently flagged this as a security gap that warrants immediate resolution.

**Coordinated Action Required:** Voice Engineering + Security must make and document the encryption decision for internal trunks. If TLS/SRTP is adopted, the SIP Interface, IP Profile, and TLS Context configurations must be updated across all SBC roles.

---

## CC-02: Stack Manager IAM Over-Privilege (ec2:* / cloudformation:*)

| Reports Identifying | Finding IDs |
|---------------------|-------------|
| Cybersecurity Analyst | F-CS-002 |
| AWS Cloud Engineer | F-AW-010 |
| Solution Architect | F-SA-002 (related — single-region SPOF) |

**Consensus:** The Stack Manager's IAM policy grants `ec2:*` and `cloudformation:*` with `Resource: "*"`, providing unrestricted EC2 and CloudFormation control across all regions. While AudioCodes confirms these permissions cannot be reduced, all three reports independently identified this as a risk requiring mitigation. The guide's temporal elevation pattern is a good compensating control but is manual and process-dependent.

**Coordinated Action Required:** Cloud Engineering + Security must implement the temporal elevation pattern with automated policy attach/detach via a runbook or pipeline. CloudTrail alerting should trigger on Stack Manager IAM policy attachment events.

---

## CC-03: Cross-Region All/All Security Group Rules

| Reports Identifying | Finding IDs |
|---------------------|-------------|
| Cybersecurity Analyst | F-CS-012 |
| AWS Cloud Engineer | F-AW-009 |
| Solution Architect | F-SA-009 |

**Consensus:** SBC Internal, ARM, and OVOC security groups all contain `All protocols / All ports` inbound/outbound rules for the other region's VPC CIDR. Three independent reviews flagged this as contradicting the otherwise carefully crafted per-service port restrictions elsewhere in the security group design. All three recommend replacing with specific port-based rules matching documented integration points.

**Coordinated Action Required:** Cloud Engineering must enumerate the specific cross-region connectivity requirements (SIP, RTP, HTTPS, SNMP, syslog) and replace All/All rules with port-scoped rules before production deployment.

---

## CC-04: No Backup or Disaster Recovery Strategy

| Reports Identifying | Finding IDs |
|---------------------|-------------|
| AWS Cloud Engineer | F-AW-002, F-AW-014 |
| Solution Architect | F-SA-001, F-SA-002, F-SA-003, F-SA-013 |
| Consultant | F-CO-001 (operational runbooks for backup/restore) |

**Consensus:** No backup strategy (EBS snapshots, AMI backups, configuration exports) is defined for any component. No disaster recovery strategy addresses regional failure. The ARM Configurator's embedded database, OVOC's 24-hour data retention, and Stack Manager's single-instance model all represent data loss risks. Multiple reports independently identified the absence of RTO/RPO definitions.

**Coordinated Action Required:** Cloud Engineering + Voice Engineering must define: (1) backup schedule per component (daily EBS snapshots minimum), (2) cross-region backup replication, (3) RTO/RPO targets, (4) documented recovery procedures.

---

## CC-05: No Monitoring or Alerting Specification

| Reports Identifying | Finding IDs |
|---------------------|-------------|
| Cybersecurity Analyst | F-CS-007 (no GuardDuty/SecurityHub) |
| AWS Cloud Engineer | F-AW-004 (no CloudWatch alarms) |
| Consultant | F-CO-005 (no monitoring/alerting spec) |

**Consensus:** The guide grants CloudWatch alarm permissions but defines no alarms. No OVOC alert thresholds, no SNMP trap responses, and no escalation paths are specified. The Cybersecurity report additionally notes the absence of AWS security services (GuardDuty, SecurityHub, CloudTrail alerting). All three reports agree that the operations team has no proactive visibility into platform health.

**Coordinated Action Required:** Voice Engineering + Cloud Engineering + Security must collaboratively define the monitoring specification covering: AWS-layer health (CloudWatch), application-layer health (OVOC/SNMP), security monitoring (GuardDuty/CloudTrail), and escalation paths.

---

## CC-06: NTP Authentication Mode = None

| Reports Identifying | Finding IDs |
|---------------------|-------------|
| Cybersecurity Analyst | F-CS-006 |
| SBC Engineer | F-SB-015 |

**Consensus:** NTP is configured with Authentication Mode set to None (Section 13.1). Both reports identify the risk of NTP poisoning affecting TLS certificate validation and CDR timestamp accuracy, though both rate the risk as Low given the internal network context. The SBC Engineer report notes that AWS internal NTP (169.254.169.123) does not support authentication.

**Coordinated Action Required:** Document the NTP authentication decision rationale. If enterprise NTP infrastructure supports authentication, enable it. If using AWS internal NTP, accept the inherent trust model.

---

## CC-07: Credential Rotation Lacks Automation

| Reports Identifying | Finding IDs |
|---------------------|-------------|
| Cybersecurity Analyst | F-CS-008, F-CS-011 |
| Consultant | F-CO-010 |

**Consensus:** Multiple credential types (Entra ID client secrets, break glass passwords, RADIUS shared secrets, SBC local passwords) rely on manual rotation with calendar reminders. Both the Cybersecurity and Consultant reports independently flagged this as an operational risk where expired credentials cause service failures and unrotated credentials persist as attack vectors.

**Coordinated Action Required:** Security + Cloud Engineering must implement automated credential expiry monitoring (alerts at 60/30/7 days before expiry) and evaluate PAM integration for break glass accounts.

---

## CC-08: Document Maturity — 14 Revisions in 8 Days

| Reports Identifying | Finding IDs |
|---------------------|-------------|
| Solution Architect | F-SA-011 |
| Consultant | F-CO-015 |

**Consensus:** Both reports independently flagged the rapid revision pace (14 versions, 8 days) as a design stability concern. The authentication model changed three times in three days (Entra ID → LDAPS → RADIUS). Both recommend a design freeze with stakeholder sign-off and a consistency review before implementation.

**Coordinated Action Required:** Solution Architect + Project Manager must obtain formal design freeze sign-off and schedule a consistency review against v2.6.

---

## CC-09: No Incident Response Procedure for Voice Infrastructure

| Reports Identifying | Finding IDs |
|---------------------|-------------|
| Cybersecurity Analyst | F-CS-015 |
| Consultant | F-CO-009 |

**Consensus:** Neither cybersecurity nor operational perspectives found any incident response procedure for voice infrastructure. Both reports recommend voice-specific severity classification, escalation matrices, diagnostic checklists, and communication plans. The break glass procedures (Section 17) provide emergency access but no incident management framework.

**Coordinated Action Required:** Voice Engineering + Security + Service Management must develop a voice-specific incident response plan that integrates with the organisation's existing ITSM processes.

---

## CC-10: Excessive Configuration Deferral

| Reports Identifying | Finding IDs |
|---------------------|-------------|
| SBC Engineer | F-SB-001, F-SB-002, F-SB-003, F-SB-004, F-SB-008, F-SB-010, F-SB-012, F-SB-013 |
| Solution Architect | F-SA-007 |
| Consultant | F-CO-001 (operational procedures absent) |

**Consensus:** At least 15 configuration areas are deferred to "implementation time" with placeholder values. The SBC Engineer report identifies specific technical gaps (codecs, DTMF, QoS, CAC, emergency calling). The Solution Architect identifies this as a design maturity issue. The Consultant notes that the absence of defined procedures compounds the problem — not only is the configuration undefined, but the process for defining it is also undefined.

**Coordinated Action Required:** Voice Engineering must produce a supplementary SBC Configuration Workbook resolving all deferred parameters before implementation begins. The Solution Architect should triage deferred items into: site-specific (expected), design decisions (require review), and vendor-dependent (require AudioCodes consultation).

---

## Cross-Cutting Findings Summary Matrix

| CC ID | Theme | Reports | Highest Severity | Coordinated Owner |
|-------|-------|---------|-------------------|-------------------|
| CC-01 | Unencrypted internal SIP | CS, SB, SA | High | Voice + Security |
| CC-02 | Stack Manager IAM over-privilege | CS, AW, SA | High | Cloud + Security |
| CC-03 | Cross-region All/All SG rules | CS, AW, SA | Medium | Cloud Engineering |
| CC-04 | No backup/DR strategy | AW, SA, CO | High | Cloud + Voice |
| CC-05 | No monitoring/alerting | CS, AW, CO | Critical | Voice + Cloud + Security |
| CC-06 | NTP auth = None | CS, SB | Low | Voice Engineering |
| CC-07 | Credential rotation no automation | CS, CO | Medium | Security + Cloud |
| CC-08 | Document maturity (14 revisions) | SA, CO | Medium | Architect + PM |
| CC-09 | No incident response procedure | CS, CO | High | Voice + Security + SM |
| CC-10 | Excessive configuration deferral | SB, SA, CO | Critical | Voice Engineering |

---

*End of Cross-Cutting Findings*
