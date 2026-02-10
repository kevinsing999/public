# Fix Log: Mermaid Rendering Fixes (Lines 3600-End)

**File:** `/home/kevin/public/AudioCodes-AWS-Deployment-Guide.md`
**Date:** 2026-02-10
**Scope:** Mermaid blocks from line ~3600 to end of file (Diagrams 16-26)

---

## Summary

| Fix Type | Count | Diagrams Affected |
|----------|-------|-------------------|
| `<-->` bidirectional arrow replacements | 7 instances replaced with 14 unidirectional arrows | D.8.4, D.8.7 Layman (x2), D.8.7 Technical (x4) |
| `<-.->` bidirectional dotted arrow replacements | 1 instance replaced with 2 unidirectional dotted arrows | D.8.7 Layman |
| `---`/`title:` frontmatter removal | 2 blocks removed (6 lines total) | D.8.5 ARM Configurator, D.8.5 ARM Router |
| `<b>`/`</b>` HTML tag removal | 22 tags removed (11 labels) | D.8.2 Downstream SBC |
| `<b>`/`</b>` + `<i>`/`</i>` HTML tag removal | 24 tags removed (11 `<b>` labels + 1 `<i>` label) | D.8.3 Downstream SBC with LBO |

**Total: 12 distinct changes across 6 diagrams.**

---

## Diagrams Reviewed (No Changes Needed)

| Diagram | Section | Lines | Result |
|---------|---------|-------|--------|
| Diagram 16 | D.5 Example 1 (sequenceDiagram) | ~3580-3604 | CLEAN - No issues found |
| Diagram 17 | D.5 Example 2 (sequenceDiagram) | ~3608-3629 | CLEAN - No issues found |
| Diagram 18 | D.8.1 Proxy SBC | ~3679-3773 | CLEAN - Uses only standard `-->` and `-.->` arrows |
| Diagram 24 | D.8.6 Stack Manager | ~4090-4134 | CLEAN - Uses only standard `-->` and `-.->` arrows |

---

## Detailed Changes

### 1. D.8.2 Downstream SBC (Diagram 19) - HTML Tag Removal

**Section:** D.8.2 Downstream SBC (On-Premises Mediant 800) - Complete Interface Architecture

Removed `<b>` and `</b>` tags from 11 node labels across all subgraph sections:

- **PhysicalPorts subgraph (4 nodes):**
  - `GE1["<b>GE_1</b> ...]` changed to `GE1["GE_1 ..."]`
  - `GE2["<b>GE_2</b> ...]` changed to `GE2["GE_2 ..."]`
  - `GE3["<b>GE_3</b> ...]` changed to `GE3["GE_3 ..."]`
  - `GE4["<b>GE_4</b> ...]` changed to `GE4["GE_4 ..."]`

- **IPInterfaces subgraph (3 nodes):**
  - `IP0["<b>Index 0: Management</b>...]` changed to `IP0["Index 0: Management..."]`
  - `IP1["<b>Index 1: Internal (LAN)</b>...]` changed to `IP1["Index 1: Internal (LAN)..."]`
  - `IP2["<b>Index 2: HA</b>...]` changed to `IP2["Index 2: HA..."]`

- **MediaRealms subgraph (1 node):**
  - `MR0["<b>Index 0: Internal_Media_Realm</b>...]` changed to `MR0["Index 0: Internal_Media_Realm..."]`

- **SIPInterfaces subgraph (1 node):**
  - `SIP0["<b>Index 0: Internal (LAN)</b>...]` changed to `SIP0["Index 0: Internal (LAN)..."]`

- **IPGroups subgraph (2 nodes):**
  - `IPG1["<b>Proxy SBC Trunk</b>...]` changed to `IPG1["Proxy SBC Trunk..."]`
  - `IPG2["<b>Registered Endpoints</b>...]` changed to `IPG2["Registered Endpoints..."]`

---

### 2. D.8.3 Downstream SBC with LBO (Diagram 20) - HTML Tag Removal

**Section:** D.8.3 Downstream SBC with Local Breakout (LBO) - Complete Interface Architecture

Removed `<b>`, `</b>`, `<i>`, and `</i>` tags from 12 node labels:

- **PhysicalPorts subgraph (4 nodes):**
  - `GE1["<b>GE_1</b> ...]` changed to `GE1["GE_1 ..."]`
  - `GE2["<b>GE_2</b> ...<br/><i>(Also used for PSTN LBO)</i>"]` changed to `GE2["GE_2 ...<br/>(Also used for PSTN LBO)"]`
  - `GE3["<b>GE_3</b> ...]` changed to `GE3["GE_3 ..."]`
  - `GE4["<b>GE_4</b> ...]` changed to `GE4["GE_4 ..."]`

