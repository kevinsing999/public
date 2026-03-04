# SBC Engineer Review — AudioCodes AWS Deployment Guide v2.6

## Internal Technical Review Report

**Reviewer Role:** Senior SBC / Voice Engineer
**Document Under Review:** AudioCodes SBC — Unified Deployment & Configuration Guide v2.6 (13 February 2026)
**Review Date:** 4 March 2026
**Report ID Prefix:** F-SB

---

## 1. Executive Summary

**Overall Rating:** Conditionally Adequate — Suitable as a high-level design reference, but requires significant supplementation before implementation.

The guide provides a competent architectural overview of the AudioCodes Mediant VE SBC deployment within AWS for Microsoft Teams Direct Routing. The network interface model (3-ENI consolidation), HA failover mechanism, and security group segmentation are well documented. However, the document defers too many critical SBC configuration parameters to "implementation time" without providing baseline values, ranges, or worked examples. A voice engineer picking up this guide would not be able to provision a working SBC without substantial additional AudioCodes product knowledge and vendor consultation.

**Top 3 Findings:**

1. **F-SB-001 (High):** No codec configuration specified — the Coder Group is referenced but never populated with actual codec entries, priority order, or ptime values.
2. **F-SB-005 (High):** Internal SIP signalling between Proxy and Downstream SBCs uses unencrypted UDP (port 5060) with no SRTP, contradicting Section 16 firewall recommendations for TLS on inter-device trunks.
3. **F-SB-008 (High):** No Call Admission Control (CAC) configuration is defined, creating risk of over-subscription and call quality degradation under load.

**Go/No-Go Recommendation:** Conditional Go — proceed to implementation with the caveat that a supplementary SBC Configuration Workbook must be developed to address the deferred parameters identified in this review.

---

## 2. Scope of Review

### Sections Examined

| Section | Title | Relevance |
|---------|-------|-----------|
| 4 | Component Specifications | Instance types, ENI model |
| 9 | SBC Provisioning | HA config, deployment prereqs |
| 11 | SBC Network Configuration | Physical/logical connectivity, Ethernet Groups, IP Interfaces |
| 12 | TLS Certificate Configuration | MTLS for Teams Direct Routing |
| 13 | Media Configuration | NTP, Media Realms, Coder Groups |
| 14 | SIP Signalling Configuration | SIP Interfaces, Proxy Sets |
| 15 | Routing Configuration | IP Profiles, IP Groups, Classification, Routing Rules |
| 16 | Firewall Rules | Port ranges, protocol specifications |
| 19 | High Availability Considerations | HA architecture, failover, SIP trunk connectivity |
| Appendix C | Quick Reference Tables | Port and instance summaries |
| Appendix D | Network Flow Diagrams | Interface mappings, call flows |

### Methodology

- Line-by-line review of all SBC-specific configuration tables and parameters
- Cross-referencing of port ranges across Media Realms, SIP Interfaces, Security Groups, and Firewall Rules for consistency
- Comparison against AudioCodes Mediant VE SBC Administrator's Manual v7.4/7.6 and Microsoft Teams Direct Routing planning guide
- Assessment of configuration completeness for a handoff to an implementation engineer

### Reference Standards

- AudioCodes Mediant VE SBC Installation Manual v7.4 / v7.6
- AudioCodes SBC Teams Direct Routing Configuration Note (Enterprise Model)
- Microsoft Teams Direct Routing Planning Guide
- ITU-T G.711, G.729, RFC 3261 (SIP), RFC 3711 (SRTP)

---

## 3. Strengths Identified

1. **3-ENI Consolidation Model (Sections 4, 11):** The decision to consolidate OAMP and LAN onto a single ENI (eth1) is well-justified and correctly documented. The design notes in Section 11.3 clearly explain the rationale for reducing from 4-ENI to 3-ENI, and the interface remapping (eth0=HA, eth1=OAMP+LAN, eth2=WAN) is consistently applied across all tables and diagrams.

2. **Media Realm Separation (Section 13.2):** The use of four distinct Media Realms on the Proxy SBC (Internal, M365, PSTN, LMO) with non-overlapping port ranges is a well-designed approach that simplifies troubleshooting, enables per-realm capacity monitoring, and aligns firewall rules to specific traffic types. The PSTN_Media_Realm being correctly sized at 500 session legs (250 concurrent calls) shows capacity planning awareness.

