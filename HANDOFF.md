# Claude Session Handoff

## Repository

- **Path:** `/home/kevin/public`
- **Remote:** `https://github.com/kevinsing999/public.git`
- **Branch:** `main` (only branch)
- **Status:** Clean, fully pushed to origin as of 13 February 2026

## What This Is

A single-file technical deployment guide: `AudioCodes-AWS-Deployment-Guide.md` (~3,560 lines). It documents the design, deployment, and configuration of AudioCodes SBC infrastructure on AWS with Microsoft Teams Direct Routing integration. The audience is cloud operations and voice engineering teams.

## Document Version

Currently at **v2.6** (13 February 2026). The full changelog is at the bottom of the document under "Document Control" (around line 3535).

## Key Structure

- **Sections 1-22A:** Main body covering AWS infrastructure, SBC configuration, HA, firewall rules, IAM, OVOC, ARM, Stack Manager, cyber security, and OVOC Data Analytics
- **Appendices A-D:** Credentials, checklists, port summaries, and architecture diagrams
- **Diagrams:** Pre-rendered PNGs in `png-diagrams/` (referenced as inline images). SVGs also exist in `svg-diagrams/`. Original Mermaid source has been removed from the markdown.
- **GitHub Pages:** Configured via `_config.yml`, `index.md`, and `_layouts/` for rendering on GitHub Pages with client-side mermaid.js

## What Was Done in Previous Sessions (12 Feb 2026)

1. **v2.3 — RADIUS authentication & OVOC audit logging**
   - Replaced SBC management auth from LDAPS to RADIUS with Cisco ISE
   - Documented AudioCodes VSA dictionary (Vendor ID 5003, ACL-Auth-Level attribute 35)
   - Noted TACACS+ is not supported on AudioCodes SBC products
   - Added OVOC audit logging (syslog, SNMP traps, dual-layer auditd + Actions Journal)
   - Updated authentication architecture diagram (PNG)
   - Added Stack Manager supported OS list and SOE compatibility
   - Clarified bidirectional SIP connectivity for site SBCs, third-party PBX, and ATAs

2. **v2.4 — CDR access auditing**
   - Added CDR access auditing guidance to Section 22A (OVOC Data Analytics)
   - Documented that OVOC does not natively log individual SQL queries via the Analytics API
   - Added 4-layer auditing approach for Analytics API (PostgreSQL logging, pgAudit, network-level, data lake)
   - Documented shared analytics account limitation and mitigations
   - Documented OVOC GUI CDR viewing audit limitation (no native per-record view logging)
   - Added 7 mitigations for GUI audit gap
   - Included risk acceptance template for compliance documentation
   - Added v2.4 changelog entry
   - Updated all changelog entries from "February 2026" to specific dates (e.g., "12 February 2026") using git commit history

## What Was Done in This Session (13 Feb 2026)

**v2.5 — Network interface remapping and security architecture update (10 items of stakeholder feedback)**

Implemented across two sub-sessions (initial implementation + QA-driven remediation):

1. **Interface remapping (eth0=HA, eth1=OAMP+LAN, eth2=WAN)**
   - Updated Section 4 Network Interfaces Required table
   - Cascaded through Section 11 SBC configuration tables: Virtual Ports (GE_1→Group 1=HA, GE_2→Group 2=OAMP+Internal, GE_3→Group 3=External), Ethernet Groups, Ethernet Device Config, and ENI-to-GE description paragraph
   - Updated Appendix D.8.7 Interface Summary, Key Concepts, and D.8.8 Matrix

2. **SIP Provider moved from Internal to External (WAN) interface**
   - Updated PSTN_Media_Realm binding, Proxy Set SIP Interfaces
   - Cascaded through Section 19 HA/failover: Traffic Types table, Information Exchange table, Connectivity Summary table, Key Design Points
   - Removed SIP Provider from Cloud East-West Firewall scope (now on External interface)

