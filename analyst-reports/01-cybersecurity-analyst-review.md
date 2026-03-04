# Cybersecurity Analyst Review Report

## AudioCodes AWS Deployment Guide v2.6

| Field | Detail |
|-------|--------|
| **Report ID** | CSR-2026-001 |
| **Document Under Review** | AudioCodes SBC - Unified Deployment & Configuration Guide v2.6 |
| **Document Date** | 13 February 2026 |
| **Review Date** | 4 March 2026 |
| **Reviewer Role** | Senior Cybersecurity Analyst / Security Architect |
| **Classification** | Internal - Restricted |
| **Finding ID Prefix** | F-CS |

---

## 1. Executive Summary

### Overall Security Rating: CONDITIONAL APPROVAL

The AudioCodes AWS Deployment Guide v2.6 is a comprehensive engineering document that demonstrates mature awareness of cloud infrastructure security, network segmentation, and identity management. It is clear that security has been considered throughout the design process rather than bolted on as an afterthought. The guide's treatment of VPC Endpoints (PrivateLink), least-privilege SBC IAM policies with tag-based conditions, cloud east-west firewall inspection, and dual external publishing patterns reflects a well-considered security architecture.

However, this review has identified 16 substantive findings across identity and access management, data protection, network security, and operational security domains. Three findings are rated Critical or High and must be addressed before production deployment.

### Top 3 Findings

1. **F-CS-001 (Critical) -- MFA Gap on SBC Management Interfaces.** RADIUS-based authentication via Cisco ISE does not natively enforce multi-factor authentication on SBC management sessions. Section 10.4 explicitly acknowledges this limitation. Given that SBC management provides full control over voice routing, call interception configuration, and security policies, this represents a significant access control gap.

2. **F-CS-002 (High) -- Stack Manager IAM Over-Privilege.** The Stack Manager IAM policy (Section 20) grants `ec2:*` and `cloudformation:*` with `Resource: "*"`, providing full EC2 control across the entire AWS account. Even with the documented temporal elevation pattern, the standing policy definition permits unrestricted EC2 and CloudFormation actions when attached.

3. **F-CS-003 (High) -- Internal SIP Signalling Unencrypted.** Section 14.1 configures all internal SIP interfaces with `TLS Port = 0` (disabled), and Section 15.1 sets `Media Security = "Not Secured"` for all internal trunks. SIP signalling and RTP media between the Proxy SBC and downstream SBCs, PBX systems, and endpoints traverse the internal network in cleartext.

### Go/No-Go Recommendation

**Conditional Go** -- The deployment may proceed to non-production environments immediately. Production deployment should be contingent upon remediation of F-CS-001, F-CS-002, and F-CS-003, or formal risk acceptance by the CISO with documented compensating controls and residual risk acknowledgement.

---

## 2. Scope of Review

### Sections Examined

This review covered all 23 sections, 4 appendices, and the document control history (26 revision entries) of the AudioCodes SBC - Unified Deployment & Configuration Guide v2.6, totalling 3,559 lines. Particular focus was applied to:

- Section 5: AWS Infrastructure Requirements (Security Groups, VPC configuration)
- Section 6: Microsoft Entra ID Integration (App Registrations, client secrets)
- Section 10: Security Controls (Administrative access, RADIUS, hardening)
- Section 12: TLS Certificate Configuration (TLS versions, mTLS)
- Section 13: Media Configuration (NTP, media realms)
- Section 14: SIP Signalling Configuration (transport security)
- Section 15: Routing Configuration (IP Profiles, media security settings)
- Section 17: Break Glass Accounts (credential management, rotation)
- Section 20: IAM Permissions and Security (Stack Manager and SBC policies)
- Section 21: Cyber Security Considerations (attack surface, logging)
- Section 22A: OVOC Data Analytics and Reporting (CDR access, audit logging)

### Methodology

The review was conducted against the following framework:

1. Line-by-line analysis of all security-relevant configuration parameters, IAM policies, security group rules, and authentication architecture.
2. Cross-referencing of configuration values across sections for internal consistency (e.g., TLS versions stated in Section 8 vs. configured in Section 12; SNMP versions recommended in Section 10.3 vs. protocol specifications in Section 5).
3. Gap analysis against industry standards and frameworks (see Appendix: Standards and References).
4. Threat modelling of the documented architecture using STRIDE methodology against the attack surface analysis in Section 21.

### Reference Standards

- NIST SP 800-53 Rev. 5 (Security and Privacy Controls)
- CIS AWS Foundations Benchmark v3.0
- ACSC Essential Eight Maturity Model
- ACSC Information Security Manual (ISM) 2024
- PCI DSS v4.0 (where voice systems handle payment card data)
- RFC 3261 (SIP), RFC 3711 (SRTP), RFC 6455 (TLS for SIP)
- Microsoft Teams Direct Routing Security Requirements

---

## 3. Strengths Identified

The guide demonstrates several security design strengths that should be acknowledged.

### S-01: Least-Privilege SBC IAM Policy (Section 20, Lines 2523-2577)

The SBC IAM policy for HA failover uses resource-scoped ARNs and tag-based conditions (`aws:ResourceTag/Env`, `aws:ResourceTag/App`) for the `ec2:ReplaceRoute` and `ec2:AssociateAddress` actions. Only the `Describe` actions use `Resource: "*"`, which is an AWS API limitation. This is a well-designed least-privilege policy that follows the principle of minimal necessary permissions.

### S-02: Dual External Publishing Pattern (Section 5, Lines 455-521)

The architecture correctly differentiates between the SBC external publishing model (dedicated EIP with Security Group L4 filtering) and the OVOC ingress model (cloud firewall plus reverse proxy). The rationale for not placing a Layer 7 firewall in front of the SBC's WAN interface is technically sound -- SIP/TLS and SRTP require direct IP connectivity for proper NAT traversal and real-time media delivery. The document articulates this clearly rather than leaving it as an unexplained exception.

### S-03: No 0.0.0.0/0 Egress Rules (Section 5, Lines 444-451)

All security group egress rules are scoped to specific destinations. AWS API access uses VPC Endpoints (PrivateLink), Microsoft Graph API access uses published M365 Endpoint ID 56 CIDRs, and Teams Direct Routing uses documented Microsoft IP ranges. The Security Group Design Notes explicitly state "No 0.0.0.0/0 outbound rules" as a design principle.

### S-04: Temporal IAM Elevation for Stack Manager (Section 20, Lines 2505-2521)

The guide recommends detaching the Stack Manager's broad IAM policy during normal operations and re-attaching it only during deployment or Day 2 operations. Three implementation options are documented (IAM policy toggle, AWS SCP deny, automated runbook), and the pattern is cross-referenced with CloudTrail audit logging.

### S-05: Comprehensive CDR Audit Analysis (Section 22A, Lines 3010-3085)

The four-layer CDR auditing approach (PostgreSQL native logging, pgAudit, network-level logging, data lake access auditing) and the candid documentation of the OVOC GUI audit limitation (Lines 3087-3152) demonstrate maturity. The guide does not conceal platform limitations; instead it documents compensating controls and provides a risk acceptance template.

### S-06: Classification Failure Response for DoS Mitigation (Section 14.1, Line 1516)

