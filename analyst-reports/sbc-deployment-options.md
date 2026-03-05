# AudioCodes SBC Deployment Options - Decision Pack

| Field | Detail |
|-------|--------|
| **Date** | 5 March 2026 |
| **Classification** | Internal - Restricted |
| **Audience** | IT Manager, Cybersecurity, Cloud Platform, Voice Engineering |
| **Source** | AudioCodes SBC - Unified Deployment & Configuration Guide v2.6 |
| **Purpose** | Present four SBC deployment options with recommendation |

---

## 1. The Problem

A cybersecurity review identified that `ec2:ReplaceRoute` - the AWS API used by AudioCodes SBCs for internal VIP failover - cannot be scoped to individual route entries. The SBC IAM policy is already at **maximum IAM granularity** (specific route table ARN + `Env` tag), but a compromised SBC could still replace *any* route in that table, not just VIP routes.

### Two Failover Paths - Only One Is Affected

| | Internal (VIP) | External (EIP) |
|---|---|---|
| **Failover API** | `ec2:ReplaceRoute` | `ec2:AssociateAddress` |
| **What moves** | Route table entry → standby ENI | EIP → standby WAN ENI |
| **Connects to** | Downstream SBCs, PBX, SIP providers | Microsoft Teams |
| **IAM scoping** | Route table ARN + `Env` tag | EIP ARN + `App` + `Env` tags |
| **Concern** | **Cannot restrict to specific routes** | **No concern** - scoped to single EIP |

> **Notes:**
> - The external EIP path (`ec2:AssociateAddress`) is **not affected** - it is already scoped to a specific EIP allocation ARN with dual tag conditions.
> - Exploiting this requires the **SBC instance to be compromised first** - this is not an internet-facing attack surface.
> - Blast radius is bounded to a single route table in a single tagged environment.
> - Read-only Describe actions have no modification capability.
> - AWS has confirmed there are no condition keys for `destinationCidrBlock` or `networkInterfaceId` on `ReplaceRoute`.

---

## 2. The Four Options

### Option 1 - HA with Retrospective Guardrails

| Aspect | Detail |
|--------|--------|
| **Architecture** | 1+1 Active/Standby across two AZs - standard AudioCodes HA via Stack Manager |
| **Failover** | SBC firmware calls AWS APIs directly; VIP + EIP move to standby; active calls survive |
| **IAM permissions** | `ec2:ReplaceRoute` + `ec2:AssociateAddress` - both retained |
| **Security controls** | 4-layer compensating control architecture (see notes) |
| **Exposure window** | ~7-18 seconds from malicious API call to full automated containment |
| **Guardrail cost** | ~$6/month per region |
| **Licensing** | 2x SBC licence per region |
| **Infrastructure** | 2x SBC instances + 1x Stack Manager (t3.medium) per environment |

> **Notes - Compensating Controls (4 layers):**
> 1. **Dedicated VIP route table** - only VIP routes (`10.x.x.x/32`) live in the table the SBC policy references; blast radius limited to VIP entries only; bound to internal subnet with default route toward east-west firewall.
> 2. **EventBridge + Lambda containment gate** - validates every `ReplaceRoute` call against a strict allowlist (VIP CIDRs, SBC ENI IDs, IAM role ARN, source IP); automatically reverts route, strips IAM instance profile, quarantines instance behind SSH-only SG, raises P1 alert via SNS. Provisioned concurrency eliminates cold starts. Executes in ~2-3 seconds after EventBridge delivery (5-15s).
> 3. **Scheduled canary Lambda** - polls route table every 60 seconds against VIP allowlist; triggers same containment if drift detected; catches delayed EventBridge delivery or console/CLI changes.
> 4. **AWS Config + VPC Flow Logs** - custom Config rule flags non-VIP route entries; Flow Log anomaly detection identifies unexpected traffic patterns.
>
> **Why reactive, not preventive:** AudioCodes firmware calls the EC2 API directly during failover - proprietary behaviour that cannot be intercepted or proxied through Lambda.
>
> **Containment posture:** Deny-by-default, fully automated, no human gate. Justified because a legitimate SBC never modifies non-VIP routes - any violation is definitively malicious or severe misconfiguration. Compromised instance left running in quarantine for forensic investigation.
>
> **Guardrail cost breakdown:** Containment Lambda ~$1, canary Lambda ~$1, provisioned concurrency ~$3, CloudWatch logs ~$1, EventBridge/SSM/SNS/SG = free tier.