3. **Classification Rule DoS Mitigation (Section 14.1):** Setting the External (WAN) SIP Interface's Classification Failure Response to 0 (silent drop) is an effective DoS mitigation technique. The design note correctly explains that unclassified SIP messages from the external interface should be silently dropped to prevent reconnaissance and amplification attacks.

4. **IP Profile SRTP Enforcement (Section 15.1):** The Teams Direct Routing IP Profile correctly sets Media Security Behaviour to "Secured", enforcing SRTP on the Teams leg. The design notes accurately describe the SBC's role in terminating SRTP on the Teams side and bridging to RTP internally.

5. **Proxy Set Keep-Alive Design (Section 14.2):** All Proxy Sets correctly use SIP OPTIONS as keep-alive probes with Hot Swap enabled. This provides reliable endpoint health monitoring and automatic failover, which is critical for voice service continuity.

6. **Comprehensive Firewall Rules (Section 16):** The firewall rule tables are among the most thorough in the document, covering every integration point with specific source/destination, ports, protocols, and directionality. The inclusion of bidirectional rules for SIP providers is particularly important.

---

## 4. Detailed Findings

### F-SB-001: Codec Configuration Not Specified

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Category** | Media / Interoperability |
| **Guide Reference** | Section 13.3 Coder Groups |
| **Description** | The guide references `AudioCodersGroups_0` as the default Coder Group used across all SBC roles but does not specify any actual codec entries, priority order, packetisation time (ptime), silence suppression settings, or payload types. The section states codec considerations as general guidance ("Typical codec priority order: G.711 A-law, G.711 Mu-law, G.729, Opus") but defers the actual configuration to implementation. |
| **Risk / Impact** | Without a defined codec baseline, implementation engineers may configure inconsistent codec sets across SBC roles, leading to unnecessary transcoding, increased DSP consumption, and potential interoperability failures (SIP 488 responses). Codec mismatch between the Proxy SBC and Downstream SBCs is a common cause of one-way audio and call quality degradation. |
| **Evidence** | Section 13.3: "The specific codec list and priority order within the Coder Group are configured during implementation based on the capabilities of each connected system." All IP Profiles reference `AudioCodersGroups_0` but this group has no defined entries. |
| **Recommendation** | Define a baseline Coder Group configuration for each SBC role with specific codec entries including: codec name, priority, ptime (20ms or 30ms), silence suppression (on/off), and payload type. At minimum, provide a default configuration for the Proxy SBC that is known to work with Microsoft Teams (G.711 A-law, SILK, Opus) and the PSTN provider (G.711 A-law/Mu-law, G.729). |
| **Priority** | Pre-Go-Live |

---

### F-SB-002: No DTMF Handling Configuration

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Category** | Signalling / Interoperability |
| **Guide Reference** | Sections 13, 14, 15 (absent) |
| **Description** | The guide contains no mention of DTMF (Dual-Tone Multi-Frequency) relay configuration. DTMF handling is critical for IVR systems, conference bridge PINs, voicemail access, and call transfer via star codes. Microsoft Teams uses RFC 2833 (RTP Events) for DTMF transport, while PSTN carriers and legacy PBX systems may use in-band DTMF, SIP INFO, or RFC 2833 with different payload types. |
| **Risk / Impact** | Without explicit DTMF configuration, users may be unable to interact with IVR systems, enter conference PINs, access voicemail, or use DTMF-based call features. DTMF interworking failures are among the most common post-deployment issues in SBC deployments. |
| **Evidence** | Search of the entire document for "DTMF", "RFC 2833", "RTP event", "telephone-event", and "SIP INFO" returns zero results. |
| **Recommendation** | Add a DTMF Configuration subsection to Section 13 or 14 specifying: DTMF transport method per trunk (RFC 2833 for Teams, carrier-specific for PSTN), payload type (typically 101), and interworking rules for DTMF translation between different transport methods. |
| **Priority** | Pre-Go-Live |

---