The External (WAN) SIP Interface is configured with `Classification Failure Response Type = 0` (silent drop), meaning unclassified SIP messages from the internet are silently discarded rather than generating a response. This prevents reconnaissance and amplification attacks. The internal interfaces use `500` (Server Internal Error) for graceful rejection, which is appropriate for trusted interfaces.

### S-07: VPC Endpoints for AWS API Access (Section 20, Lines 2745-2784)

The deployment uses Interface VPC Endpoints for EC2, CloudFormation, CloudWatch, and STS, plus a Gateway Endpoint for S3. This keeps all AWS API traffic within the AWS network, eliminating the need for NAT Gateway egress for API calls. The cost estimate ($73/month per region) demonstrates that this has been assessed for feasibility, not just documented as a theoretical option.

### S-08: Break Glass Account Framework (Section 17, Lines 2116-2202)

The break glass account design includes dedicated per-component accounts with a clear naming convention, 20-character minimum password complexity, dual-control retrieval procedures, and a quarterly review and semi-annual rotation schedule. The separation of non-production and production accounts with distinct secret repository paths is well-structured.

---

## 4. Detailed Findings

### F-CS-001: MFA Gap on SBC Management Interfaces

| Attribute | Detail |
|-----------|--------|
| **Severity** | Critical |
| **Category** | Identity and Access Management |
| **Guide Reference** | Section 10.4, Line 1001; Section 21, Lines 2622-2623 |

**Description:**
RADIUS-based authentication for SBC management access (Web GUI, CLI/SSH) does not natively enforce multi-factor authentication. Section 10.4 explicitly states: *"RADIUS-based authentication does not natively enforce multi-factor authentication on the SBC management interface."* The guide acknowledges that Cisco ISE can proxy to MFA-capable identity sources (e.g., Microsoft Entra ID via ROPC, or Duo integration) but this is not configured or documented as a requirement. Section 21 (Line 2623) confirms the MFA column for SBC authentication reads: *"Not natively supported (RADIUS limitation); ISE can proxy to MFA-capable identity sources."*

The SBC management interface provides Security Administrator access with full control over voice routing, TLS certificates, call recording configuration, and SBC security policies. Compromise of a single-factor RADIUS credential grants an attacker the ability to intercept, redirect, or record voice calls, modify firewall rules, and disable security controls.

**Risk/Impact:**
An attacker who obtains valid Active Directory credentials (through phishing, credential stuffing, or directory compromise) can authenticate to any SBC management interface without a second factor. The SBC's RADIUS integration authenticates against on-premises Active Directory via Cisco ISE (Section 10.4, Line 1011). If AD credentials are compromised, all SBCs across both regions become accessible. The ACSC Essential Eight Maturity Level 2 mandates MFA for all administrative access to critical systems.

**Evidence:**
- Section 10.4, Line 1001: Explicit acknowledgement of RADIUS MFA limitation
- Section 21, Line 2623: MFA column confirms "Not natively supported"
- Section 10.4, Lines 1048-1097: RADIUS configuration shows standard PAP/CHAP authentication with no MFA enforcement mechanism

**Recommendation:**
Configure Cisco ISE to proxy SBC RADIUS authentication through to Microsoft Entra ID with Conditional Access MFA enforcement, or integrate Cisco Duo with ISE for RADIUS-layer MFA. Document the MFA authentication flow for SBC management and validate that the MFA prompt is triggered for all SBC login events (SSH and HTTPS). As an interim measure, restrict SBC management access to dedicated jump hosts that themselves require MFA for access.

**Priority:** Immediate -- before production deployment.

---

### F-CS-002: Stack Manager IAM Over-Privilege

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Category** | Cloud Security / IAM |
| **Guide Reference** | Section 20, Lines 2482-2503; Section 21, Lines 2676-2695 |

**Description:**
The Stack Manager IAM policy grants `ec2:*` and `cloudformation:*` with `Resource: "*"`. This provides full EC2 control including the ability to launch, terminate, or modify any EC2 instance in the account; create, modify, or delete any security group; manipulate any route table; and create or delete any CloudFormation stack. The note at Line 2503 states: *"AudioCodes confirms these broad permissions (ec2:*, cloudformation:*) are required for Stack Manager to function -- it creates and manages SBC HA stacks via CloudFormation. These permissions cannot be reduced without breaking Stack Manager functionality."*

While the temporal elevation pattern (Section 20, Lines 2505-2521) reduces standing privilege, the policy itself is defined with `Resource: "*"` and provides unrestricted EC2 and CloudFormation scope whenever attached. If the Stack Manager EC2 instance is compromised while the policy is attached, the attacker gains full EC2 control across the account in all regions.

**Risk/Impact:**
- An attacker with access to the Stack Manager instance during an elevation window can create new EC2 instances (e.g., cryptocurrency mining), modify security groups to open inbound access, delete production resources, or exfiltrate data via newly created resources.
- The `iam:PassRole` permission (Line 2489) allows the Stack Manager to assign any existing IAM role to new EC2 instances, potentially escalating privileges further.
- The `iam:CreateServiceLinkedRole` permission allows creation of service-linked roles for AWS services.
- Cross-region scope (`Resource: "*"` with no region condition) means compromise affects all AWS regions, not just the Australian deployment region.

**Evidence:**
- Section 20, Lines 2488-2497: IAM policy JSON showing `"ec2:*"`, `"cloudformation:*"`, `"Resource": "*"`
- Section 21, Lines 2699-2706: Permission justification table rating `ec2:*` and `cloudformation:*` as "Medium" risk
- Section 20, Line 2480: Explicit note that `Resource: "*"` enables cross-region API calls

**Recommendation:**
1. Deploy the Stack Manager in a **dedicated AWS account** (member account within the AWS Organisation) rather than the same account as production workloads. This provides an account-level blast radius boundary.
2. If a dedicated account is not feasible, implement an **AWS Service Control Policy (SCP)** that restricts `ec2:*` actions to resources tagged with `Project: AudioCodes-Voice` at all times, not just as an optional enhancement (Section 20, Line 2726-2735).
3. Add an `aws:RequestedRegion` condition key to restrict actions to `ap-southeast-2` and `us-east-1` only, preventing lateral movement to other regions.
4. Enable **AWS CloudTrail** with real-time alerting (via EventBridge) on all `ec2:RunInstances`, `ec2:AuthorizeSecurityGroupIngress`, and `iam:PassRole` events from the Stack Manager role.
5. Reduce the temporal elevation window to the minimum necessary and require a change ticket number in the policy session tag.

**Priority:** Pre-go-live.

---

### F-CS-003: Internal SIP Signalling Unencrypted (UDP 5060)

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Category** | Data in Transit / Network Security |
| **Guide Reference** | Section 14.1, Lines 1506-1516; Section 15.1, Lines 1593-1607 |

**Description:**
The Proxy SBC Internal (LAN) SIP Interface (Index 0) and PSTN SIP Interface (Index 1) are configured with `TLS Port = 0` (disabled) and use only UDP for SIP signalling (Section 14.1, Lines 1508-1509). All internal IP Profiles set `Media Security Behavior = "Not Secured"` (Section 15.1, Lines 1595-1599), meaning RTP media between the Proxy SBC and downstream SBCs, third-party PBX systems, and registered endpoints is unencrypted.

Section 12, Line 1310 confirms: *"Downstream SBCs communicate with the Proxy SBC over the internal network using unencrypted SIP (UDP) and do not require TLS certificates for Teams connectivity."*

