# Technical Consistency Review

## Summary

The document is a large (4,378 lines) deployment guide covering AudioCodes SBC infrastructure on AWS with Microsoft Teams Direct Routing. The review identified **15 substantive inconsistencies** spanning instance types, port numbers, storage specifications, naming mismatches, the Stack Manager's described role, TLS context naming, network interface mappings, and Microsoft endpoint references. Most issues are internal contradictions between different sections of the same document rather than outright errors. Several items relate to the same class of problem (e.g., the document says in some places the Stack Manager handles failover, and in others that it does not).

---

## Issues Found

### Issue 1: SBC Instance Type Inconsistency (m5.large vs. m5n.large)

- **Lines:** 281, 374, 382, 939, 947, 3269, 3665
- **Inconsistency:** Section 4 "Recommended EC2 Instance Types" (line 281) lists `m5.large` for the SBC without transcoding. However, the "Compute Requirements Summary" table (lines 374, 939) and the Appendix D diagram (line 3665) use `m5n.large` for the same role. The Appendix C "Instance Type Summary" (line 3269) reverts to `m5.large`.
- **Which is correct:** Cannot determine authoritatively. The notes at lines 382/947 explicitly state m5n.large was chosen for enhanced networking. The Appendix C table at 3269 likely needs updating to `m5n.large` for consistency with the compute requirements tables, or the compute tables need to match Section 4. This should be reconciled to a single recommendation.

### Issue 2: OVOC QoE/Control Reports Port -- 5000 vs. 5001

- **Lines:** 486, 3240 (port 5000) vs. 1883, 1979, 2062, 3526, 3634, 3902 (port 5001)
- **Inconsistency:** The OVOC Security Group (line 486) and the Appendix C port summary (line 3240) list port **5000** for "Control/Media reports." However, all firewall rule tables in Section 16 (lines 1883, 1979, 2062), the Appendix D management flow diagram (line 3526), the Appendix D port summary quick reference (line 3634), and the OVOC interface diagram (line 3902) consistently use port **5001** for "QoE Reporting."
- **Which is correct:** Port 5001 appears far more frequently and is used in all detailed firewall rule sections. Lines 486 and 3240 should likely be corrected to 5001, or the naming/purpose should be clarified if 5000 and 5001 are genuinely different services.

### Issue 3: Stack Manager Role -- Contradictory Descriptions

- **Lines:** 55, 91, 95, 338, 854, 893, 2893, 4094 (does NOT handle failover) vs. 179, 215, 383, 409, 854, 948, 3301 (describes it as managing/orchestrating failover)
- **Inconsistency:** The document's primary narrative (Section 1 line 55, Section 2 lines 91/95, Section 4 line 338, Section 21 line 2893, and the D.8.6 diagram note at line 4094) clearly states the Stack Manager does NOT participate in active HA failover. However, several Mermaid diagram labels say "Manages HA failover" (lines 179, 215), the compute notes say "mandatory for HA failover orchestration" (lines 383, 948), the subnet diagram says "Used by Stack Manager for failover routing" (line 409), Section 9.3.1 (line 854) says it "manages HA failover by programmatically updating VPC route tables," and the Appendix D high-level diagram (line 3301) labels it with "HA Failover / Route Table Updates."
- **Which is correct:** The detailed technical explanation (SBCs call AWS APIs themselves for failover) is the correct description per AudioCodes documentation. The diagram labels and notes at lines 179, 215, 383, 409, 854, 948, and 3301 are misleading and should be corrected to say something like "Deploys HA stack" or "Initial deployment & Day 2 ops" rather than implying it handles active failover.

### Issue 4: ARM Configurator Storage -- 100 GB vs. 50 GiB

- **Lines:** 377, 942 (100 GB) vs. 3271 (50 GiB gp3)
- **Inconsistency:** The Compute Requirements Summary tables (lines 377 and 942) list 100 GB for the ARM Configurator. The Appendix C Instance Type Summary (line 3271) lists 50 GiB gp3.
- **Which is correct:** Cannot determine. The body of the document uses 100 GB consistently (appears twice). Appendix C should be reconciled.