3. **Security Groups split into three per-interface groups**
   - SBC HA Security Group (eth0), SBC Internal Security Group (eth1), SBC External Security Group (eth2)
   - Added cross-region VPC CIDR inbound rules to SBC, ARM, and OVOC Security Groups
   - SNMP 161 and HTTPS 443 from OVOC on Internal SG
   - Teams media narrowed to 20000-21999, PSTN media 40000-41999 on External SG

4. **Section 16 firewall rules**
   - Teams media port range 20000-29999 → 20000-21999
   - Added bidirectional SIP signalling and media rules for SIP Provider AU (Telstra REGISTER-type) and US
   - Renamed Downstream SBC to Downstream Devices (SBC, Media Pack, Cisco)
   - Added TCP 5061 (TLS) for inter-device SIP trunks

5. **HA and SIP trunk behaviour**
   - Failover: ongoing calls should not drop, sessions synchronised, no Re-INVITE in VIP model
   - SIP trunk flow: bidirectional from firewall perspective, restricting to outbound-only may cause early media issues

6. **Other changes**
   - Removed App Registration 3 (ARM REST API Authentication); renumbered App Registration 4 to 3
   - Added LMO scope clarification (local users only, EUC/voice subnet mapping required)
   - Clarified authentication model (SBCs=RADIUS, OVOC/ARM=Entra ID, OVOC SSO for SBC management)
   - Updated Appendix C/D port summaries (split 6000-41999 into 4 specific Media Realm ranges)
   - Updated Mermaid diagrams — see "Diagram Changes" below for full details

7. **Diagram changes**
   - **d8-7-complete-solution.mmd (Diagram 25):** Fixed SIP Provider AU routing from Internal (IntIF) to External (ExtIF); corrected Internal RTP range from 6000-41999 to 6000-19999; added SIP Provider ports to External interface label; removed stale US Stack Manager node and connections; updated SRTP port range; LDAPS→RADIUS
   - **09-ha-connectivity-architecture-diagram.mmd (Diagram 09):** Created new Mermaid source from scratch. Shows HA connectivity architecture with SIP Provider on External interface VIP (bidirectional), Downstream SBCs/PBX on Internal VIP, Elastic IP for Teams, and note boxes explaining the connectivity model
   - **18-d81-proxy-sbc-aws-complete-interface-architecture.mmd (Diagram 18):** Created new Mermaid source from scratch. Shows complete Proxy SBC interface chain: Ethernet Groups → IP Interfaces → Media Realms → SIP Interfaces → IP Groups. Reflects new Group 1=HA, Group 2=OAMP+Internal, Group 3=External mapping
   - **d8-7-simplified.mmd (Diagram 26):** No changes in this session (already correct from previous session)
   - **05-authentication-architecture-overview.mmd (Diagram 05):** No source changes, re-rendered only
   - **Re-rendered all 5 diagrams** (05, 09, 18, 25, 26) as both PNG and SVG
   - **Remaining diagrams without .mmd source:** Diagrams 04, 07, 12-17, 19-24 are PNG-only (no Mermaid source). Some may be affected by v2.5 interface changes (especially 12-17 which cover SBC configuration screens) but would need manual recreation from scratch

8. **D.6 Port Summary and changelog table fixes**
   - Fixed D.6 Port Summary category rows (Signalling, Media, Management) — had only 1 cell in a 6-column table, breaking some markdown parsers. Padded to full 6 columns
   - Fixed v2.5 changelog entry rendering as plain text — a blank line between v2.4 and v2.5 rows broke the markdown table continuity

9. **QA and remediation**
   - Ran 4 QA agents (version/removals, interface remapping, security/firewall, content changes)
   - Identified and fixed cascading failures: Section 11 SBC config tables and Section 19 SIP Provider references not updated in initial pass
   - All verification checks pass (no stale eth0/OAMP, no GE_3/HA, no SIP Provider/Internal, no Claude references)