The design note at Section 15.1, Line 1603 rationalises this: *"Media security is set to 'Not Secured' as internal traffic does not require SRTP encryption."*

However, the cloud east-west firewall section (Section 5, Lines 501-521) confirms that internal SIP signalling and RTP media traverse the cloud firewall for inspection, meaning this traffic is visible to any component in the inspection path.

**Risk/Impact:**
- SIP signalling in cleartext exposes call metadata (caller and callee identifiers, phone numbers, SIP URIs, call duration) to any entity that can observe traffic on the internal network.
- Unencrypted RTP media exposes actual voice conversations to eavesdropping.
- The firewall rules in Section 16.1 (Lines 1855-1858) show SIP signalling on `TCP/UDP 5060, 5061` to downstream devices, yet the SBC configuration disables TLS (port 0), so only UDP 5060 is active.
- The note at Section 16.1, Line 1860 recommends TLS between AudioCodes devices: *"TCP 5061 (TLS) is recommended for SIP trunks between AudioCodes devices (Proxy SBC, Downstream SBCs, Media Packs) to encrypt signalling data in transit."* This recommendation contradicts the actual configuration in Section 14.1 where TLS is disabled.
- If the cloud east-west firewall performs SSL/TLS inspection, unencrypted SIP traffic provides no protection against rogue inspection or logging.

**Evidence:**
- Section 14.1, Line 1508: Internal (LAN) SIP Interface -- `TLS Port = 0`
- Section 14.1, Line 1509: PSTN SIP Interface -- `TLS Port = 0`
- Section 15.1, Lines 1595-1599: IP Profiles with `Media Security Behavior = Not Secured` for Proxy_Downstream_Internal_Profile, PSTN_Profile, 3rd Party PBX Profile, and Registered Endpoints Profile
- Section 16.1, Line 1860: Firewall rules note recommending TLS between AudioCodes devices
- Section 12, Line 1310: Explicit statement that downstream SBCs use unencrypted SIP

**Recommendation:**
Enable TLS (port 5061) on all internal SIP interfaces and configure SIP signalling between the Proxy SBC and downstream AudioCodes devices to use TLS transport. For media encryption, enable SRTP (`Media Security = Secured`) on the Proxy_Downstream_Internal_Profile at minimum. Where third-party PBX systems do not support SRTP, document the exception in the risk register with a risk acceptance from the system owner. Align the SBC configuration with the firewall rule recommendation at Line 1860.

**Priority:** Pre-go-live.

---

### F-CS-004: OVOC CDR Audit Gap -- GUI and Analytics API

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Category** | Audit and Compliance |
| **Guide Reference** | Section 22A, Lines 3010-3014, 3060-3062, 3087-3093 |

**Description:**
Section 22A documents two distinct audit gaps in OVOC's CDR access logging:

1. **Analytics API (Lines 3010-3014):** OVOC does not natively log individual SQL queries made through the Analytics API. The guide states: *"The OVOC application-level audit trail (Actions Journal) covers GUI-based operator actions but does not extend to raw SQL sessions initiated via the PostgreSQL direct-access interface (port 5432)."*

2. **GUI Viewing (Lines 3087-3093):** The guide explicitly states: *"There is no native capability within OVOC to log or audit which operator viewed specific CDR records, call quality data, or QoE reports through the web GUI."* The Actions Journal tracks configuration changes but does not track data reads or page views.

Additionally, the Analytics API uses a single shared `analytics` PostgreSQL user (Line 3062): *"OVOC provides a single shared analytics user for all external database access. PostgreSQL logs will show user=analytics for every connection, making it impossible to distinguish between different human analysts or ETL service accounts at the database level alone."*

**Risk/Impact:**
Organisations subject to privacy regulations (Privacy Act 1988 (Cth), GDPR) or telecommunications interception laws may be required to demonstrate who accessed call records and when. The inability to attribute CDR access to individual operators creates a compliance gap for forensic investigation of potential data misuse, privacy breaches, or internal misconduct involving voice communications metadata.

**Evidence:**
- Section 22A, Line 3014: OVOC does not record query content for Analytics API sessions
- Section 22A, Lines 3062: Single shared `analytics` user prevents user-level attribution
- Section 22A, Lines 3087-3093: No native CDR view audit capability through GUI
- Section 22A, Lines 3101-3107: Table of audit questions that OVOC cannot answer

**Recommendation:**
1. Restrict Analytics API access (TCP 5432) to the ETL platform IP only via firewall rules -- no ad-hoc analyst access directly to OVOC.
2. Enable PostgreSQL `log_connections` and `log_statement='all'` on the OVOC server (with AudioCodes support engagement for supportability confirmation).
3. Enable OVOC GDPR Phone Number Masking (Privacy Mode) to reduce the sensitivity of CDR data visible through the GUI.
4. Direct all analyst CDR access to the corporate data lake where individual user accounts and native audit logging are available.
5. Document the GUI audit limitation in the risk register with formal risk acceptance per the template at Section 22A, Line 3151.

**Priority:** Pre-go-live.

---

### F-CS-005: SNMPv2 vs. SNMPv3 Ambiguity

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Network Security / Protocol Security |
| **Guide Reference** | Section 10.3, Line 977; Section 5, Lines 386-394, 426-442 |

**Description:**
Section 10.3 (Line 977) recommends: *"Disable legacy/weak management protocols (Telnet, HTTP, SNMPv1) and use only HTTPS, SSH, and SNMPv3 with strong credentials and, where supported, encryption."* However, the security groups in Section 5 specify SNMP polling (UDP 161) and SNMP traps (UDP 162) without specifying which SNMP version is in use. The SBC Internal Security Group (Line 386) permits `UDP 161` from OVOC CIDR for SNMP polling, and the OVOC Security Group (Lines 433-434) permits `UDP 162` inbound from SBC CIDR for SNMP traps.

The OVOC Security Group also shows outbound SNMP trap forwarding to NMS/SIEM on `UDP 1164-1174` (Line 440) with no version specification. Section 5, Line 453 mentions *"SNMP (v2/v3)"* in the OVOC Northbound Interface documentation, suggesting both versions may be in use.

**Risk/Impact:**
SNMPv2c uses community strings transmitted in cleartext over UDP. An attacker with network visibility to the internal subnet can intercept SNMP community strings and use them to query device configuration, enumerate network topology, or potentially modify device settings (if read-write community strings are configured). SNMP community string interception has been a common attack vector in enterprise network compromises.

**Evidence:**
- Section 10.3, Line 977: Recommends SNMPv3
- Section 5, Lines 386, 394: SNMP UDP 161/162 in security groups with no version specification
- Section 5, Line 453: References "SNMP (v2/v3)" for OVOC Northbound Interface

**Recommendation:**
Mandate SNMPv3 with authentication (SHA) and encryption (AES-128 or AES-256) for all SNMP communication between SBCs and OVOC. Document the SNMPv3 user, authentication protocol, and encryption protocol in the configuration guide. If SNMPv2c is required for compatibility with legacy monitoring systems, document the exception and restrict SNMP community strings to read-only with network-level access controls.

**Priority:** Pre-go-live.

---

### F-CS-006: NTP Authentication Mode Set to None

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Infrastructure Security |
| **Guide Reference** | Section 13.1, Lines 1410-1421 |

