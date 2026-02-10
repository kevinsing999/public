# Fix Log: Stack Manager Role Corrections

**Issue:** Multiple locations in the document incorrectly described the Stack Manager as managing/orchestrating HA failover. Per the document's own Section 2 (lines 91-95), the SBCs themselves handle failover by calling AWS EC2 APIs directly. The Stack Manager is only responsible for initial deployment and Day 2 operations.

**Review references:** 02-technical-consistency.md Issue 3; 04-structure-flow.md C4, W4, W5.

## Changes Made

### 1. Line 383 -- Compute Requirements Notes (Section 4)
- **Before:** "mandatory for HA failover orchestration"
- **After:** "mandatory for initial HA deployment and Day 2 operations"

### 2. Line 948 -- Compute Requirements Notes (Section 9.4, duplicate of Section 4)
- **Before:** "mandatory for HA failover orchestration"
- **After:** "mandatory for initial HA deployment and Day 2 operations"

### 3. Line 409 -- Subnet Design Mermaid Diagram (Section 5)
- **Before:** "Used by Stack Manager for failover routing"
- **After:** "Used by Stack Manager for deployment orchestration"

### 4. Line 854 -- Section 9.3.1 Stack Manager Description
- **Before:** "It deploys SBC stacks via AWS CloudFormation and manages HA failover by programmatically updating VPC route tables to redirect traffic to the newly Active instance."
- **After:** "It deploys SBC stacks via AWS CloudFormation and handles initial HA deployment, topology updates, and Day 2 operations (software upgrades, stack maintenance). During failover, the SBCs themselves update VPC route tables by calling AWS EC2 APIs directly to redirect traffic to the newly Active instance."

### 5. Line 3301 -- D.1 Diagram Stack Manager Label
- **No change needed.** Already shows "Initial Deployment" and "Day 2 Operations" (was previously corrected).

## Items NOT Touched (assigned to another agent)
- Lines 179, 215: Non-Prod/Prod diagram Stack Manager labels
- D.1 diagram arrow directions
