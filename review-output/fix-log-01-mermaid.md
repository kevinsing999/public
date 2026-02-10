# Fix Log: Mermaid Diagram Corrections

**Date:** 2026-02-10
**File:** `/home/kevin/public/AudioCodes-AWS-Deployment-Guide.md`
**Review source:** `/home/kevin/public/review-output/01-mermaid-diagrams.md`

---

## Changes Applied

### Fix 1: D.1 High-Level Architecture Overview (line 3284)
- **Reversed arrow directions** on lines 3316-3319: changed `ProxySBC --> StackMgr/ARMConfig/ARMRouter/OVOC` to `StackMgr/ARMConfig/ARMRouter/OVOC --> ProxySBC` so management components correctly point TO the SBC they manage.
- **Corrected Stack Manager label** from `"- HA Failover / - Route Table Updates"` to `"- Initial Deployment / - Day 2 Operations"` to reflect the Stack Manager's actual role (it does not participate in active HA failover).
- **Fixed Microsoft 365 login URL** from `login.microsoft.com` to `login.microsoftonline.com`.

### Fix 2: D.2 SIP Signaling Flow Diagram (line 3335)
- **Removed orphaned nodes** `ProxySBC2` and `ProxySBC3` which created duplicate "Proxy SBC" boxes disconnected from the main proxy subgraph.
- **Removed disconnected subgraph fragments** (`downstream`, `endpoints`, `downstreamLBO`, `localPSTN`) that were floating separately.
- **Consolidated into a single coherent diagram** with downstream SBC types nested inside the `internal` subgraph, and all connections routed through the single `ProxySBC` node.

### Fix 3: Non-Production Architecture Diagram (line 170)
- **Changed Stack Manager label** from `"Manages HA failover"` to `"HA Deployment & Day 2 Ops"` on the `SM_NP` node.

### Fix 4: Production Architecture Diagram (line 206)
- **Changed Stack Manager label** from `"Manages HA failover"` to `"HA Deployment & Day 2 Ops"` on the `SM_AUS` node.

### Fix 5: D.5 Call Flow Example 1 -- Teams User to PSTN (line 3570)
- **Replaced invalid `<-->` bidirectional arrows** with paired unidirectional `->>` arrows in the Media Flow section. Changed 3 bidirectional lines to 6 unidirectional lines (`TU->>PS`, `PS->>TU`, `PS->>PP`, `PP->>PS`, `PP->>PU`, `PU->>PP`).

### Fix 6: D.5 Call Flow Example 2 -- PSTN to Downstream SBC Endpoint (line 3595)
- **Replaced invalid `<-->` bidirectional arrows** with paired unidirectional `->>` arrows in the Media Flow section. Changed 3 bidirectional lines to 6 unidirectional lines (`PU->>PS`, `PS->>PU`, `PS->>DS`, `DS->>PS`, `DS->>SE`, `SE->>DS`).

---

## Summary

6 fixes applied across 4 mermaid diagrams. All changes align with the corrected code provided in the review file. The Stack Manager label corrections (Fixes 1, 3, 4) bring the diagrams into agreement with the document body, which states that the Stack Manager does not participate in active HA failover.
