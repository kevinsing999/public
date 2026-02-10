# Fix Log: Mermaid Rendering Issues (Lines 2000-3600)

**File:** `/home/kevin/public/AudioCodes-AWS-Deployment-Guide.md`
**Date:** 2026-02-10
**Scope:** Mermaid diagrams between lines 2000-3600

---

## Summary

| Fix Type | Diagrams Affected | Instances Fixed |
|----------|-------------------|-----------------|
| Remove `---`/`title:` frontmatter | 4 diagrams | 4 frontmatter blocks removed |
| Replace `<-->` with two `-->` lines | 7 diagrams | 19 bidirectional arrows replaced |
| Remove `<b>`/`<i>` HTML tags | 0 in range | None found in range (all on lines 3782+) |

**Total edits:** 23 issues fixed across 9 diagrams.

---

## Diagram-by-Diagram Changes

### 1. SBC Outbound Registration (was line ~2464)

**Fix type:** Remove frontmatter

**Removed:**
```
---
title: SBC Outbound Registration (AU/US Regions)
---
```

No `<-->` arrows present -- no further changes needed.

---

### 2. VIP and VPC Route Table Failover Mechanism (was line ~2484)

**Fix type:** Remove frontmatter

**Removed:**
```
---
title: VIP and VPC Route Table Failover Mechanism
---
```

No `<-->` arrows present -- no further changes needed.

---

### 3. HA Connectivity Architecture (was line ~2548)

**Fix type:** Remove frontmatter + Replace `<-->`

**Removed frontmatter:**
```
---
title: HA Connectivity Architecture - External vs Internal
---
```

**Replaced 1 bidirectional arrow:**

| Before | After |
|--------|-------|
| `SBC1 <-->\|"HA Link<br/>Heartbeat"\| SBC2` | `SBC1 -->\|"HA Link<br/>Heartbeat"\| SBC2` + `SBC2 -->\|"HA Link<br/>Heartbeat"\| SBC1` |

---

### 4. Voice Recording Option 1 - RTP/Unencrypted (was line ~2652)

**Fix type:** Replace `<-->`

**Replaced 3 bidirectional arrows:**

| Before | After |
|--------|-------|
| `Teams <-->\|"SRTP"\| ProxySBC` | `Teams -->\|"SRTP"\| ProxySBC` + `ProxySBC -->\|"SRTP"\| Teams` |
| `ProxySBC <-->\|"RTP"\| DownstreamSBC` | `ProxySBC -->\|"RTP"\| DownstreamSBC` + `DownstreamSBC -->\|"RTP"\| ProxySBC` |
| `DownstreamSBC <-->\|"RTP"\| IPPhones` | `DownstreamSBC -->\|"RTP"\| IPPhones` + `IPPhones -->\|"RTP"\| DownstreamSBC` |

---

### 5. Voice Recording Option 2 - SIPREC (was line ~2699)

**Fix type:** Replace `<-->`

**Replaced 3 bidirectional arrows:**

| Before | After |
|--------|-------|
| `Teams <-->\|"SRTP"\| ProxySBC` | `Teams -->\|"SRTP"\| ProxySBC` + `ProxySBC -->\|"SRTP"\| Teams` |
| `ProxySBC <-->\|"SRTP"\| DownstreamSBC` | `ProxySBC -->\|"SRTP"\| DownstreamSBC` + `DownstreamSBC -->\|"SRTP"\| ProxySBC` |
| `DownstreamSBC <-->\|"SRTP"\| IPPhones` | `DownstreamSBC -->\|"SRTP"\| IPPhones` + `IPPhones -->\|"SRTP"\| DownstreamSBC` |

---

### 6. D.1 High-Level Architecture Overview (was line ~3290)

**Fix type:** Replace `<-->`

**Replaced 3 bidirectional arrows:**

| Before | After |
|--------|-------|
| `Active <--> Standby` | `Active --> Standby` + `Standby --> Active` |
| `M365 <-->\|"HTTPS 443<br/>OVOC - MS: API queries<br/>MS - OVOC: Webhook notifications"\| OVOC` | `M365 -->\|...\| OVOC` + `OVOC -->\|...\| M365` |
| `ProxySBC <-->\|"UDP 5060 (Signalling)<br/>UDP 40000-49999 (Media)"\| SIPProvider` | `ProxySBC -->\|...\| SIPProvider` + `SIPProvider -->\|...\| ProxySBC` |

---

### 7. D.2 SIP Signalling Flows (was line ~3344)

