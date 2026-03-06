# AudioCodes SBC Deployment Options - Decision Pack

| Field | Detail |
|-------|--------|
| **Date** | 6 March 2026 |
| **Audience** | IT Manager, Cybersecurity, Cloud Platform, Voice Engineering |
| **Source** | AudioCodes SBC - Unified Deployment & Configuration Guide v2.6; AudioCodes Mediant VE Installation Manual (LTRT-11011) |
| **Purpose** | Present six SBC deployment options with technical background and recommendation |

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

## 1A. Technical Background - HA Mechanisms and NLB

This section explains why the on-premises HA mechanism cannot be replicated in AWS, how AWS HA works differently across single-AZ and multi-AZ deployments, and why the AWS Network Load Balancer (NLB) option was evaluated and not recommended.

### Why On-Premises HA (VMware/Hyper-V) Cannot Work in AWS

On-premises AudioCodes Mediant VE deployments on VMware, Hyper-V, or KVM use a mechanism similar to physical hardware appliance HA:

- Virtual NICs are connected to a **Layer 2 vSwitch**. When HA switchover is triggered, the newly active SBC sends a **Gratuitous ARP (GARP)** to advertise the IP's new location on the network.
- The standby VM only listens and does not respond to packets except on the dedicated HA interface.
- The HA interface is a **dedicated, separate L2 network** used exclusively for heartbeat and state synchronisation.

**AWS does not support this mechanism.** There is no Layer 2 adjacency between EC2 instances - even within the same Availability Zone. AWS networking does not support multicast or Gratuitous ARP. IP addresses are managed by the AWS control plane, not by the guest operating system's network stack. These are fundamentally two non-comparable infrastructure models (confirmed by AudioCodes).

### How AWS HA Works Instead

AudioCodes engineered a cloud-native failover mechanism for AWS that replaces GARP with AWS API calls. The mechanism differs depending on whether the deployment spans one or two Availability Zones:

| | Single-AZ HA | Multi-AZ HA |
|---|---|---|
| **SBC placement** | Both SBCs in same AZ, same subnet | SBCs in different AZs, different subnets |
| **Internal failover** | Secondary private IPs moved between ENIs (`ec2:AssignPrivateIpAddresses` / `ec2:UnassignPrivateIpAddresses`) | VIP route table entry repointed to standby ENI (`ec2:ReplaceRoute`) |
| **Why different** | Same subnet - IPs can move directly between ENIs | Different subnets per AZ - IPs cannot move; Virtual IP + route table required |
| **External failover** | EIP moved to standby WAN ENI (`ec2:AssociateAddress`) | Same |
| **IAM scoping (internal)** | Scopeable to specific ENI ARNs | Scopeable to route table ARN only (not to individual routes) |
| **IAM scoping (external)** | Scopeable to specific EIP ARN + tags | Same |
| **Virtual IP required** | No | Yes |
| **Stack Manager required** | No - CloudFormation deployment | Yes - mandatory for multi-AZ HA |
| **AZ failure protection** | No - both SBCs lost if AZ fails | Yes - survives single AZ failure |

> **Notes:**
> - The cybersecurity concern (`ec2:ReplaceRoute` cannot be scoped to individual route entries) applies **only to multi-AZ HA**. Single-AZ HA does not use `ec2:ReplaceRoute` at all.
> - Both deployment models use `ec2:AssociateAddress` for external EIP failover - this is already approved and scoped to a specific EIP ARN with dual tag conditions.
> - In single-AZ, the internal "floating" IP is a secondary private IP on the ENI. AWS allows secondary IPs to be dynamically assigned and unassigned between ENIs in the same subnet. The SBC firmware calls the EC2 API to move these during switchover.
> - In multi-AZ, the SBCs sit in different subnets (one per AZ), so a secondary IP cannot simply move. Instead, a Virtual IP is created outside both subnets and a route table entry directs traffic to the active SBC's ENI. This is the route entry that `ec2:ReplaceRoute` modifies.

### NLB (Network Load Balancer) - Evaluated and Not Recommended

The AudioCodes Mediant VE Installation Manual (Section 2.3.2, Document LTRT-11011) documents an alternative to the Virtual IP mechanism for multi-AZ HA: placing an AWS Network Load Balancer in front of the SBC pair on the internal (LAN) side.

