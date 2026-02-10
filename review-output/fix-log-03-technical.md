# Fix Log 03 -- Technical Consistency

**Source review:** `02-technical-consistency.md`
**Target file:** `AudioCodes-AWS-Deployment-Guide.md`
**Date:** 2026-02-10

---

## Fixes Applied

### Fix 1: Document Version (line 5)

- **Issue:** Header said "Document Version: 1.1" but the Document Control table records changes through version 1.7.
- **Change:** `1.1` -> `1.7`
- **Review issue:** #10

### Fix 2: QoE/Control Reports Port 5000 -> 5001 (2 locations)

- **Issue:** OVOC Security Group (line 486) and Appendix C port summary (line 3240) listed port 5000 for "Control/Media reports," while all firewall rule tables in Section 16 and Appendix D consistently use port 5001 for "QoE Reporting."
- **Changes:**
  - OVOC Security Group table: `TCP | 5000 | Control/Media reports` -> `TCP | 5001 | QoE Reporting`
  - Appendix C port summary: `TCP | 5000 | Control/Media reports from SBCs` -> `TCP | 5001 | QoE Reporting from SBCs`
- **Review issue:** #2

### Fix 3: SBC Instance Type in Appendix C (line 3269)

- **Issue:** Appendix C Instance Type Summary listed `m5.large` for the SBC (No Transcoding), while the Compute Requirements tables in Sections 4 and 9.4 and the Appendix D diagram all use `m5n.large`.
- **Change:** `m5.large` -> `m5n.large` in Appendix C table row
- **Note:** Section 4 line 281 retains `m5.large` in the general EC2 instance type options table (which lists multiple options); the specific deployment recommendation tables all now consistently use `m5n.large`.
- **Review issue:** #1

### Fix 4: TLS Context Name "Teams Direct Routing" -> "Teams" (5 locations)

- **Issue:** Section 12.1 defines the TLS Context name as "Teams", but the Proxy Sets table, IP Groups table, and design notes referred to it as "Teams Direct Routing."
- **Changes:**
  - Proxy Sets table (Index 1, TLS Context Name column): `Teams Direct Routing` -> `Teams`
  - Proxy Sets design notes: `the "Teams Direct Routing" TLS Context` -> `the "Teams" TLS Context`
  - IP Groups table (Teams Direct Routing Trunk, TLS Context column): `Teams Direct Routing` -> `Teams`
  - IP Groups design notes (Teams Direct Routing Trunk): `the "Teams Direct Routing" TLS Context` -> `the "Teams" TLS Context`
  - IP Groups design notes (TLS Context summary): `TLS Context ("Teams Direct Routing")` -> `TLS Context ("Teams")`
- **Review issue:** #8

### Fix 5: Proxy Set Name Mismatch (line 1727)

- **Issue:** IP Groups table referenced Proxy Set "Prod_AU_Downstream SBC" but the Proxy Sets table defines it as "Prod_Downstream SBC".
- **Change:** `Prod_AU_Downstream SBC` -> `Prod_Downstream SBC` in the IP Groups table
- **Review issue:** #7

### Fix 6: Firewall Protocol TCP -> UDP for Internal SIP Signaling (4 rows)

- **Issue:** Firewall rules for Proxy SBC <-> Downstream SBC SIP signaling specified TCP on ports 5060/5061, but the SIP Interface configuration (Section 14.1) explicitly disables TCP (port 0) on the Internal (LAN) interface and uses only UDP.
- **Changes (Proxy SBC firewall, Integration with Downstream SBC):**
  - Inbound row: `TCP` -> `UDP`, port `5060, 5061` -> `5060`
  - Outbound row: `TCP` -> `UDP`, port `5060, 5061` -> `5060`
- **Changes (Downstream SBC firewall, Integration with Proxy SBC):**
  - Inbound row: `TCP` -> `UDP`, port `5060, 5061` -> `5060`
  - Outbound row: `TCP` -> `UDP`, port `5060, 5061` -> `5060`
- **Review issue:** #13

### Fix 7: Network Interface Mapping (Section 4, lines 288-292)

- **Issue:** Section 4 described a simplified 2-interface model (eth0=Main, eth1=HA) that contradicted the 4-ENI architecture documented in Appendix D.
- **Change:** Replaced the 3-row table with a 4-row table matching Appendix D:
  - `eth0` = Management (OVOC, ARM, SSH, HTTPS) -- Management Subnet
  - `eth1` = LAN/Internal (Downstream SBCs, PBX, SIP Providers) -- Internal Subnet
  - `eth2` = WAN/External (Microsoft Teams Direct Routing, Public SIP) -- DMZ/External Subnet
  - `eth3` = HA Communication + AWS API Access -- HA Subnet (dedicated)
- **Review issue:** #9

### Fix 8: Media Port Range in Deployment Prerequisites (line 821)

- **Issue:** Prerequisite 3 referenced "UDP 49152-65535" as the media port range, which is inconsistent with the actual configured media realm sub-ranges (6000-9999, 10000-19999, 20000-29999, 30000-39999, 40000-49999).
- **Change:** `media ports (UDP 49152-65535, or as defined by the RTP port range)` -> `media ports (UDP 6000-49999, as defined by the configured media realm ranges in Section 14.3)`
- **Review issue:** #6

---

## Review Issues Not Addressed (Out of Scope)

The following issues from `02-technical-consistency.md` were not included in this fix batch:

- **Issue #3 (Stack Manager Role):** Contradictory descriptions of Stack Manager's failover role. Requires broader rewrite of diagram labels and notes across multiple sections.
- **Issue #4 (ARM Configurator Storage 100 GB vs 50 GiB):** Cannot determine correct value; reconciliation needed with vendor documentation.
- **Issue #5 (ARM Router Storage 80 GB vs 20 GiB):** Cannot determine correct value; reconciliation needed with vendor documentation.
- **Issue #11 (login.microsoft.com in D.1 diagram):** Single Mermaid diagram reference; not in the assigned fix list.
- **Issue #12 (Microsoft Teams IP range overlap):** Classification rules vs. firewall rules; may be by design (SIP classification vs. media).
- **Issue #14 (SNMP source port):** May be AudioCodes-specific behavior; needs vendor confirmation.