### F-SB-003: No T.38 Fax or Modem Handling

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Media / Interoperability |
| **Guide Reference** | Section 9.2 (Downstream SBC — analogue interfaces mentioned), Sections 13–15 (absent) |
| **Description** | The Downstream SBC (Mediant 800C) is documented as having FXS/FXO analogue interfaces for connecting "telephones, fax machines" (Section 9.2). However, there is no T.38 fax relay configuration, no fax detection settings, and no guidance on fax-over-IP handling. The guide also omits modem passthrough configuration for legacy analogue devices. |
| **Risk / Impact** | Fax machines connected to Downstream SBC FXS ports will fail to transmit reliably over G.711 passthrough without explicit T.38 or fax detection configuration. In enterprise environments, fax remains a compliance requirement for legal, healthcare, and finance sectors. |
| **Evidence** | Section 9.2 references "fax machines" as a use case for FXS analogue interfaces, but the terms "T.38", "fax", "modem", and "V.150" appear nowhere else in the document. |
| **Recommendation** | Add a Fax and Modem Configuration subsection specifying: T.38 re-INVITE handling, fax detection mode (CNG/CED tone detection), T.38 max datagram size, ECM (Error Correction Mode) settings, and fallback to G.711 passthrough. If fax is out of scope for this deployment, document this explicitly as a scope exclusion. |
| **Priority** | Pre-Go-Live (if fax in scope) / Post-Deployment (if fax excluded) |

---

### F-SB-004: No QoS / DSCP Marking Configuration

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Media Quality / Network |
| **Guide Reference** | Sections 13, 14 (absent) |
| **Description** | The guide does not specify DSCP (Differentiated Services Code Point) marking for SIP signalling or RTP media packets. QoS marking is essential for voice traffic prioritisation across the enterprise WAN, AWS Direct Connect, and internal LAN segments. Without DSCP marking, voice packets receive best-effort treatment and are subject to jitter, latency, and packet loss from competing data traffic. |
| **Risk / Impact** | Voice quality degradation under network congestion. DSCP marking is particularly critical for traffic traversing the cloud east-west firewall (Section 5) and AWS Direct Connect to on-premises infrastructure. Microsoft Teams endpoints mark media packets with DSCP 46 (EF) by default; the SBC should reciprocate. |
| **Evidence** | The terms "DSCP", "QoS", "DiffServ", "EF", "AF", and "traffic class" do not appear in the document. |
| **Recommendation** | Define DSCP marking policy for: SIP signalling (CS3/DSCP 24 or AF31), RTP voice media (EF/DSCP 46), and management traffic (CS2/DSCP 16). Configure the SBC's IP Profile or global QoS settings to apply these markings on egress. Document any DSCP remarking requirements at the cloud east-west firewall and Direct Connect boundaries. |
| **Priority** | Pre-Go-Live |

---

### F-SB-005: Internal SIP Signalling Uses Unencrypted UDP

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Category** | Security / Signalling |
| **Guide Reference** | Section 12 (TLS note), Section 14.1 (SIP Interfaces), Section 15.1 (IP Profiles), Section 16 firewall note |
| **Description** | All internal SIP signalling between the Proxy SBC and Downstream SBCs uses unencrypted UDP (Section 14.1: Internal SIP Interface has TLS Port = 0). The IP Profiles for internal trunks set Media Security Behaviour to "Not Secured" (Section 15.1), meaning both signalling and media are unencrypted. This contradicts the firewall rule recommendation in Section 16.1 which states: "TCP 5061 (TLS) is recommended for SIP trunks between AudioCodes devices." |
| **Risk / Impact** | Unencrypted SIP signalling exposes call metadata (caller/callee numbers, SIP headers) to interception on the internal network and across the cloud east-west firewall. While the guide acknowledges internal traffic traverses a cloud firewall for inspection (Section 5), unencrypted traffic between Proxy and Downstream SBCs crossing WAN links (e.g., via Direct Connect to branch sites) is a significant security gap. |
| **Evidence** | Section 14.1 Internal SIP Interface: UDP Port = XXXX, TCP Port = 0, TLS Port = 0. Section 15.1 Proxy_Downstream_Internal_Profile: Media Security Behavior = "Not Secured". Section 16.1 Downstream Devices note: "TCP 5061 (TLS) is recommended for SIP trunks between AudioCodes devices." |
| **Recommendation** | Align the SIP Interface and IP Profile configuration with the Section 16 recommendation. Enable TLS 5061 on the Internal SIP Interface for Proxy-to-Downstream trunks. Consider enabling SRTP (Media Security = "Secured") for the Proxy_Downstream_Internal_Profile, particularly for traffic traversing WAN links. If unencrypted internal signalling is an accepted risk, document this decision explicitly with security team sign-off. |
| **Priority** | Pre-Go-Live |

---