**Description:**
The NTP configuration in Section 13.1 sets `NTP Auth Mode = None` (Line 1417). NTP synchronisation is used for multiple security-critical functions: TLS certificate validation, CDR timestamps, syslog message timestamps, and HA synchronisation (Line 1412). The guide notes: *"A time drift of more than a few seconds can cause TLS certificate validation failures with Microsoft Teams"* (Line 1421), demonstrating awareness of NTP's importance without addressing the authentication gap.

**Risk/Impact:**
Without NTP authentication, an attacker with network access to the SBC management subnet can perform NTP poisoning attacks to shift the SBC's clock. This can be exploited to:
- Cause TLS certificate validation failures with Microsoft Teams (DoS against voice services)
- Manipulate CDR timestamps to obscure the timing of call interception or manipulation
- Cause HA synchronisation issues between Active and Standby SBCs
- Undermine forensic evidence by skewing log timestamps

The ACSC ISM control ISM-1505 requires NTP authentication for systems handling classified or sensitive data.

**Evidence:**
- Section 13.1, Line 1417: `NTP Auth Mode = None`
- Section 13.1, Lines 1412-1413: NTP described as essential for CDRs, syslog, TLS validation, and HA synchronisation

**Recommendation:**
Enable NTP authentication using symmetric key (MD5 or SHA-1) or autokey authentication between the SBC and the enterprise NTP server. If using the AWS internal NTP service (169.254.169.123, referenced at Line 814), note that it does not support NTP authentication -- in this case, document the reliance on AWS infrastructure security as a compensating control and ensure the NTP traffic does not traverse untrusted network segments.

**Priority:** Pre-go-live.

---

### F-CS-007: No AWS Security Service Integration

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Cloud Security / Monitoring |
| **Guide Reference** | Section 21, Lines 2805-2812 |

**Description:**
Section 21 documents logging and monitoring with three log types: AWS API Calls (CloudTrail), Stack Manager System Logs, and CloudFormation Events. However, there is no mention of integration with AWS GuardDuty, AWS Security Hub, AWS Config, or Amazon Inspector anywhere in the 3,559-line document. These are foundational AWS security services recommended by the CIS AWS Foundations Benchmark and the AWS Well-Architected Framework Security Pillar.

The Approval Checklist in Section 21 (Lines 2835-2842) includes *"Included in vulnerability scanning scope"* (Line 2841) but does not specify which scanning tool or service.

**Risk/Impact:**
Without GuardDuty, the organisation has no automated threat detection for anomalous API calls, cryptocurrency mining, or compromised EC2 instances in the voice infrastructure account. Without Security Hub, there is no centralised view of compliance status against security benchmarks. Without AWS Config, there is no drift detection on security groups, IAM policies, or network configurations.

**Evidence:**
- Section 21, Lines 2805-2812: Logging and Monitoring table with only three entries (CloudTrail, system logs, CloudFormation)
- No mention of GuardDuty, Security Hub, AWS Config, or Amazon Inspector in the entire document
- Section 21, Line 2841: Generic "vulnerability scanning" reference without specifying a tool

**Recommendation:**
1. Enable **AWS GuardDuty** in both deployment regions (ap-southeast-2, us-east-1) with DNS, VPC flow log, and CloudTrail findings enabled.
2. Enable **AWS Security Hub** with the CIS AWS Foundations Benchmark and AWS Foundational Security Best Practices standards.
3. Enable **AWS Config** with rules for security group change detection, IAM policy change detection, and EBS encryption enforcement.
4. Configure Security Hub findings to forward to the organisation's SIEM for centralised alerting.
5. Specify Amazon Inspector or equivalent for the vulnerability scanning requirement at Line 2841.

**Priority:** Pre-go-live.

---

### F-CS-008: Client Secret Expiry Management -- No Automated Rotation

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Identity and Access Management / Secrets Management |
| **Guide Reference** | Section 6, Lines 569-571 |

**Description:**
Section 6 documents the creation of client secrets for Microsoft Entra ID app registrations. The guidance for secret expiry is: *"Expiry: Select appropriate expiry (recommend 24 months with calendar reminder)"* (Line 570). The sole rotation mechanism is a calendar reminder. No automated rotation, expiry monitoring, or alerting mechanism is documented.

The guide covers three app registrations (Section 6): OVOC Teams Integration, ARM WebUI, and SBC Direct Routing. Each requires a client secret that, if expired, will break integration with Microsoft 365 services (QoE data collection, ARM authentication, SBA functionality).

**Risk/Impact:**
- Calendar reminders are unreliable -- personnel changes, mailbox transitions, and calendar system migrations can result in missed reminders.
- A 24-month expiry means the impact of a missed renewal is total service failure (OVOC stops receiving Teams QoE data, ARM authentication breaks).
- There is no documented procedure for emergency secret rotation if a secret is suspected to be compromised.
- The Appendix B Credentials Reference Template (Lines 3285-3289) tracks `Secret Expiry` but provides no integration with alerting or monitoring systems.

**Evidence:**
- Section 6, Line 570: "recommend 24 months with calendar reminder"
- Appendix B, Lines 3285-3289: Manual credentials tracking template
- Appendix A, Line 3241: Checklist item reads "Client secret expiry dates calendared" with no automation reference

**Recommendation:**
1. Implement automated secret expiry monitoring using a script or service that queries the Microsoft Graph API (`/applications/{id}/passwordCredentials`) and alerts when secrets are within 90 days of expiry.
2. Reduce secret expiry from 24 months to 12 months to limit the window of exposure if a secret is compromised.
3. Document an emergency secret rotation procedure including the steps to update the secret in OVOC/ARM configuration without service disruption.
4. Consider migrating from client secrets to certificate-based authentication for app registrations where supported (OVOC, ARM), which provides stronger authentication and avoids the cleartext secret management problem.

**Priority:** Pre-go-live.

---

### F-CS-009: RADIUS Shared Secret Transport Security

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Network Security / Protocol Security |
| **Guide Reference** | Section 10.4, Lines 1099-1141 |

**Description:**
The RADIUS Network Path Security table at Section 10.4 (Lines 1134-1141) states: *"RADIUS over UDP with shared secret (RADIUS does not use TLS natively; shared secret provides packet-level authentication via MD5 hash)."* The RADIUS protocol transmits the user's password encrypted with the shared secret using MD5, which is a deprecated hash algorithm. The Message-Authenticator attribute (Attribute 80) is enabled (Lines 1099-1106), which mitigates some man-in-the-middle attacks but does not provide encryption of the RADIUS payload.

RADIUS traffic between SBCs and Cisco ISE traverses the internal network (Line 1138: *"Management function shares the internal subnet (OAMP + LAN combined interface)"*), including potentially traversing the cloud east-west firewall (Section 5, Lines 501-521).

**Risk/Impact:**
- MD5 is cryptographically broken for collision resistance and is deprecated by NIST SP 800-131A.
- An attacker with access to the internal network (or the cloud east-west firewall inspection path) can capture RADIUS packets and attempt offline brute-force attacks against the shared secret.
- If the shared secret is compromised, the attacker can decrypt user passwords from captured RADIUS Access-Request packets.
- The combined OAMP + LAN subnet design (Section 11, Line 1150) means RADIUS traffic shares the same network segment as SIP signalling and management traffic, increasing the attack surface.