### Issue 5: ARM Router Storage -- 80 GB vs. 20 GiB

- **Lines:** 378, 943 (80 GB) vs. 3272 (20 GiB gp3)
- **Inconsistency:** The Compute Requirements Summary tables list 80 GB for the ARM Router. The Appendix C Instance Type Summary lists 20 GiB gp3.
- **Which is correct:** Cannot determine. Same reconciliation issue as ARM Configurator above.

### Issue 6: SBC Media Port Range -- Security Group vs. Firewall Rules vs. Diagrams

- **Lines:** 465 (6000-65535), 818 (49152-65535), 3249 (6000-65535) vs. detailed firewall rules using specific sub-ranges (10000-19999, 20000-29999, 30000-39999, 40000-49999, 6000-9999)
- **Inconsistency:** The SBC Security Group (line 465) and Appendix C (line 3249) define the inbound media port range as UDP 6000-65535. Section 9.1 prerequisite 3 (line 818) references "UDP 49152-65535, or as defined by the RTP port range." However, the actual firewall rules in Section 16 and diagrams in Appendix D use precise sub-ranges: Internal=6000-9999, Downstream=10000-19999, Teams=20000-29999, LMO=30000-39999, PSTN=40000-49999. The security group range of 6000-65535 is a superset, which is a valid approach for security groups, but the 49152-65535 reference in line 818 is inconsistent with the actual configured ranges.
- **Which is correct:** The specific sub-ranges from Section 16 and Appendix D appear to be the actual design. The security group at line 465 is intentionally broad (acceptable). Line 818 referencing 49152-65535 appears to be a leftover from a different design and should reference the actual configured ranges or note the broad range.

### Issue 7: Proxy Set Name Mismatch -- "Prod_Downstream SBC" vs. "Prod_AU_Downstream SBC"

- **Lines:** 1635, 1644 (Prod_Downstream SBC) vs. 1727 (Prod_AU_Downstream SBC)
- **Inconsistency:** The Proxy Sets table (line 1635) defines the proxy set name as "Prod_Downstream SBC" and the design notes (line 1644) reference this same name. However, the IP Groups table (line 1727) references "Prod_AU_Downstream SBC" as the proxy set name for the Downstream SBC Trunk.
- **Which is correct:** These should match. Either the Proxy Set name includes the region qualifier "AU" or it does not.

### Issue 8: TLS Context Name Inconsistency -- "Teams" vs. "Teams Direct Routing"

- **Lines:** 1416 (name: "Teams"), 1605 (TLS Context: "Teams"), 3713 (TLS Context: Teams) vs. 1634, 1643, 1726, 1736, 1743 ("Teams Direct Routing")
- **Inconsistency:** Section 12.1 TLS Context Configuration (line 1416) defines the TLS Context name as "Teams". The SIP Interface table (line 1599) and D.8.1 diagram (line 3713) also use "Teams". However, the Proxy Sets table (line 1634), IP Groups table (line 1726), and associated design notes (lines 1643, 1736, 1743) refer to the TLS Context as "Teams Direct Routing."
- **Which is correct:** The TLS Context was explicitly created with the name "Teams" in Section 12.1. References to "Teams Direct Routing" in Sections 14.2 and 15.2 should be corrected to "Teams" for consistency, or the TLS Context name in Section 12 should be changed.

### Issue 9: Network Interface Mapping -- eth1 as HA vs. eth1 as LAN