**How NLB would work:**
- NLB sits between internal peers and the SBC pair, replacing the Virtual IP
- NLB health checks detect which SBC is active and route traffic accordingly
- Eliminates `ec2:ReplaceRoute` for the internal path
- EIP failover (`ec2:AssociateAddress`) is still required for external/Teams connectivity
- AudioCodes recommends: "consider the option of using AWS NLB instead of Virtual IP addresses only, while keeping Elastic IPs for communication over the public IP addresses"

**Why NLB is not recommended for this deployment:**

1. **NLB is applicable to multi-AZ HA only** - it is not used in single-AZ deployments (confirmed by AudioCodes).
2. **Mandates DNS for all communicating equipment.** All devices connecting to the SBC via NLB must be configured to use the NLB DNS Name/FQDN - not an IP address. The SBC must set the "Local Hostname" parameter on each IP Group to the NLB FQDN, which is added to the SIP Contact header. Failure to do this prevents SIP sessions from maintaining connection after HA switchover.
3. **Not all SIP peers support DNS.** The deployment includes third-party devices (Zenitel PBX intercom system with approximately 12 endpoints, Cisco analog voice gateways) that may not support DNS-based SIP trunk configuration. Basic SIP intercom systems in particular often only support static IP addresses for SIP proxy/registrar.
4. **Restricts interworking flexibility.** Mandating DNS-based SIP connectivity constrains the Proxy SBC's ability to interwork with any SIP server or device. AudioCodes' deployment recommendation is to not restrict the SBC to DNS-only connectivity.
5. **Adds operational dependency.** DNS resolution introduces an additional point of failure in the real-time voice signalling path.
6. **Does not eliminate all IAM concerns.** NLB replaces the VIP (eliminating `ec2:ReplaceRoute`) but `ec2:AssociateAddress` is still required for external EIP failover.

> **Notes:**
> - Cisco IOS-XE voice gateways (VG series) fully support DNS for SIP configuration and would be NLB-compatible.
> - Zenitel PBX intercom systems are model-dependent - many basic SIP intercom implementations only support static IP addresses for SIP proxy configuration.
> - The decision to not recommend NLB is a deployment flexibility decision, not a technical impossibility. NLB is a supported AudioCodes option.

---

## 2. The Six Options

### Option 1 - HA with Retrospective Guardrails

| Aspect | Detail |
|--------|--------|
| **Architecture** | 1+1 Active/Standby across two AZs - standard AudioCodes HA via Stack Manager |
| **Failover** | SBC firmware calls AWS APIs directly; VIP + EIP move to standby; active calls survive |
| **IAM permissions** | `ec2:ReplaceRoute` + `ec2:AssociateAddress` - both retained |
| **Security controls** | 4-layer compensating control architecture (see notes) |
| **Exposure window** | ~7-18 seconds from malicious API call to full automated containment |
| **Guardrail cost** | ~$6/month per region |
| **Licensing** | 1x SBC session/feature licence per region (single logical SBC) + 2x base VM licences |
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
> - **TOTAL REBUILD for future HA** - most likely required at project completion. Kapila (AudioCodes) has confirmed that migrating from standalone to HA is a complete tear-down and rebuild. Stack Manager must deploy the HA pair from scratch via CloudFormation - you cannot retrofit HA onto an existing standalone instance.
> - Eliminates Stack Manager component, HA heartbeat subnet, VIP routing infrastructure.
> - Recovery time on failure: minutes to hours depending on failure mode. Could extend up to a day if the MSP needs to familiarise themselves with a complex and non-routine SBC standing-up recovery procedure.
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

### Option 5 - On-Premises Virtualised SBC in HA

| Aspect | Detail |
|--------|--------|
| **Architecture** | AudioCodes Mediant VE (Virtual Edition) deployed on existing on-premises hypervisors in HA |
| **Failover** | Traditional HA - VRRP/native AudioCodes HA on hypervisor; active calls survive |
| **IAM permissions** | N/A - no cloud IAM involved |
| **Security controls** | Existing on-premises security controls, hypervisor access controls, network ACLs |
| **Call survivability** | Active calls survive (session state synchronised) |
| **Licensing** | Mediant VE software licence (session/feature + base VM) |
| **Infrastructure** | 2x VMs on existing hypervisors - no new hardware procurement |