### Option 2 - Standalone SBC (No HA)

| Aspect | Detail |
|--------|--------|
| **Architecture** | Single SBC instance per region - no HA pairing, no VIP, no route table manipulation |
| **Failover** | None - manual recovery (instance restart/replacement) |
| **IAM permissions** | `ec2:ReplaceRoute` **removed entirely**; `ec2:AssociateAddress` not required |
| **Security controls** | N/A - no IAM risk to mitigate |
| **Single point of failure** | Yes - SBC failure = total voice outage for region |
| **Licensing** | 1x SBC licence per region |
| **Infrastructure** | 1x SBC instance per region; no Stack Manager required |

> **Notes:**
> - **Fastest path to production** - simplest architecture, no HA infrastructure to build.
> - **TOTAL REBUILD for future HA.** Kapila (AudioCodes) has confirmed that migrating from standalone to HA is a complete tear-down and rebuild. Stack Manager must deploy the HA pair from scratch via CloudFormation - you cannot retrofit HA onto an existing standalone instance.
> - Eliminates Stack Manager component, HA heartbeat subnet, VIP routing infrastructure.
> - Recovery time on failure: minutes to hours depending on failure mode.
> - All active calls drop on instance failure.

### Option 3 - Non-Seamless HA (2x Standalone SBCs)

| Aspect | Detail |
|--------|--------|
| **Architecture** | Two independent SBC instances per region - not an AudioCodes HA pair |
| **Failover** | External: DNS-based, SIP proxy primary/secondary, or Teams DR priority/weight settings |
| **IAM permissions** | `ec2:ReplaceRoute` **removed entirely**; `ec2:AssociateAddress` **removed entirely** |
| **Security controls** | N/A - no IAM risk to mitigate |
| **Call survivability** | Active calls on primary **drop** - no session state synchronisation |
| **Licensing** | 2x SBC licence per region (double cost) |
| **Infrastructure** | 2x SBC instances per region; no Stack Manager required |

> **Notes:**
> - Eliminates all route table and EIP IAM permissions - zero cloud API failover risk.
> - Failover speed depends on DNS TTL or SIP retry timers - not seamless like true HA.
> - Each SBC maintains independent configuration - risk of configuration drift between primary and secondary.
> - Not an AudioCodes-supported HA pattern - this is a custom resilience design.
> - No rebuild risk - can add a third SBC or convert one into an HA pair later without tearing down existing instances.
> - Requires SIP provider and Microsoft coordination for primary/secondary configuration.

### Option 4 - On-Premises SBC in HA

| Aspect | Detail |
|--------|--------|
| **Architecture** | Physical AudioCodes Mediant appliance (800/1000/2600) with VRRP or native HA |
| **Failover** | Traditional HA - VRRP/AudioCodes native; active calls survive |
| **IAM permissions** | N/A - no cloud IAM involved |
| **Security controls** | Physical security, network ACLs - shifts to physical access domain |
| **Call survivability** | Active calls survive (session state synchronised) |
| **Licensing** | Hardware appliance licence |
| **Infrastructure** | Physical appliance + rack space + power + cooling |

