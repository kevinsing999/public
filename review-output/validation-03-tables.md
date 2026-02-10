# Validation 03: Markdown Table Integrity Check

**File:** `/home/kevin/public/AudioCodes-AWS-Deployment-Guide.md`
**Date:** 2026-02-10
**Validator:** Claude Opus 4

---

## 1. OVOC Security Group Table (line 483)

**Result: PASS**

The table at lines 483-491 is properly formatted with 5 columns (Direction | Protocol | Port | Source/Destination | Purpose), a correct separator row, and 7 data rows. Column alignment is consistent. The QoE row (line 489) correctly shows:

```
| Inbound | TCP | 5001 | SBC CIDR | QoE Reporting |
```

Port 5001 is present and correct.

---

## 2. Compute Requirements Summary Tables (Section 4, line 375 and Section 9.4, line 940)

### Section 4 Table (line 375)

**Result: PASS**

The table has 6 columns (Application | Resource | Instance Type | Memory | Recommended Disk Space | Processors) with a correct separator row and 5 data rows. All rows have the correct column count of 6. The notes block (lines 383-389) is coherent and well-formed as a blockquote with 5 bullet points.

### Section 9.4 Table (line 940)

**Result: PASS**

The table at lines 940-946 is identical in structure and content to the Section 4 table (6 columns, 5 data rows). All column counts match. The notes block (lines 948-954) is identical and coherent.

Both tables are consistent with each other -- same data, same formatting.

---

## 3. Appendix C Instance Type Summary Table (line 3272)

**Result: PASS**

The table at lines 3272-3280 has 6 columns (Component | Environment | Instance Type | vCPUs | Memory | Storage) with 7 data rows. All rows have the correct column count.

Verified values:
- **SBC (No Transcoding):** Instance Type = `m5n.large` (line 3275) -- correct.
- **ARM Configurator:** Storage = `100 GB gp3` (line 3277) -- correct.
- **ARM Router:** Storage = `80 GB gp3` (line 3278) -- correct.

---

## 4. Appendix C Port Summary Table (line 3236)

**Result: PASS**

The Signalling Ports table at lines 3236-3249 has 5 columns (Component | Protocol | Port | Direction | Purpose) with 12 data rows. The QoE row (line 3246) correctly shows:

```
| OVOC | TCP | 5001 | Inbound | QoE Reporting from SBCs |
```

Port 5001 is present and correct.

The Media Ports sub-table (lines 3253-3256) is also properly formatted with 5 columns and 2 data rows.

---

## 5. Network Interfaces Table in Section 4 (line 288)

**Result: PASS**

The table at lines 288-293 has 3 columns (Interface | Purpose | Subnet Type) with 4 data rows:

| Row | Interface | Purpose | Subnet Type |
|-----|-----------|---------|-------------|
| 1   | eth0      | Management (OVOC, ARM, SSH, HTTPS) | Management Subnet |
| 2   | eth1      | LAN/Internal (Downstream SBCs, PBX, SIP Providers) | Internal Subnet |
| 3   | eth2      | WAN/External (Microsoft Teams Direct Routing, Public SIP) | DMZ/External Subnet |
| 4   | eth3      | HA Communication + AWS API Access | HA Subnet (dedicated) |

All 4 rows (eth0-eth3) are present with correct column counts and consistent formatting.

---

## 6. Proxy Sets Tables (Section 14.2, lines 1637-1673)

**Result: PASS**

Three Proxy Sets tables were checked:

- **Proxy SBC Proxy Sets** (line 1637): 7 columns, 6 data rows. Properly formatted.
- **Downstream SBC Proxy Sets** (line 1662): 7 columns, 1 data row. Properly formatted.
- **Downstream SBC with LBO Proxy Sets** (line 1670): 7 columns, 2 data rows. Properly formatted.

All separator rows are correct. Column counts are consistent across all rows.

---

## 7. IP Groups Tables (Section 15.2, lines 1731-1769)

**Result: PASS**

Three IP Groups tables were checked:

- **Proxy SBC IP Groups** (line 1731): 5 columns, 7 data rows. Properly formatted.
- **Downstream SBC IP Groups** (line 1756): 5 columns, 2 data rows. Properly formatted.
- **Downstream SBC with LBO IP Groups** (line 1765): 5 columns, 3 data rows. Properly formatted.

The Proxy Set reference for the Downstream SBC Trunk (line 1734) shows `Prod_Downstream SBC` -- correct as specified.

---

## 8. TLS Context Table (Section 12, line 1416)

**Result: PASS**

The table at lines 1416-1427 has 2 columns (Parameter | Value) with 7 data rows. The Name value is `Teams` (line 1419) -- correct as specified. Table formatting is intact with proper separator row and consistent column alignment.

---

## 9. Firewall Rules Tables (Section 16, lines 1877-2185)

**Result: PASS**

Spot-checked the following tables for structural integrity after TCP/UDP edits:

- **16.1 Device Administration via OVOC** (line 1885): 8 columns, 7 rows. SNMP rows correctly show `UDP`, QoE shows `TCP (TLS)`, Device Management shows `TCP`. Formatting intact.
- **16.1 Teams Direct Routing** (line 1915): 8 columns, 4 rows. Signalling rows show `TCP`, Media rows show `UDP`. Correct and intact.
- **16.1 Integration with Downstream SBC** (line 1938): 8 columns, 4 rows. SIP rows show `UDP`, media rows show `UDP`. Correct and intact.
- **16.2 OVOC Firewall Rules - Device Administration** (line 1981): 8 columns, 7 rows. Same structure as 16.1 equivalent. Intact.
- **16.3 ARM Firewall Rules** (line 2025): 8 columns, multiple sub-tables. All properly formatted.
- **16.4 Downstream SBC Firewall Rules** (line 2064): 8 columns across multiple sub-tables. All intact.
- **16.5 SIP Generic Endpoint** (line 2135): 8 columns. Intact.
- **16.6 Teams Endpoints** (line 2161): 8 columns. Intact.

All firewall tables maintain consistent 8-column structure (Service | Direction | Protocol | Source | Src Port | Destination | Dst Port | Remark) with properly aligned separator rows. No broken rows detected.

---

## 10. Root CA Trust Anchors Table (line 1483)

**Result: PASS**

The table at lines 1483-1488 has 2 columns (Certificate Name | Purpose) with 4 data rows. Verified content:

| Certificate Name | Purpose |
|---|---|
| DigiCert Global Root G2 | Root CA trust anchor for Microsoft SIP certs |
| DigiCert Global Root G3 | Included as a precautionary measure; DigiCert Global Root G2 is the confirmed active root CA for Teams SIP |
| Baltimore CyberTrust Root | Expired May 2025; retain only if required for backward compatibility with older configurations |
| DigiCert intermediate certificates (as needed) | Intermediate CA certificates in the chain |

DigiCert G3 note is in the correct Purpose column (line 1486). Baltimore note about expiry is in the correct Purpose column (line 1487). Table structure is intact.

---

## 11. HA Parameters Tables (Sections 9.3.2 and 9.3.4)

### Section 9.3.2 Proxy SBC HA Configuration (line 901)

**Result: PASS**

The table at lines 901-907 has 3 columns (Parameter | Value | Description) with 5 data rows. The `revertive-mode` row (line 903) is properly formatted:

```
| **revertive-mode** (Pre-empt mode) | Off | When the preferred Active instance recovers from a failure, it will **not** automatically resume the Active role. Instead, the recovered instance remains in Standby until a manual switchover or subsequent failure event. This prevents unnecessary service disruption caused by repeated role changes. |
```

Description is coherent and complete.

### Section 9.3.4 Downstream SBC HA Configuration (line 926)

**Result: PASS**

The table at lines 926-932 has 3 columns (Parameter | Value | Description) with 5 data rows. The `revertive-mode` row (line 928) is properly formatted with the same description as the Proxy SBC table. Both tables are structurally identical and consistent.

---

## 12. SBC Prerequisites Table (Section 9.1, line 817)

**Result: PASS**

The table at lines 817-825 has 4 columns (# | Prerequisite | Details | Notes) with 7 data rows (prerequisites 1-7). All rows have the correct column count of 4.

The media port range reference appears in row 3 (line 821, "AWS Networking Readiness"):

```
Signalling ports (TCP/TLS 5061) and media ports (UDP 6000-49999, as defined by the configured media realm ranges in Section 14.3) must be explicitly allowed.
```

The media port range `UDP 6000-49999` is intact within the Details column. The row is properly formatted with no broken pipe characters or column misalignment.

---

## Summary

| # | Table | Location | Result |
|---|-------|----------|--------|
| 1 | OVOC Security Group | Line 483 | PASS |
| 2a | Compute Requirements (Section 4) | Line 375 | PASS |
| 2b | Compute Requirements (Section 9.4) | Line 940 | PASS |
| 3 | Appendix C Instance Type Summary | Line 3272 | PASS |
| 4 | Appendix C Port Summary | Line 3236 | PASS |
| 5 | Network Interfaces (Section 4) | Line 288 | PASS |
| 6 | Proxy Sets (Section 14.2) | Line 1637 | PASS |
| 7 | IP Groups (Section 15.2) | Line 1731 | PASS |
| 8 | TLS Context (Section 12) | Line 1416 | PASS |
| 9 | Firewall Rules (Section 16) | Lines 1877-2185 | PASS |
| 10 | Root CA Trust Anchors | Line 1483 | PASS |
| 11a | HA Parameters (Section 9.3.2) | Line 901 | PASS |
| 11b | HA Parameters (Section 9.3.4) | Line 926 | PASS |
| 12 | SBC Prerequisites (Section 9.1) | Line 817 | PASS |

**Overall Result: ALL TABLES PASS -- No formatting issues detected.**