> **Notes:**
> - Same AudioCodes Mediant VE software as the AWS deployment but hosted on existing on-premises hypervisors (VMware, Hyper-V, KVM).
> - **No hardware procurement lead time** - uses existing hypervisor capacity, significantly faster to deploy than Option 4.
> - No new rack space, power, or cooling required - leverages existing data centre infrastructure.
> - Full AudioCodes HA support - same HA mechanism as Option 4 but virtualised.
> - HA failover uses standard networking (VRRP or hypervisor-level IP mobility) - no cloud API dependency.
> - Noted IAM risk not present - no cloud IAM permissions involved in failover.
> - **Against cloud-first strategy** - same strategic trade-off as Option 4, but lower capital cost and faster deployment.
> - Dependent on existing hypervisor capacity and availability in the required data centre locations.
> - Ongoing management within the on-premises virtualisation estate (patching, snapshots, hypervisor lifecycle).

### Option 6 - Single-AZ HA in AWS

| Aspect | Detail |
|--------|--------|
| **Architecture** | 1+1 Active/Standby within a single Availability Zone - AudioCodes HA via CloudFormation |
| **Failover** | SBC firmware moves secondary private IPs + EIP to standby; active calls survive |
| **IAM permissions (internal)** | `ec2:AssignPrivateIpAddresses` + `ec2:UnassignPrivateIpAddresses` - scopeable to specific ENI ARNs |
| **IAM permissions (external)** | `ec2:AssociateAddress` - already approved and scoped to specific EIP ARN + dual tag conditions |
| **Security controls** | No compensating controls required - all IAM permissions are fully scopeable to specific resources |
| **AZ resilience** | **None** - both SBCs in same AZ; AZ failure = total voice outage for region |
| **Call survivability** | Active calls survive (session state synchronised via HA link) |
| **Licensing** | 1x SBC session/feature licence per region (single logical SBC) + 2x base VM licences |
| **Infrastructure** | 2x SBC instances per region; **Stack Manager not mandatory** - CloudFormation deployment (confirmed by AudioCodes) |

> **Notes:**
> - **`ec2:ReplaceRoute` is NOT required** - eliminated entirely. No Virtual IP and no route table manipulation. Internal failover uses secondary private IPs on the same subnet, moved between ENIs via standard EC2 API calls.
> - **`ec2:AssociateAddress` is still required** for external EIP failover (Teams Direct Routing, SIP providers). This permission is already approved - scoped to a specific EIP allocation ARN with dual tag conditions (`App` + `Env`).
> - **IAM permissions are fully scopeable.** `ec2:AssignPrivateIpAddresses` and `ec2:UnassignPrivateIpAddresses` support resource-level IAM scoping to specific ENI ARNs. This is fundamentally different from `ec2:ReplaceRoute` which can only be scoped to the route table level. The cybersecurity concern that prompted this decision pack is fully addressed.
> - **Stack Manager is not mandatory** for single-AZ deployment. The HA pair can be deployed via CloudFormation template directly. This also eliminates the Stack Manager's broad IAM permissions (`ec2:*`, `cloudformation:*`) from the ongoing deployment posture.
> - **Full AudioCodes HA** - same 1+1 Active/Standby with session synchronisation, call survivability, and automatic failover as Option 1. The only difference is the failover mechanism (secondary IP movement vs route table manipulation) and AZ scope.
> - **CRITICAL TRADE-OFF - No AZ failure protection.** Both SBCs reside in the same Availability Zone. If the AZ experiences an outage (infrastructure failure, network partition, power event), both SBCs are lost simultaneously. Voice services fail for the region until the AZ recovers or manual intervention rebuilds in another AZ.
> - **AZ failure context:** AWS AZ failures are infrequent but do occur. Notable AWS AZ-level incidents have historically resulted in hours of degraded service. The business must accept that single-AZ deployment trades AZ-level resilience for a cleaner IAM posture.
> - **Same AZ-level risk profile as Options 4 and 5.** On-premises deployments (physical or virtualised) at a single site have the same exposure to site-level failure. If on-premises single-site HA is considered acceptable, single-AZ HA in AWS carries equivalent risk.
> - **Simpler architecture than Option 1.** No dedicated VIP route table, no VIP subnet, no per-AZ HA subnets, no compensating control stack (EventBridge, Lambda, Config rules), no Stack Manager. Both SBCs share the same subnets.
> - **Peer connectivity unchanged.** Internal peers (downstream SBCs, Zenitel PBX, Cisco VG gateways) continue to connect to the SBC via IP address. No DNS dependency. The secondary IP that moves between ENIs is in the same subnet, so no routing changes are needed - ARP resolution handles the new ENI association at the VPC level.