**Fix type:** Remove frontmatter + Replace `<-->`

**Removed frontmatter:**
```
---
title: SIP Signaling Flow Diagram
---
```

**Replaced 7 bidirectional arrows:**

| Before | After |
|--------|-------|
| `Teams <-->\|"TLS 5061"\| ProxySBC` | `Teams -->\|"TLS 5061"\| ProxySBC` + `ProxySBC -->\|"TLS 5061"\| Teams` |
| `DownstreamSBC <-->\|"UDP 5060"\| ProxySBC` | `DownstreamSBC -->\|"UDP 5060"\| ProxySBC` + `ProxySBC -->\|"UDP 5060"\| DownstreamSBC` |
| `PBX <-->\|"UDP 5060"\| ProxySBC` | `PBX -->\|"UDP 5060"\| ProxySBC` + `ProxySBC -->\|"UDP 5060"\| PBX` |
| `OtherProxy <-->\|"TCP 5060/5061"\| ProxySBC` | `OtherProxy -->\|"TCP 5060/5061"\| ProxySBC` + `ProxySBC -->\|"TCP 5060/5061"\| OtherProxy` |
| `DownstreamLBO <-->\|"UDP 5060"\| ProxySBC` | `DownstreamLBO -->\|"UDP 5060"\| ProxySBC` + `ProxySBC -->\|"UDP 5060"\| DownstreamLBO` |
| `IPPhones <-->\|"UDP 5060-5069"\| DownstreamSBC` | `IPPhones -->\|"UDP 5060-5069"\| DownstreamSBC` + `DownstreamSBC -->\|"UDP 5060-5069"\| IPPhones` |
| `IPPhones <-->\|"UDP 5060-5069"\| DownstreamLBO` | `IPPhones -->\|"UDP 5060-5069"\| DownstreamLBO` + `DownstreamLBO -->\|"UDP 5060-5069"\| IPPhones` |

---

### 8. D.3 Media (RTP/SRTP) Flows (was line ~3403)

**Fix type:** Replace `<-->`

**Replaced 2 bidirectional arrows:**

| Before | After |
|--------|-------|
| `M365 <-->\|"SRTP"\| TEAMS` | `M365 -->\|"SRTP"\| TEAMS` + `TEAMS -->\|"SRTP"\| M365` |
| `M365 <-->\|"SRTP"\| TEAMS_LMO` | `M365 -->\|"SRTP"\| TEAMS_LMO` + `TEAMS_LMO -->\|"SRTP"\| M365` |

---

### 9. D.4 Management & Monitoring Flows (was line ~3490)

**Fix type:** Replace `<-->`

**Replaced 3 bidirectional arrows:**

| Before | After |
|--------|-------|
| `OVOC <-->\|"Device Mgmt<br/>TCP 443"\| SBCs` | `OVOC -->\|"Device Mgmt<br/>TCP 443"\| SBCs` + `SBCs -->\|"Device Mgmt<br/>TCP 443"\| OVOC` |
| `ARMConfig <-->\|"HTTPS<br/>TCP 443"\| SBCs` | `ARMConfig -->\|"HTTPS<br/>TCP 443"\| SBCs` + `SBCs -->\|"HTTPS<br/>TCP 443"\| ARMConfig` |
| `ARMRouter <-->\|"HTTPS<br/>TCP 443"\| SBCs` | `ARMRouter -->\|"HTTPS<br/>TCP 443"\| SBCs` + `SBCs -->\|"HTTPS<br/>TCP 443"\| ARMRouter` |

---

## Diagrams Inspected but Not Changed (No Issues Found)

| Diagram | Location | Reason |
|---------|----------|--------|
| 8-Phase Deployment Sequence | was line ~2282 | No `<-->`, no frontmatter, no HTML tags |
| D.5 Call Flow Example 1 | was line ~3580 | sequenceDiagram -- uses `->>` syntax, no issues |
| D.5 Call Flow Example 2 | was line ~3608 | sequenceDiagram -- uses `->>` syntax, no issues |

---

## Verification

After all edits, confirmed:
- Zero `<-->` instances remain in lines 2000-3600
- Zero `---`/`title:` frontmatter blocks remain inside mermaid fences in lines 2000-3600
- Zero `<b>`/`<i>` HTML tags found in mermaid blocks within lines 2000-3600
- All remaining `<-->` instances (7 total) are on lines 3970+ (outside this range)
- All remaining `title:` frontmatter blocks (2 total) are on lines 3984+ (outside this range)
