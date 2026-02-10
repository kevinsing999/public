# Validation Pass 02 - Consistency Check

**Document:** `/home/kevin/public/AudioCodes-AWS-Deployment-Guide.md`
**Date:** 2026-02-10
**Reviewer:** Automated (Claude)

---

## Summary

| # | Check | Result |
|---|-------|--------|
| 1 | Stack Manager role | **FAIL** |
| 2 | QoE port (5001) | **PASS** |
| 3 | Document version 1.7 | **PASS** |
| 4 | TLS Context name ("Teams") | **PASS** |
| 5 | Proxy Set name (no Prod_AU_Downstream) | **PASS** |
| 6 | gp2/GP2 eliminated | **PASS** |
| 7 | Section 4 interface mapping (4 interfaces, matches Appendix D) | **FAIL** |
| 8 | revertive-mode Off description | **PASS** |
| 9 | Spelling: "signaling" vs "signalling" | **PASS** |
| 10 | login.microsoft.com eliminated | **PASS** |
| 11 | Markdown separators (Sections 13/14 and 14/15) | **PASS** |
| 12 | General markdown integrity | **PASS** |

**Overall: 2 FAIL, 10 PASS**

---

## Detailed Findings

### 1. Stack Manager Role -- FAIL

The majority of Stack Manager references are correct (deployment-only, Day 2 operations, not active failover). However, one instance uses ambiguous language that could imply active HA involvement:

**Line 49:**
```
- **AudioCodes Stack Manager** for HA lifecycle management
```

The phrase "HA lifecycle management" is ambiguous. While it could mean managing the lifecycle of the HA deployment (deployment, updates, healing), it could also be read as actively managing HA failover. This is in the Executive Summary bullet list, a high-visibility location.

**Recommended fix:** Change to:
```
- **AudioCodes Stack Manager** for initial HA deployment and Day 2 operations
```

All other Stack Manager references (lines 55, 59, 81-91, 95, 148-149, 179, 275, 321, 386, 403-404, 412, 452, 857, 2305-2318, 2788, 2813, 2865-2900, etc.) correctly describe it as handling deployment, Day 2 operations, and explicitly state it does NOT participate in active failover. These are all correct.

---

### 2. QoE Port -- PASS

All QoE port references consistently use **5001**. No instances of port 5000 for QoE found anywhere.

Verified at lines: 489, 1890, 1986, 2069, 3246, 3533, 3647, 3915, 3948.

---

### 3. Document Version -- PASS

Line 5 reads:
```
**Document Version:** 1.7
```

Correct. The changelog at line 4387 also includes a 1.7 entry.

---

### 4. TLS Context Name -- PASS

"Teams Direct Routing" appears throughout the document as a **general concept name** (e.g., "Microsoft Teams Direct Routing requirements", "Teams Direct Routing Trunk", "Teams Direct Routing Profile"), which is correct and expected.

The TLS Context is consistently named **"Teams"** (not "Teams Direct Routing") in all configuration references:
- Line 1412: `TLS Context named "Teams"`
- Line 1438: `"Teams" TLS Context`
- Line 1465, 1472, 1473, 1479, 1496: All reference the `"Teams"` TLS Context
- Line 1604: Table shows `Teams` in TLS Context Name column
- Line 1639: Proxy Set table shows `Teams` for TLS Context Name
- Line 1733: IP Group table shows `Teams` for TLS Context
- Line 1750: Explicitly states `TLS Context ("Teams")`
- Line 3726: Mermaid diagram correctly shows `TLS Context: Teams`

No instances of "Teams Direct Routing" used as a TLS Context name.

---

### 5. Proxy Set Name -- PASS

Zero instances of `Prod_AU_Downstream` found in the document. The correct name `Prod_Downstream SBC` is used consistently at lines 1640, 1649, and 1734.

---

### 6. gp2/GP2 Eliminated -- PASS

Zero instances of `gp2` or `GP2` found anywhere in the document. All storage references use gp3/GP3 (e.g., line 379: "GP3 SSD 2 TB", line 3274: "8 GiB gp3").

---

### 7. Interface Mapping (Section 4 vs Appendix D) -- FAIL

**Section 4 (lines 288-293)** correctly shows 4 interfaces:

| Interface | Purpose | Subnet Type |
|-----------|---------|-------------|
| eth0 | Management | Management Subnet |
| eth1 | LAN/Internal | Internal Subnet |
| eth2 | WAN/External | DMZ/External Subnet |
| eth3 | HA Communication + AWS API Access | HA Subnet (dedicated) |

**Appendix D.8.1 (lines 3698-3701)** correctly shows 4 ENIs mapping to eth0-eth3:
- eth0 -> Management ENI
- eth1 -> Internal ENI
- eth2 -> External ENI
- eth3 -> HA ENI

**Appendix D.8.8 (lines 4217-4220)** also correctly shows eth0-eth3 with matching assignments.

These all match. **However**, there is an inconsistency in a **mermaid diagram in Section 5** (Subnet Design, lines 424-434):

**Lines 425 and 433:**
```
SBC_HA_A["SBC eth1 (HA traffic)"]
SBC_HA_B["SBC eth1 (HA traffic)"]
```

The HA subnet nodes are labeled as `eth1` but the HA interface is `eth3`. This contradicts Section 4 (line 293), Appendix D.8.1 (line 3701), and Appendix D.8.8 (line 4220), all of which correctly say eth3 is the HA interface.

**Recommended fix:** Lines 425 and 433 should be:
```
SBC_HA_A["SBC eth3 (HA traffic)"]
SBC_HA_B["SBC eth3 (HA traffic)"]
```

Note: This is technically in Section 5 (AWS Infrastructure Requirements), not Section 4, but it directly relates to interface mapping consistency.

---

### 8. revertive-mode Off Description -- PASS

Both revertive-mode descriptions are correct and consistent:

**Line 903 (SBC HA Configuration - Instance 1):**
> When the preferred Active instance recovers from a failure, it will **not** automatically resume the Active role. Instead, the recovered instance remains in Standby until a manual switchover or subsequent failure event. This prevents unnecessary service disruption caused by repeated role changes.

**Line 928 (SBC HA Configuration - Instance 2):**
> When the preferred Active instance recovers from a failure, it will **not** automatically resume the Active role. Instead, the recovered instance remains in Standby until a manual switchover or subsequent failure event. This prevents unnecessary service disruption caused by repeated role changes.

Both correctly describe Off behavior: recovered instance stays in Standby.

---

### 9. Spelling: "signaling" vs "signalling" -- PASS

Zero instances of American spelling "signaling" found anywhere in the document. All prose uses the British/Australian spelling "signalling" consistently. No instances found inside code blocks, PowerShell parameters, or mermaid diagrams either (so there is nothing to exempt).

---

### 10. login.microsoft.com -- PASS

Zero instances of the incorrect `login.microsoft.com` found. All references use the correct `login.microsoftonline.com`:
- Line 642: `POST https://login.microsoftonline.com/{TenantID}/oauth2/v2.0/token`
- Line 663: `https://login.microsoftonline.com/common/oauth2/nativeclient`
- Line 1219: `login.microsoftonline.com` (OAuth authentication)
- Line 2018: `login.microsoftonline.com` (Azure AD authentication)
- Line 3268: `login.microsoftonline.com` (Azure AD Authentication)
- Line 3294, 3503, 3923, 3935, 3985: All correctly use `login.microsoftonline.com`

---

### 11. Markdown Separators -- PASS

`---` horizontal rule separators exist at the correct locations:

- **Between Sections 13 and 14:** Line 1588 contains `---`, immediately before `## 14. SIP Signalling Configuration` on line 1590.
- **Between Sections 14 and 15:** Line 1675 contains `---`, immediately before `## 15. Routing Configuration` on line 1677.

---

### 12. General Markdown Integrity -- PASS

- **Code blocks:** 68 triple-backtick lines total = 34 code blocks. All properly opened and closed. 33 have language identifiers (mermaid, json, powershell), 1 is bare (line 641, a plain HTTP request example). All balanced.
- **Tables:** Approximately 1000 table rows found. Spot-checked multiple tables; no garbled or mangled rows detected.
- **No garbled text from bad string replacements** detected during the full-text searches.
- **No unclosed code blocks** found.

---

## Action Items

1. **Line 49:** Reword "HA lifecycle management" to "initial HA deployment and Day 2 operations" to remove ambiguity about Stack Manager's role in active failover.
2. **Lines 425 and 433:** Change `eth1` to `eth3` in the Subnet Design mermaid diagram to match the documented interface mapping (eth3 = HA interface).
