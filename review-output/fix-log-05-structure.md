# Fix Log: Structure, Flow, and Writing Quality Issues

**Source review:** `/home/kevin/public/review-output/04-structure-flow.md`
**Target file:** `/home/kevin/public/AudioCodes-AWS-Deployment-Guide.md`
**Date:** 2026-02-10

---

## Fix 1: revertive-mode description (lines ~900 and ~925)

**Issue (W2):** The parameter table sets `revertive-mode` to "Off", but the description text stated the instance "will automatically resume the Active role" -- that describes revertive=On behaviour, contradicting the configured value.

**Change:** Rewrote the description in both the Proxy SBC HA Configuration table (Section 9.3.2) and the Downstream SBC HA Configuration table (Section 9.3.4) to accurately describe Off behaviour:

- Old: "When the preferred Active instance recovers from a failure, it will automatically resume the Active role after synchronisation with the current Active instance is complete. Setting this to 'Off' means the recovered instance remains in Standby until a manual switchover or subsequent failure event."
- New: "When the preferred Active instance recovers from a failure, it will **not** automatically resume the Active role. Instead, the recovered instance remains in Standby until a manual switchover or subsequent failure event. This prevents unnecessary service disruption caused by repeated role changes."

---

## Fix 2: Missing horizontal rule between Sections 13 and 14

**Issue (S3):** Section 13 (Media Configuration) ended without a `---` horizontal rule before Section 14, inconsistent with every other major section transition.

**Change:** Added `---` separator between the end of Section 13 and the start of Section 14 (SIP Signalling Configuration).

---

## Fix 3: Missing horizontal rule between Sections 14 and 15

**Issue (S4):** Section 14 ended without a `---` separator before Section 15 (Routing Configuration).

**Change:** Added `---` separator between the end of Section 14 and the start of Section 15.

---

## Fix 4: Extra blank line before Section 17

**Issue (F5):** A double blank line appeared between the horizontal rule and the Section 17 heading, inconsistent with all other section transitions.

**Change:** Removed the extra blank line so there is exactly one blank line after the `---` and before `## 17. Break Glass Accounts`.

---

## Fix 5: Spelling standardisation -- British/Australian English

**Issue (W1):** The document mixed British and American English spelling. Given Australian authorship, standardised to British/Australian spelling.

### "signaling" -> "signalling"

Changed all prose/description instances of "signaling" to "signalling" (37 occurrences across headings, body text, and table description cells). Also updated the TOC anchor link from `#14-sip-signaling-configuration` to `#14-sip-signalling-configuration`.

**Preserved unchanged (American spelling retained):**
- Line 795: `-SipSignalingPort` inside a PowerShell code block (parameter name)
- Line 3319: `TLS 5061 (Signaling)` inside a mermaid diagram node label
- Line 3343: `title: SIP Signaling Flow Diagram` inside a mermaid diagram metadata block

### "synchronization" -> "synchronisation"

Changed all three occurrences on the NTP section paragraph (Section 13.1):
- "NTP synchronization" -> "NTP synchronisation"
- "HA synchronization" -> "HA synchronisation"
- "configured to synchronize" -> "configured to synchronise"

### "organization" -> "organisation"

Changed one prose instance:
- Section 10.3: "the organization's password vault" -> "the organisation's password vault"

**Preserved unchanged (American spelling retained):**
- Lines 526, 579, 625, 662, 1039: "Accounts in this organizational directory only" -- Microsoft Entra ID UI text
- Line 1454: "Organization (O)" / "Organization Name" -- CSR certificate field names
- Line 1455: "Organizational Unit (OU)" / "As per organization" -- CSR certificate field values

---

## Fix 6: ARM storage sizes in Appendix C

**Issue (C1 related):** The Appendix C "Instance Type Summary" table showed ARM Configurator as 50 GiB and ARM Router as 20 GiB, but the authoritative compute tables in Sections 4 and 9.4 both state 100 GB and 80 GB respectively.

**Change:** Updated Appendix C to match:
- ARM Configurator: `50 GiB gp3` -> `100 GB gp3`
- ARM Router: `20 GiB gp3` -> `80 GB gp3`

---

## Fix 7: Double hyphen in port range

**Issue (F1):** Line 818 contained `49152--65535` (double hyphen) where a single hyphen was intended for the port range.

**Change:** Corrected to `49152-65535` (single hyphen), consistent with all other port range notation in the document.

---

## Summary

| # | Fix | Category | Lines affected |
|---|-----|----------|---------------|
| 1 | revertive-mode description corrected for Off behaviour | Writing quality (W2) | ~903, ~928 |
| 2 | Added `---` between Sections 13 and 14 | Structure (S3) | ~1588 |
| 3 | Added `---` between Sections 14 and 15 | Structure (S4) | ~1675 |
| 4 | Removed extra blank line before Section 17 | Formatting (F5) | ~2188 |
| 5 | Spelling standardisation (signaling/organization/synchronization) | Writing quality (W1) | ~40 locations |
| 6 | ARM storage sizes corrected in Appendix C | Content accuracy (C1) | ~3277-3278 |
| 7 | Double hyphen in port range fixed | Formatting (F1) | ~821 |