### F-SB-006: Classification Rules Use /16 Wildcard Entries

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Security / Configuration |
| **Guide Reference** | Section 15.4 Classification Rules |
| **Description** | The Classification Rules for Microsoft Teams use wildcard notation (e.g., `52.112.*.*`, `52.113.*.*`) representing individual /16 entries. Six rules are defined to cover two CIDR ranges: 52.112.0.0/14 and 52.122.0.0/15. The guide itself notes: "Consider using broader subnet-based rules rather than individual /16 entries where Microsoft's published ranges permit, to reduce the number of rules and simplify maintenance." |
| **Risk / Impact** | Using six /16 wildcard rules instead of two CIDR-based rules increases the Classification Rule table size unnecessarily. While functionally equivalent, more rules mean longer classification processing time and a larger attack surface if a rule is misconfigured. AudioCodes SBCs support CIDR notation in Classification Rules — the wildcard approach is unnecessary. |
| **Evidence** | Section 15.4: Six rules (Index 0–5) using `52.112.*.*` through `52.115.*.*` and `52.122.*.*` through `52.123.*.*`. The design notes acknowledge this can be simplified: "Consider using broader subnet-based rules." |
| **Recommendation** | Replace the six /16 wildcard rules with two CIDR-based rules: `52.112.0.0/14` (covers 52.112–52.115) and `52.122.0.0/15` (covers 52.122–52.123). This reduces the rule count from 6 to 2, simplifies maintenance, and aligns with the guide's own recommendation. |
| **Priority** | Immediate |

---

### F-SB-007: Mediant 800C End-of-Life Status Not Addressed

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Product Lifecycle |
| **Guide Reference** | Section 9.2 Downstream SBC Provisioning |
| **Description** | The Downstream SBC is specified as the AudioCodes Mediant 800C. AudioCodes has previously announced end-of-sale for certain Mediant 800 variants, and the product is a legacy branch appliance. The guide does not document the EOL/EOS status of the Mediant 800C, the expected support timeline, or any planned migration path to a successor platform (e.g., Mediant 800B, Mediant SE). |
| **Risk / Impact** | Deploying a platform that is at or near end-of-life creates long-term support risk. Firmware updates, security patches, and vendor support may cease during the operational life of this deployment. Branch site SBCs are typically deployed for 5–7 years. |
| **Evidence** | Section 9.2: "The Downstream SBC is a physical AudioCodes Mediant 800C SBC appliance." No mention of product lifecycle status, end-of-sale date, last-order date, or end-of-support date. |
| **Recommendation** | Confirm the Mediant 800C's current lifecycle status with AudioCodes. Document the last-order date, end-of-support date, and the recommended successor platform. If the 800C is approaching EOL, include a migration strategy in the operational plan. |
| **Priority** | Pre-Go-Live |

---

### F-SB-008: No Call Admission Control (CAC) Configuration

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Category** | Capacity Management |
| **Guide Reference** | Sections 13, 14, 15 (absent) |
| **Description** | The guide defines Media Realm session leg counts (Section 13.2) but does not configure Call Admission Control (CAC) at the IP Group or SBC global level. CAC limits the number of concurrent calls per trunk to prevent over-subscription and ensure quality for existing calls. Without CAC, if inbound call volume exceeds the SBC's licensed capacity or the media realm's session leg allocation, calls may be admitted but experience degraded quality (codec fallback, no available media ports). |
| **Risk / Impact** | During peak call volumes or denial-of-service attacks, the SBC will continue to admit calls beyond its capacity, causing quality degradation for all active calls rather than cleanly rejecting excess calls with SIP 503 (Service Unavailable). |
| **Evidence** | Search for "admission control", "CAC", "max calls", "max sessions", "call limit" returns zero results. Media Realm session legs are defined (Section 13.2) but no IP Group-level or global call limits are configured. |
| **Recommendation** | Configure CAC at the IP Group level for each trunk: set maximum concurrent calls per IP Group aligned with licensing, Media Realm capacity, and contracted trunk capacity (e.g., PSTN trunk: 250 concurrent calls matching the 500-leg PSTN_Media_Realm). Configure SBC global call limits aligned with the instance type's licensed session capacity. Define CAC rejection behaviour (SIP 503 with Retry-After header). |
| **Priority** | Pre-Go-Live |

---