> **Notes:**
> - Proven HA mechanism with no cloud API dependency.
> - **Against cloud-first strategy** - moves voice infrastructure back on-premises.
> - Hardware procurement lead time: weeks to months depending on model and availability.
> - Requires physical data centre presence with rack space, power, cooling, and network connectivity.
> - Ongoing hardware maintenance and lifecycle management (patching, warranty, end-of-life).
> - Security concerns shift entirely from IAM/cloud to physical access controls and network segmentation.

---

## 3. Comparison Matrix

| Category | Option 1: HA + Guardrails | Option 2: Standalone | Option 3: 2x Standalone | Option 4: On-Premises |
|----------|--------------------------|---------------------|------------------------|----------------------|
| **HA capability** | Full 1+1 Active/Standby | None | External failover (DNS/SIP) | Full HA (VRRP/native) |
| **Call survivability** | Active calls survive | All calls drop | Active calls drop | Active calls survive |
| **Recovery time** | Seconds (automatic) | Minutes-hours (manual) | Seconds-minutes (DNS/SIP) | Seconds (automatic) |
| **Security risk** | 7-18s window, 4-layer defence | Zero IAM risk | Zero IAM risk | Noted risk not present |
| **Build effort** | Moderate-high | Low (fastest) | Moderate | Variable (hardware) |
| **Licensing** | 2x SBC/region + ~$6/mo | 1x SBC/region | 2x SBC/region | Appliance licence |
| **Future flexibility** | Already at target state | **Total rebuild for HA** | Can convert directly to HA | Locked to on-premises |
| **Vendor support** | AudioCodes-supported HA | Standard support | Custom pattern (not HA support) | Hardware support |
| **Cyber approval** | Depends on risk appetite | High likelihood | High likelihood | High likelihood |
| **Cloud-first aligned** | Yes | Yes | Yes | No |

> **Notes - Business Continuity:**
> - Voice is a critical business service - outages impact external customer communication, internal collaboration, emergency calling, and regulatory compliance.
> - Options 1 and 4 provide seamless failover with call survivability. Options 2 and 3 do not.
> - Option 2 recovery depends on failure mode: instance reboot (minutes), replacement (potentially hours).
> - Option 3 failover speed depends on DNS TTL (often 60-300s) or SIP retry behaviour.
>
> **Notes - Cost:**
> - Specific SBC licensing costs should be confirmed with AudioCodes.
> - Option 1 includes Stack Manager (1x t3.medium per environment) - low additional EC2 cost.
> - Option 4 includes data centre costs (rack space, power, cooling).
> - EC2 instance costs depend on selected instance type and region.
>
> **Notes - Future Flexibility (critical for Option 2):**
> - Choosing standalone now and needing HA later = total rebuild (Kapila confirmed). Stack Manager must deploy from scratch via CloudFormation.
> - Option 3 avoids this trap - can convert directly to HA because there is no programmatic route table manipulation to facilitate heartbeat and failover in the standalone configuration.
> - Option 1 is already at target HA state - guardrails can be removed if Cyber changes position.
> - Option 4 locks voice infrastructure to on-premises - requires migration project to move to cloud later.

---

## 4. Recommendation

### Primary: Option 1 - HA with Retrospective Guardrails

Option 1 is the recommended path. It delivers the target-state HA architecture from day one, avoids any future rebuild risk, and provides seamless failover with call survivability. The 7-18 second exposure window is bounded by a 4-layer automated defence that reverts, revokes, quarantines, and alerts without human intervention. The guardrail infrastructure costs ~$6/month per region.

### Fallback: Option 4 - On-Premises HA

If cybersecurity determines that the compensating controls in Option 1 are insufficient and `ec2:ReplaceRoute` must be eliminated entirely, Option 4 is the recommended fallback. It delivers all of the desired functionality - full HA, call survivability, and the noted IAM risk is simply not present - using a proven physical appliance with traditional VRRP/native HA. The trade-off is strategic: it depends on how important the cloud-first commitment is to the organisation. If cloud-first is a firm direction, Option 4 is off the table. If there is flexibility on that position, it eliminates the concern entirely without compromise on availability or call survivability.

