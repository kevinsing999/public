# Fix Log: External Facts (03-external-facts.md)

**Date:** 2026-02-10
**Source file:** `/home/kevin/public/AudioCodes-AWS-Deployment-Guide.md`
**Review file:** `/home/kevin/public/review-output/03-external-facts.md`

---

## Fixes Applied

### 1. GP2 to GP3 for OVOC Storage (Review Issue #1)

Changed all OVOC-related GP2/gp2 references to GP3/gp3. AWS gp3 is now the default EBS volume type, offering 20% lower cost and better baseline performance than gp2.

**Locations changed:**

- **Lines 362-363** (OVOC Specifications table): `500 GB GP2 SSD` -> `500 GB GP3 SSD`, `2 TB GP2 SSD` -> `2 TB GP3 SSD`
- **Line 378** (Compute Requirements Summary table): `AWS EBS: GP2 SSD 2 TB` -> `AWS EBS: GP3 SSD 2 TB`
- **Line 388** (Notes block): `GP2 SSD is recommended as the baseline storage tier` -> `GP3 SSD is recommended as the baseline storage tier`
- **Line 943** (Section 9.4 Compute Requirements table): `AWS EBS: GP2 SSD 2 TB` -> `AWS EBS: GP3 SSD 2 TB`
- **Line 953** (Section 9.4 Notes block): `GP2 SSD is recommended as the baseline storage tier` -> `GP3 SSD is recommended as the baseline storage tier`
- **Lines 3275-3276** (Appendix C Quick Reference table): `500 GiB gp2` -> `500 GiB gp3`, `2 TiB gp2` -> `2 TiB gp3`

Non-OVOC components (Stack Manager, SBC, ARM) already used gp3 in Appendix C and were left unchanged.

**Verification:** Grep for `[Gg][Pp]2` returns zero matches across the entire document.

### 2. Client Authentication EKU Date Corrected (Review Issue #2)

**Line 735:** Changed from:
> `Must include Client Authentication EKU (mandatory from March 2026)`

To:
> `Must include Client Authentication EKU (enforcement timeline evolving -- verify against latest Microsoft Message Center announcements)`

**Rationale:** The March 2026 date conflated two different Microsoft certificate requirements. The exact enforcement timeline for Client Authentication EKU is evolving and depends on multiple factors (Chrome Root Program Policy v1.6, Microsoft's own timeline for root certificate chain requirements). Directing readers to verify against the latest announcements is more accurate.

### 3. DigiCert Global Root G3 Note Added (Review Issue #6)

**Line 1485:** Changed the Purpose column from:
> `Root CA trust anchor for Microsoft SIP certs`

To:
> `Included as a precautionary measure; DigiCert Global Root G2 is the confirmed active root CA for Teams SIP`

**Rationale:** Microsoft transitioned SIP TLS certificates to DigiCert Global Root G2 in October 2023. There is no confirmed use of G3 for Teams SIP certificates. Including G3 is not harmful (defense in depth) but the note clarifies it is precautionary.

### 4. Baltimore CyberTrust Root Expiry Noted (Review Issue #7)

**Line 1486:** Changed the Purpose column from:
> `Legacy root CA (may still be referenced)`

To:
> `Expired May 2025; retain only if required for backward compatibility with older configurations`

**Rationale:** The Baltimore CyberTrust Root certificate expired in May 2025 and Microsoft completed the transition to DigiCert Global Root G2 in October 2023. For a February 2026 document, simply stating "may still be referenced" understates the situation.

### 5. Previous-Generation Instance Notes Added (Review Issues #4 and #5)

**Line 282** (r4.large entry in SBC instance types table): Added parenthetical note to the Notes column:
> `Memory optimized (r4 is previous-generation; consider r5 or r6i for better price-performance)`

**After line 348** (ARM Specifications table): Added a new note block after the table:
> **Note:** m4 is a previous-generation instance family. If AudioCodes AMI compatibility permits, consider m5 or m6i equivalents for better price-performance.

**Rationale:** r4 and m4 are previous-generation AWS instance families. While still functional and potentially required by specific AudioCodes AMI compatibility constraints, readers should be aware of current-generation alternatives.

---

## Review Issues NOT Addressed (Out of Scope for This Fix Pass)

- **Issue #3** (Stack Manager "mandatory for HA failover orchestration" note): Already corrected in a prior fix pass (fix-log-02-stackmgr.md). Both occurrences now read "mandatory for initial HA deployment and Day 2 operations."
- **Issue #8** (OVOC QoE port 5000 vs 5001 inconsistency): Internal consistency issue, not an external fact fix.
- **Issue #9** (RTP media range 6000-65535 too broad): Security hardening recommendation, not an external fact correction.
- **Issue #11** (login.microsoft.com vs login.microsoftonline.com in diagram): Very low severity; functionally equivalent due to redirect.