### F-SB-009: SBC Software Version Not Specified

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Version Management |
| **Guide Reference** | Section 4 (minimum version 7.4.500), Section 9.1 (prerequisite 7) |
| **Description** | The guide specifies a minimum SBC version of 7.4.500 for Cross-AZ HA support (Section 4) but does not specify the target deployment version. AudioCodes has released version 7.6 (referenced in the documentation links in Section 23), which includes security fixes, new features, and improved Microsoft Teams interoperability. The gap between minimum supported version (7.4.500) and latest available version (7.6.x) is significant. |
| **Risk / Impact** | Deploying on the minimum supported version rather than the latest recommended version may miss critical bug fixes, security patches, and Teams interoperability improvements. Different SBC instances may be deployed on different versions if the target is not specified. |
| **Evidence** | Section 4: "Minimum Version for Cross-AZ HA: Version 7.4.500". Section 23 references both v7.4 and v7.6 installation manuals. No target deployment version is stated. |
| **Recommendation** | Specify the exact target SBC firmware version (e.g., 7.6.xxx.xxx) and document it in the deployment prerequisites. Establish a version management policy requiring all SBC instances to run the same firmware version. Reference the AudioCodes release notes for the chosen version to confirm Teams Direct Routing certification. |
| **Priority** | Immediate |

---

### F-SB-010: No Emergency Calling (E911/000) Routing Configuration

| Attribute | Detail |
|-----------|--------|
| **Severity** | High |
| **Category** | Regulatory / Routing |
| **Guide Reference** | Section 15.5 (absent from routing scenarios) |
| **Description** | The routing scenario table in Section 15.5 does not include emergency calling (000 for Australia, 911/E911 for the US). Emergency call routing requires specific handling: location-based routing to the nearest PSAP, bypass of CAC restrictions, priority queuing, and potentially direct PSTN breakout (bypassing Teams). The guide's routing rules are deferred to implementation, but emergency calling is not even listed as a scenario. |
| **Risk / Impact** | Regulatory non-compliance. Both Australia (Telecommunications Act) and the US (Kari's Law, RAY BAUM's Act) have strict requirements for emergency calling in enterprise voice deployments. Failure to route emergency calls correctly has life-safety implications and regulatory penalties. |
| **Evidence** | Section 15.5 Supported Routing Scenarios: No mention of "emergency", "000", "911", "E911", "PSAP", or "location". |
| **Recommendation** | Add emergency calling as a mandatory routing scenario. Define: emergency number patterns (000 for AU, 911 for US), routing priority (highest), PSTN breakout path (direct to regional SIP provider, bypassing Teams), CAC exemption, location information insertion (if applicable), and callback number (ELIN or registered location). Document compliance requirements for both AU and US jurisdictions. |
| **Priority** | Immediate |

---

### F-SB-011: No SRTP Enforcement Between Proxy SBCs (Proxy-to-Proxy)

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Security / Media |
| **Guide Reference** | Section 15.1 IP Profiles, Section 14.2 Proxy Sets (Index 6) |
| **Description** | The Proxy-to-Proxy trunk (connecting AU Proxy SBC to US Proxy SBC) uses the `Proxy_Downstream_Internal_Profile` with Media Security Behaviour set to "Not Secured" (Section 15.1). This trunk carries inter-region SIP signalling and RTP media across the organisation's WAN backbone (AWS Direct Connect / VPN), potentially traversing multiple network segments and jurisdictions. |
| **Risk / Impact** | Cross-region voice traffic between Australia and the US traverses international network links without encryption. This traffic may be subject to lawful intercept requirements in both jurisdictions. Unencrypted media on cross-region links is a higher risk than unencrypted media on local LAN segments. |
| **Evidence** | Section 15.1: Proxy_Downstream_Internal_Profile used for Proxy-to-Proxy trunk, Media Security Behavior = "Not Secured". Section 14.2 Proxy Set Index 6 (Proxy-to-Proxy) uses Internal (LAN) SIP Interface with no TLS Context. |
| **Recommendation** | Create a dedicated `Proxy_to_Proxy_Profile` with Media Security Behaviour set to "Secured" (SRTP) and configure a TLS Context for inter-Proxy SIP signalling. This provides end-to-end encryption for cross-region voice traffic without impacting internal LAN-side performance. |
| **Priority** | Pre-Go-Live |

---