- **MediaRealms subgraph (2 nodes):**
  - `MR0["<b>Index 0: Internal_Media_Realm</b>...]` changed to `MR0["Index 0: Internal_Media_Realm..."]`
  - `MR1["<b>Index 1: PSTN_Media_Realm</b>...]` changed to `MR1["Index 1: PSTN_Media_Realm..."]`

- **SIPInterfaces subgraph (2 nodes):**
  - `SIP0["<b>Index 0: Internal (LAN)</b>...]` changed to `SIP0["Index 0: Internal (LAN)..."]`
  - `SIP1["<b>Index 1: PSTN</b>...]` changed to `SIP1["Index 1: PSTN..."]`

- **IPGroups subgraph (3 nodes):**
  - `IPG1["<b>Proxy SBC Trunk</b>...]` changed to `IPG1["Proxy SBC Trunk..."]`
  - `IPG2["<b>Registered Endpoints</b>...]` changed to `IPG2["Registered Endpoints..."]`
  - `IPG3["<b>PSTN (Telco) Trunk</b>...]` changed to `IPG3["PSTN (Telco) Trunk..."]`

---

### 3. D.8.4 OVOC (Diagram 21) - Bidirectional Arrow Fix

**Section:** D.8.4 OVOC - Interface Architecture

**Before:**
```
Microsoft365(("Microsoft 365")) <-->|TCP 443| GraphIntegration
```

**After:**
```
Microsoft365(("Microsoft 365")) -->|TCP 443| GraphIntegration
GraphIntegration -->|TCP 443| Microsoft365
```

---

### 4. D.8.5 ARM Configurator (Diagram 22) - Frontmatter Removal

**Section:** D.8.5 ARM (AudioCodes Routing Manager) - Interface Architecture (first diagram)

**Removed 3 lines:**
```
---
title: ARM Configurator - Interface Architecture (AWS Instance: m4.xlarge)
---
```

The title is already provided by the markdown heading above the diagram block.

---

### 5. D.8.5 ARM Router (Diagram 23) - Frontmatter Removal

**Section:** D.8.5 ARM (AudioCodes Routing Manager) - Interface Architecture (second diagram)

**Removed 3 lines:**
```
---
title: ARM Router - Interface Architecture (AWS Instance: m4.large, One per Region)
---
```

The title is already provided by the markdown heading above the diagram block.

---

### 6. D.8.7 Layman View (Diagram 25) - Bidirectional Arrow Fixes (3 instances)

**Section:** D.8.7 Complete Solution - End-to-End Connectivity Map (Layman-Friendly View)

**Fix 6a - Teams to WAN:**

Before:
```
Teams <-->|"TLS 5061<br/>Bidirectional"| WAN
```
After:
```
Teams -->|"TLS 5061<br/>Bidirectional"| WAN
WAN -->|"TLS 5061<br/>Bidirectional"| Teams
```

**Fix 6b - LAN to Downstream:**

Before:
```
LAN <-->|"Voice<br/>Traffic"| Downstream
```
After:
```
LAN -->|"Voice<br/>Traffic"| Downstream
Downstream -->|"Voice<br/>Traffic"| LAN
```

**Fix 6c - HA to Backup (bidirectional dotted):**

Before:
```
HA <-.->|"Keep in Sync"| Backup
```
After:
```
HA -.->|"Keep in Sync"| Backup
Backup -.->|"Keep in Sync"| HA
```

---

### 7. D.8.7 Technical View (Diagram 26) - Bidirectional Arrow Fixes (4 instances)

**Section:** D.8.7 Complete Solution - Detailed Technical View

**Fix 7a - Teams to EIP:**

Before:
```
Teams <-->|"TLS 5061<br/>Bidirectional"| EIP
```
After:
```
Teams -->|"TLS 5061<br/>Bidirectional"| EIP
EIP -->|"TLS 5061<br/>Bidirectional"| Teams
```

**Fix 7b - M365 to OVOC:**

Before:
```
M365 <-->|"HTTPS"| OVOC
```
After:
```
M365 -->|"HTTPS"| OVOC
OVOC -->|"HTTPS"| M365
```

**Fix 7c - LANgw to DS:**

Before:
```
LANgw <--> DS
```
After:
```
LANgw --> DS
DS --> LANgw
```

**Fix 7d - A_HA to S_HA:**

Before:
```
A_HA <-->|"Heartbeat<br/>State Sync"| S_HA
```
After:
```
A_HA -->|"Heartbeat<br/>State Sync"| S_HA
S_HA -->|"Heartbeat<br/>State Sync"| A_HA
```

---

## Verification

After all changes:
- Zero `<-->` instances remain in the entire file
- Zero `<-.->` instances remain in the entire file
- Zero `<b>`, `</b>`, `<i>`, `</i>` HTML tags remain in any mermaid block in the file
- Zero `---`/`title:` frontmatter blocks remain inside mermaid code fences in the assigned range
- All remaining `---` occurrences in the file are markdown horizontal rules (section separators), not mermaid frontmatter