### Also Worth Considering: Option 3 - 2x Standalone SBCs

Option 3 removes all route table and EIP IAM permissions while still providing resilience through DNS/SIP-based failover. Active calls will drop on primary failure, but new calls route to the secondary within seconds to minutes. Option 3 preserves a direct upgrade path to full HA. However, running two independent SBCs introduces configuration drift risk - each instance maintains its own configuration independently, and keeping them in sync is an ongoing operational burden.

### Not Recommended: Option 2 - Standalone (No HA)

Option 2 is not recommended. While it is the fastest to deploy and eliminates the IAM concern, it introduces a single point of failure for voice services and - critically - requires a **total rebuild** to add HA later (confirmed by AudioCodes). This creates a significant risk of painting the organisation into a corner.

---

## 5. Decision Framework and Next Steps

### Factors to Score

| # | Factor | Key Question |
|---|--------|-------------|
| 1 | **Risk appetite** | Is a 7-18s exposure window with automated containment acceptable, or must `ReplaceRoute` be eliminated entirely? |
| 2 | **Voice criticality** | What is the acceptable RTO for voice services? Is a single point of failure tolerable? |
| 3 | **Cloud-first commitment** | Does cloud-first strategy preclude an on-premises SBC? |
| 4 | **Build vs. rebuild** | Is the risk of a total rebuild later (Option 2) acceptable given timeline pressures? |
| 5 | **Cyber's position** | What is the formal position on compensating controls (Option 1)? |
| 6 | **Timeline pressure** | How urgently must Direct Routing be in production? |
| 7 | **Licensing budget** | Is double SBC licensing (Options 1 & 3) within budget? |

### Open Questions for the Decision Meeting

| # | Question | Owner |
|---|----------|-------|
| 1 | What is the formal position on the 7-18s exposure window with 4-layer automated containment? | Cybersecurity |
| 2 | Is the compensating control architecture sufficient to close the finding? | Cybersecurity |
| 3 | If Option 1 is rejected, is the position permanent or reviewable after non-prod demonstration? | Cybersecurity |
| 4 | What is the acceptable RTO for voice services? | IT Management |
| 5 | Is the total rebuild risk (Option 2 → HA) acceptable? | IT Management |
| 6 | Does cloud-first strategy rule out Option 4? | IT Management |
| 7 | What is the estimated effort to build the guardrail stack (Option 1)? | Cloud Platform / TTO |
| 8 | Can the guardrail stack be built and tested in non-prod before a final decision? | Cloud Platform / TTO |
| 9 | Can regional SIP providers support primary/secondary SBC configuration (Option 3)? | Voice Engineering |
| 10 | What is the hardware lead time for a physical AudioCodes appliance (Option 4)? | Voice Engineering |
| 11 | What is the target date for Microsoft Teams Direct Routing go-live? | All stakeholders |
| 12 | Is this decision per-region or must it be consistent across all regions? | All stakeholders |

### References

| Document | Relevance |
|----------|-----------|
| Cybersecurity Analyst Review - ReplaceRoute Finding | Full finding detail, containment architecture, architecture diagrams, cost breakdown |
| Cybersecurity Analyst Review - ReplaceRoute Containment Architecture Appendix | EventBridge + Lambda design, validation logic, exposure window analysis |
| AudioCodes Deployment Guide v2.6 - Section 19 (HA) | HA failover mechanism, call survivability, VIP/EIP behaviour |
| AudioCodes Deployment Guide v2.6 - Section 20 (IAM) | SBC IAM policy, ReplaceRoute and AssociateAddress scoping |
| AWS IAM Service Authorisation Reference | Confirms no condition keys for destination CIDR or target ENI on `ReplaceRoute` |
| Cross-Cutting Findings - IAM Privilege | Broader IAM privilege concerns including Stack Manager |

---

*Generated 5 March 2026*