### F-SB-012: RTP Port Range Placeholders Throughout

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Configuration Completeness |
| **Guide Reference** | Section 13.2 Media Realms, Section 14.1 SIP Interfaces |
| **Description** | All RTP Start Port values in the Media Realm tables (Section 13.2) are shown as `XXXX` placeholders. Similarly, the UDP Port values in the SIP Interface tables (Section 14.1) are `XXXX`. While port ranges are defined in Appendix C (6000–19999 internal, 20000–21999 M365, 30000–39999 LMO, 40000–41999 PSTN), the actual Media Realm start ports are not populated in the configuration tables. |
| **Risk / Impact** | Implementation engineers must cross-reference Appendix C to determine start port values, introducing risk of misconfiguration. The SIP Interface UDP ports (for internal and PSTN interfaces) are not documented anywhere, even in Appendix C. |
| **Evidence** | Section 13.2: All RTP Start Port entries show "XXXX". Section 14.1: Internal SIP Interface UDP Port = "XXXX", PSTN SIP Interface UDP Port = "XXXX". |
| **Recommendation** | Populate all `XXXX` placeholders with the actual port values derived from the Appendix C ranges. For SIP Interface UDP ports, specify the listening ports (e.g., 5060 for internal, 5062 for PSTN — using different ports to distinguish traffic as noted in the design notes). |
| **Priority** | Immediate |

---

### F-SB-013: IP Interface Addresses Are All Placeholders

| Attribute | Detail |
|-----------|--------|
| **Severity** | Low |
| **Category** | Configuration Completeness |
| **Guide Reference** | Section 11.4 IP Interfaces, Section 9.3.1 Active/Standby Parameter Comparison |
| **Description** | All IP addresses in the IP Interface tables (Section 11.4) and the Active/Standby Parameter Comparison (Section 9.3.1) are shown as `X.X.X.X` placeholders. While this is expected for a generic deployment guide, the absence of even example addresses makes it difficult to validate the configuration or use it as a reference during implementation. |
| **Risk / Impact** | Low — implementation engineers are expected to substitute actual IP addresses. However, the absence of example values means potential configuration errors (e.g., using the same gateway for different subnets, or misconfiguring DNS) are not caught at design review time. |
| **Evidence** | Section 11.4: All IP Address, Gateway, and DNS fields show "X.X.X.X" across all SBC roles. Section 9.3.1: All HA, Management, Internal, and External Subnet IP entries show "X.X.X.X". |
| **Recommendation** | Add a worked example using RFC 5737 documentation addresses (e.g., 198.51.100.0/24 for external, 10.100.1.0/24 for internal) to illustrate the addressing model. This helps reviewers validate the design without exposing real IP addresses. |
| **Priority** | Post-Deployment |

---

### F-SB-014: No SBC Capacity Sizing Guidance

| Attribute | Detail |
|-----------|--------|
| **Severity** | Medium |
| **Category** | Capacity Planning |
| **Guide Reference** | Section 4, Section 13.2 |
| **Description** | The guide specifies instance types (m5n.large for Proxy SBC without transcoding, c5.2xlarge with transcoding) and Media Realm session legs (1000 internal, 1000 M365, 500 PSTN) but does not provide expected call volume data, concurrent session targets, or a capacity sizing calculation. The relationship between instance type, licensed session count, and Media Realm allocation is not documented. |
| **Risk / Impact** | Without capacity sizing, there is no way to verify whether the chosen instance type and Media Realm configuration can handle the expected call volume. Over-provisioning wastes cost; under-provisioning causes call failures. |
| **Evidence** | Section 4: Instance types listed with vCPU/memory but no session capacity numbers. Section 13.2: Media Realm session legs defined but no reference to expected call volumes. |
| **Recommendation** | Add a capacity planning section specifying: expected concurrent call volume per region, peak hour call volume, licensed session count for the selected SBC model, and how Media Realm session legs map to the licensing. Include the AudioCodes capacity planning calculator output if available. |
| **Priority** | Pre-Go-Live |

---

### F-SB-015: NTP Authentication Mode Set to None

| Attribute | Detail |
|-----------|--------|
| **Severity** | Low |
| **Category** | Security / Time Synchronisation |
| **Guide Reference** | Section 13.1 NTP Server Configuration |
| **Description** | NTP is configured with Authentication Mode set to "None" (Section 13.1). While the NTP server address is a placeholder (`X.X.X.X`), the absence of NTP authentication allows potential NTP poisoning attacks that could skew SBC time, affecting TLS certificate validation, CDR timestamps, and HA synchronisation. |
| **Risk / Impact** | Low in a controlled internal network. Higher risk if the NTP source is across a WAN link. NTP time manipulation could cause TLS handshake failures with Microsoft Teams (certificate not-yet-valid or expired errors) and CDR timestamp inaccuracies affecting billing reconciliation. |
| **Evidence** | Section 13.1: "NTP Auth Mode: None". |
| **Recommendation** | If the enterprise NTP infrastructure supports NTPv4 symmetric key authentication or Autokey, enable NTP authentication on the SBC. If using AWS internal NTP (169.254.169.123), authentication is not supported but the source is inherently trusted within the VPC. Document the NTP authentication decision rationale. |
| **Priority** | Post-Deployment |