**v2.6 — Security group egress hardening and VPC Endpoints**

10. **Replaced all 0.0.0.0/0 security group outbound rules with specific destinations**
    - **Stack Manager SG:** TCP 443 → VPC Endpoint SG (EC2, CloudFormation, CloudWatch, IAM via PrivateLink) + S3 Prefix List
    - **SBC HA SG (eth0):** TCP 443 → VPC Endpoint SG (EC2 API for HA failover route table updates, EIP reassignment)
    - **SBC Internal SG (eth1):** All/All → 7 specific rules: SIP signalling (TCP/UDP 5060-5061 → VPC CIDR), RTP media (UDP 6000-39999 → VPC CIDR), OVOC management/SNMP/syslog/QoE (→ OVOC CIDR), cross-region (→ Other Region VPC CIDR)
    - **SBC External SG (eth2):** All/All → 5 specific rules: Teams SIP (TCP 5061 → 52.112.0.0/14, 52.120.0.0/14), Teams SRTP (UDP 20000-21999 → same), SIP Provider signalling/media (→ SIP Provider CIDRs), cross-region
    - **ARM SG:** All/All → Microsoft Graph/Entra ID CIDRs (M365 Endpoint ID 56: 20.20.32.0/19, 20.190.128.0/18, 20.231.128.0/19, 40.126.0.0/18) + VPC CIDR + cross-region
    - **OVOC SG:** TCP 443 → same M365 Endpoint ID 56 CIDRs

11. **Added Security Group Design Notes** (after SG tables in Section 5.3)
    - Explains least-privilege egress approach, VPC Endpoints for AWS API, S3 Gateway Endpoint, M365 CIDR maintenance, Teams DR CIDR stability, SIP Provider CIDR management

12. **Added VPC Endpoints (PrivateLink) subsection to Section 20**
    - Required endpoints: EC2 (critical for HA), S3 Gateway (free), CloudFormation, CloudWatch, STS
    - Optional endpoints: SSM, SSM Messages, CloudWatch Logs, ELB
    - VPC Endpoint Security Group table
    - Configuration notes: Private DNS, EC2 endpoint in HA subnet, S3 prefix list, cost estimate (~$73/month/region)

13. **Diagram alignment verified**
    - All 5 .mmd source diagrams checked — no 0.0.0.0/0 or security group rules depicted; diagrams show connectivity architecture, not SG rules
    - SVG text search found 3 PNG-only diagrams with related content (04 Subnet Design, 06 Deployment Sequence, 24 Stack Manager) — no conflicts, potential future enhancement only

## Important Conventions

- **Do not mention Claude** as a contributor in commits, changelog, or anywhere in the document. All authorship is attributed to "KS".
- **British/Australian English** spelling throughout (standardised, colour, etc.)
- **Commit messages** should not include `Co-Authored-By: Claude` lines
- **Diagrams** are pre-rendered PNGs (the Mermaid source is gone from the markdown). Mermaid `.mmd` source files exist in `diagrams/` for: 05 (authentication), 09 (HA connectivity), 18 (D.8.1 interface architecture), 25 (d8-7 complete solution), 26 (d8-7 simplified). Render with: `npx mmdc -i diagrams/<file>.mmd -o png-diagrams/<file>.png -t neutral -b white -w 2400`. Diagrams without .mmd source (04, 07, 12-17, 19-24) are PNG-only and would need manual recreation if updates are required.
- **Document version** in the header (line 5) and changelog must stay in sync

## Repo Contents

```
AudioCodes-AWS-Deployment-Guide.md   # The main document
png-diagrams/                        # 26 pre-rendered PNG diagrams
svg-diagrams/                        # SVG versions of diagrams
diagrams/                            # Diagram source/working files
_config.yml, index.md, _layouts/     # GitHub Pages configuration
review-output/                       # Validation/review reports
package.json, node_modules/          # Node dependencies (mermaid CLI for diagram generation)
```