- **Lines:** 290-291 (eth0=Main, eth1=HA) vs. 3685-3688, 4131-4148, 4200-4207, 4247-4251 (eth0=Mgmt, eth1=LAN, eth2=WAN, eth3=HA)
- **Inconsistency:** Section 4 "Network Interfaces Required" (lines 290-291) maps eth0 to "Management, Signaling, Media (Main)" and eth1 to "HA Communication + AWS API Access." The subnet diagram (lines 422, 430) also shows "SBC eth1 (HA traffic)." However, the comprehensive D.8.1 diagram (lines 3685-3688), the D.8.7 diagrams (lines 4131-4148, 4247-4251), and the D.8.8 Interface Summary Matrix (lines 4204-4207) all consistently map eth1 to LAN/Internal and eth3 to HA.
- **Which is correct:** The Appendix D mapping (eth0=Mgmt, eth1=LAN, eth2=WAN, eth3=HA) is correct per AudioCodes 4-ENI architecture with 4 Ethernet Groups. Section 4 (lines 290-291) and the subnet diagram (lines 422, 430) are simplified/incorrect and should be updated.

### Issue 10: Document Version Header vs. Document Control Table

- **Line:** 5 (Document Version 1.1) vs. 4367-4374 (versions up to 1.7)
- **Inconsistency:** The header says "Document Version: 1.1" but the Document Control table at the bottom records changes through version 1.7.
- **Which is correct:** The header should read version 1.7 to match the latest entry in the Document Control table.

### Issue 11: Microsoft Login Endpoint -- login.microsoftonline.com vs. login.microsoft.com

- **Lines:** 639, 660, 1216, 2011, 3262, 3496, 3910, 3922, 3972 (login.microsoftonline.com) vs. 3288 (login.microsoft.com)
- **Inconsistency:** All references throughout the document use `login.microsoftonline.com` except the D.1 High-Level Architecture diagram (line 3288) which uses `login.microsoft.com`.
- **Which is correct:** `login.microsoftonline.com` is the correct Microsoft Entra ID OAuth endpoint. Line 3288 should be corrected.

### Issue 12: Microsoft Teams IP Range Overlap/Inconsistency in Classification Rules vs. Firewall Rules

- **Lines:** 1796-1801 (classification rules use 52.112.*.* through 52.115.*.* and 52.122.*.*, 52.123.*.*) vs. 1910-1913 (firewall rules use 52.112.0.0/14 and 52.122.0.0/15 for signaling, but 52.112.0.0/14 and 52.120.0.0/14 for media)
- **Inconsistency:** The classification rules (Section 15.4) only cover 52.112.0.0/14 and 52.122.0.0/15, but the media firewall rules (lines 1912-1913) use 52.120.0.0/14 instead of 52.122.0.0/15. The 52.120.0.0/14 range covers 52.120.0.0-52.123.255.255, which is a superset that includes 52.122.0.0/15. However, the classification rules do not cover the 52.120.*.* and 52.121.*.* ranges at all. If media traffic can originate from those IPs, the SBC classification rules may be incomplete.
- **Note:** The D.7 quick reference (line 3649) indicates 52.120.0.0/14 covers "52.120.0.0 - 52.123.255.255" for media relays. The classification rules at Section 15.4 would not classify SIP messages from 52.120.*.* or 52.121.*.* ranges (only media uses those, so this may be by design if classification is SIP-only).

### Issue 13: Downstream SBC Firewall -- TCP for Internal SIP Signaling vs. UDP in SIP Interface Config

- **Lines:** 1933-1934, 2096-2097 (TCP for SIP signaling between Proxy and Downstream SBC) vs. 1597, 1603, 1613 (SIP Interface uses UDP only, TCP port=0)
- **Inconsistency:** The firewall rules for integration between Proxy SBC and Downstream SBC (lines 1933-1934, 2096-2097) specify TCP as the protocol for SIP signaling on ports 5060/5061. However, the SIP Interface configuration (Section 14.1) explicitly disables TCP (port 0) and TLS (port 0) on the Internal (LAN) SIP Interface, using only UDP. The design notes (line 1603) confirm "internal signaling uses UDP."
- **Which is correct:** The SIP Interface config (UDP only) appears to be the intended design. The firewall rules should list UDP rather than TCP for Downstream-to-Proxy SBC SIP signaling on port 5060.

### Issue 14: OVOC SNMP Source Port Inconsistency