**Evidence:**
- Section 10.4, Line 1136: RADIUS uses MD5 hash protection only
- Section 10.4, Line 1138: Management shares the internal subnet
- Section 10.4, Lines 1056-1058: RADIUS uses UDP 1812/1813

**Recommendation:**
Evaluate the feasibility of deploying RADIUS over TLS (RadSec, RFC 6614) between the SBCs and Cisco ISE, which encapsulates RADIUS within a TLS tunnel. If the AudioCodes SBC does not support RadSec, implement the following compensating controls: (a) use unique per-SBC shared secrets of at least 32 characters, (b) store shared secrets in the organisation's password vault, (c) rotate shared secrets annually, and (d) ensure RADIUS traffic is segmented to the management VLAN with strict access controls.

**Priority:** Post-deployment (next maintenance window).

---

### F-CS-010: No Vulnerability Management or Patching Cadence

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Operational Security |
| **Guide Reference** | Section 10.3, Line 978 |

**Description:**
Section 10.3 states: *"Keep SBC software at a vendor-supported release; apply security patches per change process and review AudioCodes security/hardening guidelines at each upgrade"* (Line 978). This is the entirety of the patching guidance. No formal vulnerability management policy, patching cadence, or SLA for critical security patches is defined.

The deployment includes 9 production VMs across two regions (Section 3, Line 160), each running AudioCodes proprietary software, Linux operating systems, and PostgreSQL databases (OVOC). The guide does not address vulnerability scanning, CVE tracking, or security advisory monitoring for any of these components.

**Risk/Impact:**
Without a defined patching cadence, known vulnerabilities in AudioCodes software, the underlying Linux OS, PostgreSQL (OVOC), or Java/Tomcat (OVOC web application) may remain unpatched indefinitely. Voice infrastructure is an attractive target for advanced persistent threats due to the intelligence value of intercepted voice communications. The ACSC Essential Eight mandates patching of internet-facing systems within 48 hours of a critical CVE and all systems within two weeks.

**Evidence:**
- Section 10.3, Line 978: Generic "apply security patches per change process" guidance
- Section 21, Line 2841: "Included in vulnerability scanning scope" without specifying tool or cadence
- No CVE tracking, security advisory monitoring, or patching SLA documented

**Recommendation:**
1. Define a patching cadence: Critical CVEs within 48 hours, High within 2 weeks, Medium within 30 days, Low within 90 days.
2. Subscribe to AudioCodes security advisories and monitor for CVEs affecting Mediant VE, ARM, OVOC, and Stack Manager.
3. Include all 9 production VMs in the organisation's vulnerability scanning programme (e.g., Amazon Inspector, Qualys, Tenable).
4. Document the patching procedure for each component type, including HA failover considerations during SBC patching.

**Priority:** Pre-go-live.

---

### F-CS-011: Break Glass Password Rotation -- No Automation

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Identity and Access Management |
| **Guide Reference** | Section 17, Lines 2194-2201 |

**Description:**
Section 17 defines a manual password rotation schedule for break glass accounts: quarterly status review, semi-annual rotation, and rotation after each use (Lines 2196-2201). The access procedure requires dual control and incident ticket creation (Lines 2188-2192). However, there is no automated mechanism for enforcing the rotation schedule, alerting on overdue rotations, or verifying that post-use rotation has occurred.

With 14 break glass accounts across three environments (Lines 2137-2170), manual rotation tracking is operationally burdensome and error-prone.

**Risk/Impact:**
- Break glass credentials that are not rotated after use remain valid and can be reused if an attacker obtains them from the password vault or from the operator who last used them.
- Without automated rotation enforcement, the semi-annual rotation schedule may be missed, leaving stale credentials active for extended periods.
- Break glass accounts are high-value targets because they bypass centralised authentication (RADIUS and Entra ID).

**Evidence:**
- Section 17, Lines 2196-2201: Manual rotation schedule with no automation
- Section 17, Lines 2137-2170: 14 break glass accounts across 3 environments
- Section 17, Line 2192: "Rotate password after each use (recommended)" -- not mandatory

**Recommendation:**
1. Implement automated secret rotation for break glass accounts using the organisation's secrets manager (e.g., AWS Secrets Manager with rotation Lambda, CyberArk password rotation).
2. Change the post-use rotation from "recommended" to **mandatory**, with automated verification that the password has been changed within 24 hours of use.
3. Configure alerting on overdue rotations (>180 days since last rotation).
4. Implement break glass account login monitoring: configure SIEM alerts for any login event using a break glass username, triggering immediate incident response notification.

**Priority:** Pre-go-live.

---

### F-CS-012: Overly Broad Cross-Region Security Group Rules

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Network Security |
| **Guide Reference** | Section 5, Lines 390-397, 407-412, 421-424, 441 |

**Description:**
Multiple security groups permit `All protocols / All ports` from the other region's VPC CIDR for cross-region connectivity:

- SBC Internal Security Group (Line 390): `Inbound | All | All | Other Region VPC CIDR`
- SBC Internal Security Group (Line 397): `Outbound | All | All | Other Region VPC CIDR`
- SBC External Security Group (Line 407): `Inbound | All | All | Other Region VPC CIDR`
- SBC External Security Group (Line 412): `Outbound | All | All | Other Region VPC CIDR`
- ARM Security Group (Line 421): `Inbound | All | All | Other Region VPC CIDR`
- ARM Security Group (Line 424): `Outbound | All | All | Other Region VPC CIDR`
- OVOC Security Group (Line 441): `Inbound | All | All | Other Region VPC CIDR`

These rules effectively create an unrestricted tunnel between the AU and US VPCs for all protocols and ports.

**Risk/Impact:**
If either region's VPC is compromised, the `All/All` rules provide unrestricted lateral movement to the other region. The cross-region traffic is described as necessary for *"Cross-region SBC-to-SBC and management connectivity"* (Line 390), but the actual protocols required are limited: SIP signalling (TCP/UDP 5060-5061), RTP media (UDP 6000-41999), HTTPS management (TCP 443), and SNMP (UDP 161/162). The `All/All` rules are significantly broader than necessary.

**Evidence:**
- Section 5, Lines 390, 397, 407, 412, 421, 424, 441: Seven `All | All | Other Region VPC CIDR` rules across four security groups
- Section 16, Lines 1862-1869: Inter-proxy SBC firewall rules specify only TCP 5060/5061 (SIP) and UDP 10000-19999 (media)

**Recommendation:**
Replace all `All protocols / All ports` cross-region rules with specific protocol and port rules that match the documented firewall rules in Section 16. For cross-region SBC-to-SBC connectivity, permit only: TCP/UDP 5060-5061 (SIP signalling), UDP 10000-19999 (RTP media), TCP 443 (HTTPS management), UDP 161-162 (SNMP). Remove the `All/All` rules from the External SBC Security Group entirely -- cross-region SBC-to-SBC signalling uses the Internal interface, not the External interface.

**Priority:** Pre-go-live.

---

### F-CS-013: No Data-at-Rest Encryption Specified

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Data Protection |
| **Guide Reference** | Sections 4, 9.4, 22A (entire document) |

**Description:**
The guide does not address data-at-rest encryption for any component in the deployment. Specifically:

- **EBS Volumes:** Section 4 and 9.4 specify EBS GP3 SSD volumes for all components (Lines 326-331) but do not mention EBS encryption. The OVOC instance uses up to 2 TB of GP3 storage (Line 328) containing CDR data, QoE metrics, and alarm data.
- **OVOC PostgreSQL Database:** The OVOC embedded PostgreSQL database (`dbems`, Section 22A, Line 2891) stores call detail records, quality metrics, and user information. No database-level encryption (TDE or pg_tls_encryption) is mentioned.
- **Configuration Backups:** Section 21, Line 2664 mentions *"Configuration backup and recovery operations"* as a Stack Manager function but does not specify encryption for backup data.

**Risk/Impact:**
If an EBS volume snapshot is shared, copied to another account, or if a terminated instance's volume is not properly destroyed, CDR data (which contains call metadata including phone numbers, timestamps, and duration) could be exposed. The CIS AWS Foundations Benchmark requires EBS encryption to be enabled by default at the account level.

**Evidence:**
- Section 4, Lines 326-331: EBS storage specifications with no encryption mention
- Section 22A, Lines 2891-2894: OVOC PostgreSQL on unencrypted storage
- No occurrence of "encryption at rest", "EBS encryption", or "KMS" in the entire document

**Recommendation:**
1. Enable EBS encryption by default at the AWS account level using a customer-managed KMS key.
2. Verify that all existing EBS volumes are encrypted, or create encrypted copies and replace unencrypted volumes.
3. For OVOC PostgreSQL, confirm with AudioCodes whether the embedded PostgreSQL supports Transparent Data Encryption or native encryption extensions.
4. Encrypt all configuration backups before storage in S3 or other backup destinations.

**Priority:** Pre-go-live.

---

### F-CS-014: RADIUS Local Cache Timeout of 900 Seconds

| Attribute | Detail |
|-----------|--------|
| **Severity** | Low |
| **Category** | Identity and Access Management |
| **Guide Reference** | Section 10.4, Lines 1087-1088 |

**Description:**
The SBC RADIUS configuration sets `RADIUS Local Cache Timeout = 900 seconds` (15 minutes) with `RADIUS Local Cache Mode = Reset Timer Upon Access` (Lines 1087-1088). This means that once a user authenticates successfully via RADIUS, their credentials are cached locally on the SBC for 15 minutes. Any subsequent access within that window is authenticated against the local cache without contacting the RADIUS server.

The `Reset Timer Upon Access` mode extends the cache timeout each time the cached credential is used, meaning an active session could remain cached indefinitely as long as the user accesses the SBC at least once every 15 minutes.

**Risk/Impact:**
- If a user's Active Directory account is disabled or their AD security group membership is revoked (removing SBC access), the user can continue to access the SBC for up to 15 minutes (or longer with the reset timer) using cached credentials.
- If an attacker compromises a RADIUS session, the cached credentials remain valid for the cache duration regardless of remediation actions taken on the RADIUS server or Active Directory.
- The reset timer effectively makes the cache timeout infinite for an active attacker.

**Evidence:**
- Section 10.4, Line 1087: `RADIUS Local Cache Timeout = 900 seconds`
- Section 10.4, Line 1088: `RADIUS Local Cache Mode = Reset Timer Upon Access`

**Recommendation:**
Reduce the RADIUS Local Cache Timeout to 300 seconds (5 minutes) and change the Cache Mode from `Reset Timer Upon Access` to `Do Not Reset Timer` to ensure that cached credentials expire at a fixed interval. This balances usability (avoiding re-authentication for every page load) with security (limiting the window during which revoked credentials remain valid). Document the cache timeout as a known delay in access revocation.

**Priority:** Post-deployment.

---

### F-CS-015: No Security Incident Response Procedure for Voice Infrastructure

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Operational Security |
| **Guide Reference** | Section 21 (entire section); Section 17 |

**Description:**
The guide does not define or reference a security incident response procedure specific to voice infrastructure. Section 21 covers cyber security considerations including attack surface analysis (Lines 2787-2794), data handling (Lines 2797-2803), and logging/monitoring (Lines 2805-2812), but does not address what happens when a security incident is detected.

The Break Glass Accounts section (Section 17) defines emergency access procedures but only for the scenario where the identity provider is unavailable -- not for security incident containment. No procedure exists for scenarios such as: suspected SBC compromise, unauthorised call routing changes, SRTP key compromise, or toll fraud detection.

**Risk/Impact:**
Without a documented incident response procedure for voice infrastructure, the operations team may not know how to isolate a compromised SBC, preserve forensic evidence (CDR data, syslog, configuration snapshots), or contain a toll fraud attack in progress. Voice infrastructure incidents have unique characteristics (real-time media, regulatory interception obligations, carrier notification requirements) that are not addressed by generic IT incident response procedures.

**Evidence:**
- Section 21: No incident response procedure documented
- No occurrence of "incident response", "security incident", or "toll fraud" in the document
- Section 17: Break glass procedures cover IdP failure only, not security incidents

**Recommendation:**
Develop a voice infrastructure security incident response procedure covering: (a) SBC isolation and containment steps, (b) forensic evidence preservation (CDR export, syslog snapshot, configuration backup), (c) carrier notification procedures for toll fraud, (d) Microsoft Teams Direct Routing deregistration steps, (e) RADIUS emergency access revocation, (f) communication escalation matrix, and (g) post-incident review and hardening.

**Priority:** Pre-go-live.

---

### F-CS-016: TLS 1.2 Only -- No TLS 1.3 for Teams Connectivity

| Attribute | Detail |
|-----------|--------|
| **Severity** | Low |
| **Category** | Cryptographic Standards |
| **Guide Reference** | Section 8, Line 729; Section 12.1, Lines 1318-1323 |

**Description:**
Section 8 (Microsoft Teams Direct Routing Requirements) states: *"TLS Version: TLS 1.2 minimum (TLS 1.3 recommended)"* (Line 729). However, the TLS Context configuration in Section 12.1 sets `TLS Version = TLSv1.2` (Line 1322) with no mention of TLS 1.3 enablement. The configuration step at Line 1335 reinforces: *"Set the TLS Version to TLSv1.2 (minimum version required by Microsoft Teams)."*

**Risk/Impact:**
TLS 1.2 is currently considered secure, so this is not an immediate vulnerability. However, TLS 1.3 provides significant security improvements including removal of legacy cipher suites (RC4, DES, 3DES, AES-CBC, MD5, SHA-1), simplified handshake (1-RTT), mandatory forward secrecy, and protection against downgrade attacks. Given that the guide itself recommends TLS 1.3 in Section 8, the implementation should align with the stated recommendation.

**Evidence:**
- Section 8, Line 729: "TLS 1.3 recommended"
- Section 12.1, Line 1322: `TLS Version = TLSv1.2` configured
- Section 12.1, Line 1335: "Set the TLS Version to TLSv1.2" -- no TLS 1.3 guidance

**Recommendation:**
Verify that the deployed AudioCodes firmware version (7.4.500+) supports TLS 1.3 for SIP signalling. If supported, update the TLS Context configuration to `TLSv1.3` (or `TLSv1.2+TLSv1.3` if the platform supports dual-version negotiation). If the firmware does not yet support TLS 1.3, document this as a future upgrade item and track AudioCodes firmware releases for TLS 1.3 support.

**Priority:** Post-deployment.

---

## 5. Risk Matrix