---

## 3. Comparison Matrix

| Category | Option 1: Multi-AZ HA + Guardrails | Option 2: Standalone | Option 3: 2x Standalone | Option 4: On-Prem Physical | Option 5: On-Prem Virtualised | Option 6: Single-AZ HA |
|----------|--------------------------|---------------------|------------------------|----------------------|-------------------------------|------------------------|
| **HA capability** | Full 1+1 Active/Standby | None | External failover (DNS/SIP) | Full HA (VRRP/native) | Full HA (VRRP/native) | Full 1+1 Active/Standby |
| **Call survivability** | Active calls survive | All calls drop | Active calls drop | Active calls survive | Active calls survive | Active calls survive |
| **Recovery time** | Seconds (automatic) | Minutes-hours, potentially up to a day (manual - see notes) | Seconds-minutes (DNS/SIP) | Seconds (automatic) | Seconds (automatic) | Seconds (automatic) |
| **AZ failure protection** | Yes - survives single AZ failure | No - single instance | No - both independent | N/A (on-prem site risk) | N/A (on-prem site risk) | **No - both SBCs in same AZ** |
| **Security risk** | 7-18s window, 4-layer defence | Noted IAM risk not present | Noted IAM risk not present | Noted IAM risk not present | Noted IAM risk not present | Noted IAM risk not present (all permissions scopeable) |
| **Build effort** | Moderate-high | Low (fastest) | Moderate | Variable (hardware) | Moderate - uses existing infra | Moderate - simpler than Option 1 |
| **Licensing** | 1x session/feature + 2x base VM + ~$6/mo | 1x SBC/region | 2x full SBC/region | Appliance licence | VE software licence | 1x session/feature + 2x base VM |
| **Future flexibility** | Already at target state | **Total rebuild for HA** (most likely at project completion) | Already HA - no concerns | Locked to on-premises | Locked to on-premises | Can migrate to multi-AZ later (rebuild required) |
| **Vendor support** | AudioCodes-supported HA | Standard support | Custom pattern (not HA support) | Hardware support | AudioCodes-supported HA | AudioCodes-supported HA |
| **Cyber approval** | Depends on risk appetite | High likelihood | High likelihood | High likelihood | High likelihood | High likelihood |
| **Cloud-first aligned** | Yes | Yes | Yes | No | No | Yes |
| **Stack Manager** | Required (mandatory for multi-AZ) | Not required | Not required | N/A | N/A | Not required (CloudFormation) |
| **Timeline to deploy** | Moderate - HA build + guardrail stack | Fastest - simplest architecture | Moderate - 2x SBC config + provider coordination | Slowest - hardware procurement + data centre logistics | Moderate-fast - existing hypervisors | Moderate - simpler than Option 1 (no guardrail stack, no Stack Manager) |

> **Notes - Business Continuity:**
> - Voice is a critical business service - outages impact external customer communication, internal collaboration, emergency calling, and regulatory compliance.
> - Options 1, 4, 5, and 6 provide seamless failover with call survivability. Options 2 and 3 do not.
> - Option 2 recovery depends on failure mode: instance reboot (minutes), replacement (potentially hours). Recovery time could extend up to a day if the MSP needs to familiarise themselves with a complex and non-routine SBC standing-up procedure.
> - Option 3 failover speed depends on DNS TTL (often 60-300s) or SIP retry behaviour.
> - **Option 6 AZ failure risk:** While Option 6 provides full HA against instance failure, it does not protect against AZ-level failure. An AZ outage takes both SBCs offline simultaneously. Recovery requires waiting for the AZ to recover or manual rebuild in another AZ - potentially hours. This is the same site-level risk as Options 4 and 5.
>
> **Notes - Cost:**
> - Specific SBC licensing costs should be confirmed with AudioCodes.
> - Option 1 includes Stack Manager (1x t3.medium per environment) + guardrail infrastructure (~$6/month per region).
> - Option 6 does not require Stack Manager or guardrail infrastructure - lower ongoing cost than Option 1.
> - Option 4 includes data centre costs (rack space, power, cooling).
> - Option 5 leverages existing hypervisor capacity - no new hardware costs, only VE software licensing.
> - EC2 instance costs depend on selected instance type and region.
>
> **Notes - Future Flexibility (critical for Options 2 and 6):**
> - Choosing standalone now and needing HA later = total rebuild (Kapila confirmed). Stack Manager must deploy from scratch via CloudFormation.
> - Option 3 is already HA - the HA mechanism used does not programmatically manipulate the AWS route table, so there are no concerns with this approach.
> - Option 1 is already at target HA state - guardrails can be removed if Cyber changes position.
> - **Option 6 to multi-AZ migration:** Moving from single-AZ to multi-AZ HA would require a rebuild, as the failover mechanism changes from secondary IP movement to VIP route table manipulation, and Stack Manager becomes mandatory. This is the same class of rebuild as standalone-to-HA but with the advantage that HA concepts and configuration are already in place.
> - Options 4 and 5 lock voice infrastructure to on-premises - require migration project to move to cloud later.

