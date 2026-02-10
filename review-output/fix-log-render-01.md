# Fix Log: Mermaid Rendering Issues (Lines 1-2000)

**File:** `/home/kevin/public/AudioCodes-AWS-Deployment-Guide.md`
**Date:** 2026-02-10
**Scope:** Lines 1-2000 (Diagrams 1-5 from render-issues.md)

---

## Diagrams Modified

### Diagram 1: HA Failover Mechanism (originally line ~97)

**Fix 1a - Removed `<b>` HTML tags from node labels:**
- **Line 101 (original):** `SBC_Active["<b>Mediant VE SBC (Active)</b><br/>ENI: 10.0.1.x<br/><br/>Calls AWS API on failover"]`
- **Changed to:** `SBC_Active["Mediant VE SBC (Active)<br/>ENI: 10.0.1.x<br/><br/>Calls AWS API on failover"]`
- **Reason:** `<b>` and `</b>` HTML tags may not render correctly in GitHub's Mermaid renderer.

**Fix 1b - Removed `<b>` HTML tags from node labels:**
- **Line 105 (original):** `SBC_Standby["<b>Mediant VE SBC (Standby)</b><br/>ENI: 10.0.2.x<br/><br/>Calls AWS API on failover"]`
- **Changed to:** `SBC_Standby["Mediant VE SBC (Standby)<br/>ENI: 10.0.2.x<br/><br/>Calls AWS API on failover"]`
- **Reason:** Same as Fix 1a.

**Fix 1c - Replaced `<-->` bidirectional arrow:**
- **Line 108 (original):** `SBC_Active <-->|"HA Subnet"| SBC_Standby`
- **Changed to:**
  ```
  SBC_Active -->|"HA Subnet"| SBC_Standby
  SBC_Standby -->|"HA Subnet"| SBC_Active
  ```
- **Reason:** GitHub uses Mermaid v9 which does not support `<-->`. Replaced with two unidirectional arrows.

---

### Diagram 2: Non-Production Environment Architecture (originally line ~170)

**Fix 2a - Replaced `<-->` bidirectional arrow:**
- **Line 177 (original):** `SBC1_NP <--> SBC2_NP`
- **Changed to:**
  ```
  SBC1_NP --> SBC2_NP
  SBC2_NP --> SBC1_NP
  ```
- **Reason:** GitHub uses Mermaid v9 which does not support `<-->`. Replaced with two unidirectional arrows.

---

### Diagram 3: Production Environment Architecture (originally line ~206)

**Fix 3a - Replaced `<-->` bidirectional arrow (Australia region):**
- **Line 213 (original):** `SBC1_AUS <--> SBC2_AUS`
- **Changed to:**
  ```
  SBC1_AUS --> SBC2_AUS
  SBC2_AUS --> SBC1_AUS
  ```
- **Reason:** GitHub uses Mermaid v9 which does not support `<-->`. Replaced with two unidirectional arrows.

**Fix 3b - Replaced `<-->` bidirectional arrow (US region):**
- **Line 226 (original):** `SBC1_US <--> SBC2_US`
- **Changed to:**
  ```
  SBC1_US --> SBC2_US
  SBC2_US --> SBC1_US
  ```
- **Reason:** Same as Fix 3a.

---

### Diagram 4: Subnet Design (originally line ~408)

**No changes required.** This diagram uses only standard `-->` and `-.->` arrows. No `<-->`, `<-.->`, `<b>`, `<i>`, or `---`/`title:` frontmatter blocks found.

---

### Diagram 5: Authentication Architecture Overview (originally line ~995)

**Fix 5a - Replaced `<-->` bidirectional arrow (OAuth):**
- **Line 1003 (original):** `proxy <-->|"OAuth"| entra`
- **Changed to:**
  ```
  proxy -->|"OAuth"| entra
  entra -->|"OAuth"| proxy
  ```
- **Reason:** GitHub uses Mermaid v9 which does not support `<-->`. Replaced with two unidirectional arrows.

**Fix 5b - Replaced `<-->` bidirectional arrow (LDAPS):**
- **Line 1012 (original):** `downstream <-->|"LDAPS"| ad`
- **Changed to:**
  ```
  downstream -->|"LDAPS"| ad
  ad -->|"LDAPS"| downstream
  ```
- **Reason:** Same as Fix 5a.

**Fix 5c - Replaced `<-->` bidirectional arrow (Direct Connect):**
- **Line 1015 (original):** `proxy <-->|"Direct Connect"| downstream`
- **Changed to:**
  ```
  proxy -->|"Direct Connect"| downstream
  downstream -->|"Direct Connect"| proxy
  ```
- **Reason:** Same as Fix 5a.

---

## Summary

| Change Type | Count | Diagrams Affected |
|-------------|-------|-------------------|
| `<-->` replaced with two `-->` arrows | 6 instances | Diagrams 1, 2, 3, 5 |
| `<b>`/`</b>` HTML tags removed | 2 nodes (4 tags) | Diagram 1 |
| `---`/`title:` frontmatter removed | 0 | (none in range) |
| `<-.->` replaced | 0 | (none in range) |
| `<i>`/`</i>` HTML tags removed | 0 | (none in range) |
| **Total edits** | **8 changes across 9 lines** | **4 diagrams** |

## Items NOT in Scope (Beyond Line 2000)

The following issues from `render-issues.md` are outside lines 1-2000 and were not addressed:
- Diagrams 7-26 (lines 2282+): contain additional `<-->` arrows, `---`/`title:` frontmatter blocks, `<b>`/`<i>` tags, and `<-.->` arrows