---

## 5. Risk Matrix

| Finding ID | Title | Severity | Likelihood | Impact | Risk Rating |
|------------|-------|----------|------------|--------|-------------|
| F-SB-001 | No codec configuration specified | High | High | High | Critical |
| F-SB-002 | No DTMF handling configuration | High | High | High | Critical |
| F-SB-003 | No T.38 fax/modem handling | Medium | Medium | Medium | Medium |
| F-SB-004 | No QoS/DSCP marking | Medium | High | Medium | High |
| F-SB-005 | Internal SIP unencrypted (contradicts Section 16) | High | High | Medium | High |
| F-SB-006 | Classification Rules use /16 wildcards | Medium | Low | Low | Low |
| F-SB-007 | Mediant 800C EOL status unknown | Medium | Medium | High | High |
| F-SB-008 | No Call Admission Control | High | Medium | High | High |
| F-SB-009 | SBC software version not specified | Medium | High | Medium | High |
| F-SB-010 | No emergency calling routing | High | Medium | Critical | Critical |
| F-SB-011 | No SRTP on Proxy-to-Proxy trunk | Medium | Medium | Medium | Medium |
| F-SB-012 | RTP port range placeholders | Medium | High | Low | Medium |
| F-SB-013 | IP addresses all placeholders | Low | High | Low | Low |
| F-SB-014 | No capacity sizing guidance | Medium | Medium | Medium | Medium |
| F-SB-015 | NTP auth mode None | Low | Low | Medium | Low |

---

## 6. Gap Analysis

| Best Practice Area | Guide Coverage | Gap |
|-------------------|----------------|-----|
| Codec configuration with priorities | Referenced but not populated | Full codec table with ptime, priority, silence suppression |
| DTMF interworking | Not mentioned | RFC 2833 config, SIP INFO translation, payload type mapping |
| T.38 fax relay | Not mentioned | Fax detection, T.38 parameters, ECM settings |
| QoS / DSCP marking | Not mentioned | DSCP policy per traffic type, remarking at boundaries |
| Call Admission Control | Not mentioned | Per-trunk and global call limits, rejection behaviour |
| Emergency calling routing | Not mentioned | E000/E911 routing, PSAP connectivity, location services |
| SBC firmware version management | Minimum version only | Target version, upgrade policy, version consistency |
| Capacity sizing | Instance types only | Call volume projections, session licensing, sizing calc |
| Internal signalling encryption | Deferred / contradicted | TLS/SRTP policy for inter-device trunks |
| SBC hardening checklist | General guidance in Section 10 | Specific SBC CLI hardening commands, disabled services list |
| Session timer configuration | Not mentioned | SIP session timer (RFC 4028) for zombie call cleanup |
| SIP OPTIONS monitoring thresholds | Keep-alive enabled | OPTIONS interval, failure threshold, recovery threshold |
| Registration behaviour | Mentioned for PSTN | SIP REGISTER refresh interval, expiry, authentication |
| Number manipulation rules | Referenced but deferred | Calling/called number manipulation tables with examples |

---

## 7. Recommendations Summary

### Immediate (Before Design Finalisation)

1. Specify target SBC firmware version (F-SB-009)
2. Add emergency calling routing scenarios (F-SB-010)
3. Simplify Classification Rules to CIDR notation (F-SB-006)
4. Populate all port and address placeholders (F-SB-012, F-SB-013)

### Pre-Go-Live (Before Production Deployment)

5. Define baseline codec configuration for all trunk types (F-SB-001)
6. Configure DTMF interworking per trunk (F-SB-002)
7. Configure T.38 fax handling if in scope (F-SB-003)
8. Define and configure QoS/DSCP marking policy (F-SB-004)
9. Resolve internal SIP encryption contradiction (F-SB-005)
10. Confirm Mediant 800C lifecycle status (F-SB-007)
11. Configure Call Admission Control (F-SB-008)
12. Enable SRTP on Proxy-to-Proxy trunk (F-SB-011)
13. Complete capacity sizing exercise (F-SB-014)

### Post-Deployment (Operational Improvements)