- **Lines:** 1880-1882, 1976-1978, 2059-2061, 3523-3525
- **Inconsistency:** In the firewall rules, SNMP Trap from SBC to OVOC shows source port 161 and destination port 162. However, SNMP traps are typically sent FROM an ephemeral source port, not from port 161. Port 161 is the SNMP agent port (for receiving queries), not the typical source for traps. The same pattern repeats for SNMP Keep-Alive (SBC source port 161 to OVOC destination port 1161). This may be AudioCodes-specific behavior, but it is worth verifying.
- **Note:** This is flagged as a potential issue, not a definitive error, since AudioCodes devices may use port 161 as the source for traps.

### Issue 15: Non-Production VM Count Missing OVOC

- **Lines:** 198-202
- **Inconsistency:** The Non-Production environment is listed as "Total VMs: 5" with 2x SBC, 1x Stack Manager, 1x ARM Configurator, 1x ARM Router. This count is correct for what is listed, but it is worth noting that OVOC is absent from Non-Production (only in Production per line 254). This is not an error, just confirming this is by design since Section 6 line 330 mentions OVOC for Phase 6 is "Production only" and the Mermaid diagram at 172-196 confirms no OVOC in non-prod.

---

## Verified Consistent Items

The following items were checked and found to be consistent across the document:

1. **Virtual IP range 169.254.64.0/24** -- Consistently referenced as the VIP range for HA failover across Sections 2, 5, 9, 19, 21, and Appendix D (lines 86, 407, 852, 2392, 2420, 2483, 2568, 2883, 3688, 4264).

2. **Stack Manager instance type t3.medium** -- Consistently referenced at lines 59, 179, 215, 228, 325, 375, 940, 2871, 3268, 3301, 4063.

3. **ARM instance types** -- ARM Configurator as m4.xlarge and ARM Router as m4.large are consistent across all tables (lines 181, 218-219, 229, 347-348, 377-378, 942-943, 3271-3272).

4. **OVOC instance types** -- m5.2xlarge (Low Profile) and m5.4xlarge (High Profile) are consistent at lines 360-361, 376, 941, 3273-3274.

5. **Microsoft Teams SIP signaling port 5061 (TLS)** -- Consistently referenced at lines 464, 761-763, 792, 818, 1599, 1605, 1910-1911, 3232, 3258-3260, 3297, 3313, 3356, 3622-3623, 3699, 3713.

6. **Teams Direct Routing certificate requirements** -- Consistent between Sections 8 and 12 (public CA requirement, FQDN matching, TLS 1.2 minimum).

7. **SBC IAM policy for HA failover** -- The six EC2 permissions (DescribeRouteTables, CreateRoute, ReplaceRoute, DeleteRoute, DescribeNetworkInterfaces, DescribeInstances) are identically listed at lines 305-311, 2399-2405, 2816-2821.

8. **Stack Manager IAM policy** -- Identical between Section 20 (lines 2790-2802) and Section 21 (lines 2905-2920).

9. **Break glass account names** -- Consistent between Section 17 (lines 2209-2237) and Appendix B (lines 3204-3218).

10. **AWS regions** -- ap-southeast-2 (Australia) and us-east-1 (US) consistently used at lines 173, 209, 222, 873-875.

11. **Microsoft Graph API endpoints** -- graph.microsoft.com and login.microsoftonline.com consistently used (except the one D.1 diagram error noted in Issue 11).

12. **LDAPS port 636** -- Consistently referenced for on-premises Active Directory authentication at lines 1099, 1103, 1134-1135, 1208, 1894, 2073, 2990, 3550, 3697, 3771.

13. **Media realm port sub-ranges** -- The following ranges are consistently applied throughout the firewall rules and diagrams: Teams media=20000-29999, LMO=30000-39999, PSTN=40000-49999, Internal=6000-9999 (Proxy SBC), Downstream-to-Proxy=10000-19999.

14. **SBC minimum version 7.4.500** -- Consistent at lines 274 and 822.

15. **Cross-references** -- All internal section references (Section 10.4, Section 16, Section 17, Section 20, Section 21) point to real, existing sections with correct anchor targets.