| Finding ID | Title | Severity | Likelihood | Impact | Overall Rating |
|------------|-------|----------|------------|--------|----------------|
| F-CS-001 | MFA Gap on SBC Management | Critical | High | Critical | Critical |
| F-CS-002 | Stack Manager IAM Over-Privilege | High | Medium | Critical | High |
| F-CS-003 | Internal SIP Signalling Unencrypted | High | Medium | High | High |
| F-CS-004 | OVOC CDR Audit Gap | High | High | Medium | High |
| F-CS-005 | SNMPv2 vs. SNMPv3 Ambiguity | Medium | Medium | Medium | Medium |
| F-CS-006 | NTP Authentication Mode = None | Medium | Low | High | Medium |
| F-CS-007 | No AWS Security Service Integration | Medium | Medium | Medium | Medium |
| F-CS-008 | Client Secret Expiry -- No Automation | Medium | Medium | High | Medium |
| F-CS-009 | RADIUS Shared Secret Transport | Medium | Low | Medium | Medium |
| F-CS-010 | No Vulnerability Management Cadence | Medium | High | Medium | Medium |
| F-CS-011 | Break Glass Rotation -- No Automation | Medium | Medium | Medium | Medium |
| F-CS-012 | Overly Broad Cross-Region SG Rules | Medium | Low | High | Medium |
| F-CS-013 | No Data-at-Rest Encryption | Medium | Low | High | Medium |
| F-CS-014 | RADIUS Local Cache Timeout | Low | Medium | Low | Low |
| F-CS-015 | No Voice IR Procedure | Medium | Medium | High | Medium |
| F-CS-016 | TLS 1.2 Only -- No TLS 1.3 | Low | Low | Low | Low |

---

## 6. Gap Analysis

The following table identifies areas where the guide deviates from established security best practices and frameworks.

| Security Domain | Best Practice / Standard | Guide Coverage | Gap |
|-----------------|--------------------------|----------------|-----|
| **MFA for Admin Access** | ACSC Essential Eight ML2; NIST AC-7; ISM-1173 | Acknowledged as limitation (S10.4) | No MFA enforcement for SBC management; ISE-to-MFA proxy not configured |
| **IAM Least Privilege** | CIS AWS 1.16; NIST AC-6 | Temporal elevation documented (S20) | ec2:*/cloudformation:* with Resource:* remains over-privileged when attached |
| **Encryption in Transit (Internal)** | NIST SC-8; ISM-0489 | TLS on external interface only (S12/S14) | Internal SIP/RTP unencrypted; TLS recommended but not configured |
| **Encryption at Rest** | CIS AWS 2.2.1; NIST SC-28; ISM-1080 | Not addressed | No EBS encryption, no database encryption, no backup encryption |
| **Vulnerability Management** | ACSC Essential Eight; NIST SI-2 | Generic "apply patches" guidance (S10.3) | No cadence, no CVE tracking, no scanning tool specified |
| **Security Monitoring** | CIS AWS 4.x; NIST SI-4 | CloudTrail only (S21) | No GuardDuty, Security Hub, Config, or Inspector |
| **NTP Authentication** | NIST AU-8; ISM-1505 | NTP configured without auth (S13.1) | NTP poisoning risk for time-dependent security functions |
| **SNMP Security** | NIST SC-8; ISM-1311 | SNMPv3 recommended (S10.3) | SNMP version not specified in security groups or configuration |
| **Secret Rotation** | NIST IA-5; CIS Azure 1.7 | Manual calendar reminder (S6) | No automated rotation, monitoring, or alerting for client secrets |
| **Audit Logging** | NIST AU-3; Privacy Act 1988 | CDR audit gap documented (S22A) | No native CDR access auditing in OVOC GUI or Analytics API |
| **Incident Response** | NIST IR-1; ISM-0576 | Not addressed | No voice-specific incident response procedure |
| **Network Segmentation** | NIST SC-7; CIS AWS 5.x | Security groups defined (S5) | Cross-region All/All rules undermine segmentation |
| **TLS Best Practice** | NIST SC-13; RFC 8446 | TLS 1.3 recommended but not configured (S8/S12) | TLS 1.2 only in implementation |
| **Protocol Security** | RFC 6614 (RadSec); NIST SC-8 | RADIUS over UDP acknowledged (S10.4) | MD5-based shared secret, no TLS for RADIUS |

---

## 7. Recommendations Summary

### Immediate (Before Production Deployment)

| ID | Recommendation | Finding |
|----|---------------|---------|
| R-01 | Configure Cisco ISE to enforce MFA for all SBC RADIUS authentication via Entra ID Conditional Access or Duo integration | F-CS-001 |
| R-02 | Restrict SBC management access to MFA-protected jump hosts as interim measure | F-CS-001 |
| R-03 | Deploy Stack Manager in a dedicated AWS member account with SCP-enforced boundaries | F-CS-002 |
| R-04 | Add `aws:RequestedRegion` condition to Stack Manager IAM policy limiting to ap-southeast-2 and us-east-1 | F-CS-002 |

### Pre-Go-Live

| ID | Recommendation | Finding |
|----|---------------|---------|
| R-05 | Enable TLS (port 5061) on all internal SIP interfaces and SRTP on Proxy-Downstream IP Profile | F-CS-003 |
| R-06 | Enable OVOC GDPR Phone Number Masking and restrict Analytics API to ETL platform IP only | F-CS-004 |
| R-07 | Mandate SNMPv3 with SHA authentication and AES encryption for all OVOC-SBC SNMP communication | F-CS-005 |
| R-08 | Enable NTP authentication or document reliance on AWS NTP as a compensating control | F-CS-006 |
| R-09 | Enable GuardDuty, Security Hub, and AWS Config in both deployment regions | F-CS-007 |
| R-10 | Implement automated client secret expiry monitoring with 90-day advance alerting | F-CS-008 |
| R-11 | Define patching cadence: Critical 48 hours, High 2 weeks, Medium 30 days | F-CS-010 |
| R-12 | Implement automated break glass password rotation via secrets manager | F-CS-011 |
| R-13 | Replace All/All cross-region security group rules with specific protocol/port rules | F-CS-012 |
| R-14 | Enable EBS encryption by default at the account level using customer-managed KMS key | F-CS-013 |
| R-15 | Develop voice infrastructure security incident response procedure | F-CS-015 |

### Post-Deployment (Next Maintenance Window)

| ID | Recommendation | Finding |
|----|---------------|---------|
| R-16 | Evaluate RadSec (RADIUS over TLS) for SBC-to-ISE communication | F-CS-009 |
| R-17 | Reduce RADIUS local cache timeout to 300 seconds, disable reset timer | F-CS-014 |
| R-18 | Upgrade TLS Context to TLS 1.3 when AudioCodes firmware supports it | F-CS-016 |

---

## 8. Action Items Register