14. Evaluate NTP authentication (F-SB-015)
15. Develop SBC hardening runbook with specific CLI commands
16. Implement session timer configuration for zombie call cleanup

---

## 8. Action Items Register

| # | Action | Owner | Priority | Target Date | Status |
|---|--------|-------|----------|-------------|--------|
| 1 | Specify target SBC firmware version | Voice Engineering | High | Design phase | Open |
| 2 | Define emergency calling routing rules | Voice Engineering + Compliance | Critical | Design phase | Open |
| 3 | Replace wildcard Classification Rules with CIDR | Voice Engineering | Medium | Design phase | Open |
| 4 | Populate all XXXX/X.X.X.X placeholders | Voice Engineering | Medium | Pre-implementation | Open |
| 5 | Create baseline Coder Group configuration | Voice Engineering | High | Pre-implementation | Open |
| 6 | Configure DTMF interworking rules | Voice Engineering | High | Implementation | Open |
| 7 | Define T.38 scope and configuration | Voice Engineering | Medium | Implementation | Open |
| 8 | Define QoS/DSCP marking policy | Voice + Network Engineering | High | Pre-implementation | Open |
| 9 | Resolve internal SIP encryption decision | Voice + Security | High | Design phase | Open |
| 10 | Confirm Mediant 800C EOL status with AudioCodes | Vendor Management | Medium | Immediate | Open |
| 11 | Configure CAC per trunk and globally | Voice Engineering | High | Implementation | Open |
| 12 | Enable SRTP on Proxy-to-Proxy trunk | Voice Engineering | Medium | Implementation | Open |
| 13 | Complete capacity sizing calculation | Voice + Cloud Engineering | Medium | Design phase | Open |
| 14 | Evaluate NTP authentication options | Voice + Security | Low | Post-deployment | Open |

---

## 9. Appendix: Sections Reviewed

| Section | Lines | Key Tables/Configs Reviewed |
|---------|-------|-----------------------------|
| 4. Component Specifications | 163–339 | Instance types, ENI model, IAM role |
| 9. SBC Provisioning | 801–946 | Deployment prerequisites, HA config parameters |
| 11. SBC Network Configuration | 1144–1303 | Physical/virtual ports, Ethernet Groups, Ethernet Devices, IP Interfaces |
| 12. TLS Certificate Configuration | 1306–1405 | TLS Context, CSR fields, MTLS root certs |
| 13. Media Configuration | 1408–1493 | NTP, Media Realms (Proxy/Downstream/LBO), Coder Groups |
| 14. SIP Signalling Configuration | 1496–1581 | SIP Interfaces, Proxy Sets (all roles) |
| 15. Routing Configuration | 1583–1779 | IP Profiles, IP Groups, Classification Rules, Routing scenarios |
| 16. Firewall Rules | 1783–2055 | All firewall rule tables for Proxy, OVOC, ARM, Downstream |
| 19. HA Considerations | 2223–2468 | HA architecture, failover mechanism, SIP trunk HA, voice recording |
| Appendix C | 3314–3369 | Port summary, instance summary |
| Appendix D | 3372–3531 | Interface mappings, call flow diagrams |

---

## 10. Appendix: Standards and References

| Standard / Reference | Relevance |
|---------------------|-----------|
| RFC 3261 — SIP: Session Initiation Protocol | Core SIP signalling reference |
| RFC 3711 — SRTP: Secure Real-time Transport Protocol | Media encryption (Teams requirement) |
| RFC 2833 — RTP Payload for DTMF Digits | DTMF relay configuration |
| RFC 4028 — Session Timers in SIP | Zombie call cleanup |
| RFC 3550 — RTP: Real-Time Transport Protocol | Media transport |
| ITU-T T.38 — Fax over IP | Fax relay protocol |
| ITU-T G.711 — Pulse Code Modulation | Primary voice codec |
| ITU-T G.729 — Coding of Speech at 8 kbit/s | Low-bandwidth voice codec |
| AudioCodes Mediant VE SBC Installation Manual v7.4 / v7.6 | Vendor installation reference |
| AudioCodes SBC Teams Direct Routing Configuration Note | Teams integration reference |
| Microsoft Teams Direct Routing Planning Guide | Microsoft requirements |
| AudioCodes Mediant 800C Datasheet | Downstream SBC specifications |
| Telecommunications Act 1997 (Australia) — Emergency Calling | AU regulatory requirement |
| Kari's Law / RAY BAUM's Act (US) | US emergency calling regulation |

---

*End of SBC Engineer Review Report*