---

## 4. Recommendation

### Primary: Option 1 - Multi-AZ HA with Retrospective Guardrails

Option 1 remains the recommended path. It delivers the target-state HA architecture from day one with maximum resilience - protecting against both instance failure and AZ-level failure. The 7-18 second exposure window is bounded by a 4-layer automated defence that reverts, revokes, quarantines, and alerts without human intervention. The guardrail infrastructure costs ~$6/month per region.

**Why Option 1 over Option 6:** Both options deliver full AudioCodes HA with call survivability. The difference is resilience scope. Option 1 protects against AZ-level failure (infrastructure outage, network partition, power event affecting an entire Availability Zone). Option 6 does not. AWS AZ failures are infrequent but have historically resulted in hours of degraded service when they occur. For a critical voice service, the additional protection of multi-AZ deployment is worth the trade-off of accepting the `ec2:ReplaceRoute` permission with compensating controls.

**Why Option 1 over NLB:** The NLB alternative was evaluated (see Section 1A) and not recommended. NLB mandates DNS-based SIP connectivity for all communicating equipment, which restricts the Proxy SBC's interworking flexibility and creates compatibility concerns with devices such as the Zenitel PBX intercom system. The deployment should not be constrained by a DNS dependency in the real-time voice signalling path. NLB also does not eliminate all IAM concerns - `ec2:AssociateAddress` is still required for external EIP failover.

### Cloud-First Fallback: Option 6 - Single-AZ HA in AWS

If cybersecurity determines that the compensating controls in Option 1 are insufficient and `ec2:ReplaceRoute` must be eliminated entirely while remaining cloud-first, Option 6 is the recommended fallback. It delivers full AudioCodes HA with call survivability, eliminates `ec2:ReplaceRoute` entirely, and all remaining IAM permissions are fully scopeable to specific resource ARNs. It also eliminates the Stack Manager and its associated broad IAM permissions. The architecture is simpler and lower cost than Option 1.

**The trade-off is AZ resilience.** Both SBCs reside in the same Availability Zone. An AZ-level failure takes both SBCs offline simultaneously. The business must accept this risk. However, this is the same site-level risk profile as Options 4 and 5 (on-premises single-site deployment). If on-premises HA at a single site is considered acceptable, single-AZ HA in AWS carries equivalent risk.

### On-Premises Fallback: Option 5 - On-Premises Virtualised HA

If the organisation is willing to step outside cloud-first strategy, Option 5 delivers all desired functionality - full HA, call survivability, and the noted IAM risk is simply not present - using AudioCodes Mediant VE on existing on-premises hypervisors. No hardware procurement is required, making it significantly faster to deploy than Option 4. The trade-off is strategic: voice infrastructure moves back on-premises.

### Alternative On-Premises Fallback: Option 4 - On-Premises Physical HA

If existing hypervisor capacity is not available or not suitable, Option 4 achieves the same outcome as Option 5 using a physical AudioCodes Mediant appliance. The trade-off is hardware procurement lead time and data centre logistics, making it the slowest option to deploy.

### Also Worth Considering: Option 3 - 2x Standalone SBCs

Option 3 removes all route table and EIP IAM permissions while still providing resilience through DNS/SIP-based failover. Active calls will drop on primary failure, but new calls route to the secondary within seconds to minutes. The HA mechanism does not manipulate the AWS route table, so the noted IAM risk is not present. However, running two independent SBCs introduces configuration drift risk - each instance maintains its own configuration independently, and keeping them in sync is an ongoing operational burden.