| Item | Description | Owner | Priority | Target Date | Status |
|------|-------------|-------|----------|-------------|--------|
| AI-01 | Configure ISE MFA proxy for SBC RADIUS authentication | Security / Voice Engineering | Critical | Before Prod Go-Live | Open |
| AI-02 | Implement MFA-protected jump hosts for SBC management (interim) | Infrastructure | Critical | 2 weeks | Open |
| AI-03 | Evaluate and implement dedicated AWS account for Stack Manager | Cloud Platform | High | Before Prod Go-Live | Open |
| AI-04 | Add region condition keys to Stack Manager IAM policy | Cloud Platform | High | 2 weeks | Open |
| AI-05 | Configure real-time CloudTrail alerting for Stack Manager role actions | Cloud Security | High | 2 weeks | Open |
| AI-06 | Enable TLS on internal SIP interfaces across all SBCs | Voice Engineering | High | Before Prod Go-Live | Open |
| AI-07 | Enable SRTP on Proxy_Downstream_Internal IP Profile | Voice Engineering | High | Before Prod Go-Live | Open |
| AI-08 | Enable OVOC GDPR Phone Number Masking (Privacy Mode) | Voice Engineering | High | Before Prod Go-Live | Open |
| AI-09 | Restrict OVOC Analytics API (TCP 5432) to ETL platform IP via firewall | Network Security | High | Before Prod Go-Live | Open |
| AI-10 | Enable PostgreSQL log_connections on OVOC (with AudioCodes support) | Voice Engineering | Medium | Before Prod Go-Live | Open |
| AI-11 | Configure SNMPv3 on all SBCs and OVOC | Voice Engineering | Medium | Before Prod Go-Live | Open |
| AI-12 | Enable NTP authentication or document compensating control | Voice Engineering | Medium | Before Prod Go-Live | Open |
| AI-13 | Enable GuardDuty in ap-southeast-2 and us-east-1 | Cloud Security | Medium | Before Prod Go-Live | Open |
| AI-14 | Enable Security Hub with CIS benchmark | Cloud Security | Medium | Before Prod Go-Live | Open |
| AI-15 | Enable AWS Config with security group and IAM change rules | Cloud Security | Medium | Before Prod Go-Live | Open |
| AI-16 | Implement automated Entra ID client secret expiry monitoring | Identity / Cloud | Medium | Before Prod Go-Live | Open |
| AI-17 | Define and document patching cadence for all voice components | Voice Engineering / Security | Medium | Before Prod Go-Live | Open |
| AI-18 | Subscribe to AudioCodes security advisories | Voice Engineering | Medium | 1 week | Open |
| AI-19 | Implement automated break glass password rotation | Identity / Infrastructure | Medium | Before Prod Go-Live | Open |
| AI-20 | Configure break glass login SIEM alerting | Security Operations | Medium | Before Prod Go-Live | Open |
| AI-21 | Replace cross-region All/All security group rules with specific rules | Network Security | Medium | Before Prod Go-Live | Open |
| AI-22 | Enable EBS encryption at account level with CMK | Cloud Platform | Medium | Before Prod Go-Live | Open |
| AI-23 | Develop voice infrastructure incident response procedure | Security / Voice Engineering | Medium | Before Prod Go-Live | Open |
| AI-24 | Evaluate RadSec for RADIUS transport security | Security / Voice Engineering | Low | Post Go-Live (Q3 2026) | Open |
| AI-25 | Reduce RADIUS cache timeout and disable reset timer | Voice Engineering | Low | Post Go-Live (Q3 2026) | Open |
| AI-26 | Upgrade TLS Context to TLS 1.3 when firmware supports it | Voice Engineering | Low | Post Go-Live (Q3/Q4 2026) | Open |

---

## 9. Appendix: Sections Reviewed

| Section | Title | Lines | Security Relevance |
|---------|-------|-------|--------------------|
| 1 | Executive Summary | 45-76 | Architecture scope, key decisions |
| 2 | Critical Findings | 78-128 | HA failover mechanism, API access requirements |
| 3 | Architecture Overview | 131-160 | VM count, regional distribution |
| 4 | Component Specifications | 163-338 | Instance types, IAM requirements, SBC IAM policy |
| 5 | AWS Infrastructure Requirements | 342-521 | Security groups, VPC config, publishing patterns, east-west firewall |
| 6 | Microsoft Entra ID Integration | 525-671 | App registrations, client secrets, API permissions |
| 7 | Microsoft Graph API Permissions | 674-717 | Permission scopes, data access |
| 8 | Microsoft Teams Direct Routing Requirements | 720-797 | TLS requirements, certificate CAs, DNS |
| 9 | SBC Provisioning | 801-946 | HA configuration, deployment prerequisites |
| 10 | Security Controls | 949-1141 | Administrative access, RADIUS, hardening, authentication |
| 11 | SBC Network Configuration | 1144-1303 | Interface mapping, VLAN segmentation |
| 12 | TLS Certificate Configuration | 1306-1404 | TLS contexts, CSR, mTLS, trusted roots |
| 13 | Media Configuration | 1408-1493 | NTP, media realms, codecs |
| 14 | SIP Signalling Configuration | 1496-1779 | SIP interfaces, proxy sets, classification rules |
| 15 | Routing Configuration | 1583-1779 | IP profiles, media security settings, IP groups |
| 16 | Firewall Rules | 1783-2113 | All firewall rules by component and integration |
| 17 | Break Glass Accounts | 2116-2202 | Emergency access, credential management |
| 18 | Deployment Methodology | 2205-2220 | Deployment sequence and methods |
| 19 | High Availability Considerations | 2223-2473 | HA architecture, failover, voice recording |
| 20 | IAM Permissions and Security | 2476-2843 | IAM policies, VPC endpoints, security analysis |
| 21 | Cyber Security Considerations | 2608-2843 | Security architecture, attack surface, compliance |
| 22 | Licensing Considerations | 2846-2874 | Licensing model (not security-critical) |
| 22A | OVOC Data Analytics and Reporting | 2877-3156 | CDR access, audit logging, data classification |
| 23 | References and Documentation | 3159-3215 | Vendor and Microsoft documentation links |
| App A | Deployment Checklist | 3219-3278 | Pre-deployment and integration verification |
| App B | Credentials Reference Template | 3281-3310 | Credential storage guidance |
| App C | Quick Reference Tables | 3314-3368 | Port and instance summaries |
| App D | Network Flow Diagrams | 3372-3532 | Flow diagrams and interface mappings |

---

## 10. Appendix: Standards and References

| Standard / Framework | Version | Relevance |
|----------------------|---------|-----------|
| NIST SP 800-53 | Rev. 5 (2020) | Comprehensive security controls baseline |
| CIS Amazon Web Services Foundations Benchmark | v3.0 (2024) | AWS-specific security configuration requirements |
| ACSC Essential Eight Maturity Model | 2023 | Australian Government mandated cyber security baseline |
| ACSC Information Security Manual (ISM) | 2024 | Australian Government information security controls |
| PCI DSS | v4.0 (2024) | Payment card data protection (if applicable to voice) |
| RFC 3261 | 2002 | SIP: Session Initiation Protocol |
| RFC 3711 | 2004 | SRTP: The Secure Real-time Transport Protocol |
| RFC 6614 | 2012 | Transport Layer Security (TLS) Encryption for RADIUS |
| RFC 8446 | 2018 | TLS 1.3 specification |
| NIST SP 800-131A | Rev. 2 (2019) | Transitioning the Use of Cryptographic Algorithms (MD5 deprecation) |
| Microsoft Teams Direct Routing Documentation | Current | Microsoft-specific SBC security requirements |
| AudioCodes Security Guidelines | Per product release | Vendor hardening guidance |
| AWS Well-Architected Framework -- Security Pillar | 2024 | AWS security design principles |

---

*End of Report*

*Prepared by: Senior Cybersecurity Analyst / Security Architect*
*Review Date: 4 March 2026*
*Document Classification: Internal - Restricted*