### Not Recommended: Option 2 - Standalone (No HA)

Option 2 is not recommended. While it is the fastest to deploy and eliminates the IAM concern, it introduces a single point of failure for voice services and - critically - requires a **total rebuild** to add HA later (confirmed by AudioCodes), most likely at project completion. Recovery time on failure could extend up to a day if the MSP needs to work through an unfamiliar SBC recovery procedure. This creates a significant risk of painting the organisation into a corner.

---

## 5. Decision Framework and Next Steps

### Factors to Score

| # | Factor | Key Question |
|---|--------|-------------|
| 1 | **Risk appetite** | Is a 7-18s exposure window with automated containment acceptable, or must `ReplaceRoute` be eliminated entirely? |
| 2 | **AZ resilience** | Is single-AZ acceptable (Option 6), or must the deployment survive an AZ failure (Option 1)? |
| 3 | **Voice criticality** | What is the acceptable RTO for voice services? Is a single point of failure tolerable? |
| 4 | **Cloud-first commitment** | Does cloud-first strategy preclude an on-premises SBC? |
| 5 | **Build vs. rebuild** | Is the risk of a total rebuild later (Option 2) acceptable given timeline pressures? |
| 6 | **Cyber's position** | What is the formal position on compensating controls (Option 1)? |
| 7 | **Timeline pressure** | How urgently must Direct Routing be in production? |
| 8 | **Licensing budget** | Is double SBC licensing (Options 1 & 3) within budget? |

### Open Questions for the Decision Meeting

| # | Question | Owner |
|---|----------|-------|
| 1 | What is the formal position on the 7-18s exposure window with 4-layer automated containment? | Cybersecurity |
| 2 | Is the compensating control architecture sufficient to close the finding? | Cybersecurity |
| 3 | If Option 1 is rejected, is the position permanent or reviewable after non-prod demonstration? | Cybersecurity |
| 4 | Does cybersecurity have any concerns with `ec2:AssignPrivateIpAddresses` / `ec2:UnassignPrivateIpAddresses` scoped to specific ENI ARNs (Option 6)? | Cybersecurity |
| 5 | What is the acceptable RTO for voice services? | IT Management |
| 6 | Is single-AZ deployment acceptable for voice services, given that an AZ failure would cause total regional voice outage? | IT Management |
| 7 | Is the total rebuild risk (Option 2 to HA) acceptable? | IT Management |
| 8 | Does cloud-first strategy rule out Options 4 and 5? | IT Management |
| 9 | What is the estimated effort to build the guardrail stack (Option 1)? | Cloud Platform / TTO |
| 10 | Can the guardrail stack be built and tested in non-prod before a final decision? | Cloud Platform / TTO |
| 11 | Can regional SIP providers support primary/secondary SBC configuration (Option 3)? | Voice Engineering |
| 12 | Is there sufficient hypervisor capacity on-premises for Option 5? | Infrastructure / Voice Engineering |
| 13 | What is the hardware lead time for a physical AudioCodes appliance (Option 4)? | Voice Engineering |
| 14 | What is the target date for Microsoft Teams Direct Routing go-live? | All stakeholders |
| 15 | Is this decision per-region or must it be consistent across all regions? | All stakeholders |

### References

| Document | Relevance |
|----------|-----------|
| Cybersecurity Analyst Review - ReplaceRoute Finding | Full finding detail, containment architecture, architecture diagrams, cost breakdown |
| Cybersecurity Analyst Review - ReplaceRoute Containment Architecture Appendix | EventBridge + Lambda design, validation logic, exposure window analysis |
| AudioCodes Deployment Guide v2.6 - Section 19 (HA) | HA failover mechanism, call survivability, VIP/EIP behaviour |
| AudioCodes Deployment Guide v2.6 - Section 20 (IAM) | SBC IAM policy, ReplaceRoute and AssociateAddress scoping |
| AudioCodes Mediant VE Installation Manual (LTRT-11011) - Section 2.3.2 | NLB deployment option, DNS requirements, Local Hostname configuration |
| AWS IAM Service Authorisation Reference | Confirms no condition keys for destination CIDR or target ENI on `ReplaceRoute` |
| Cross-Cutting Findings - IAM Privilege | Broader IAM privilege concerns including Stack Manager |

---

*Generated 5 March 2026 - updated 6 March 2026 with technical background (Section 1A), Option 6, and NLB analysis*
