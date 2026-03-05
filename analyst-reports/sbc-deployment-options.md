# AudioCodes SBC Deployment Options — Decision Pack

## Microsoft Teams Direct Routing — SBC HA Architecture Options

| Field | Detail |
|-------|--------|
| **Date** | 5 March 2026 |
| **Classification** | Internal — Restricted |
| **Audience** | IT Manager, Cybersecurity, Cloud Platform, Voice Engineering |
| **Related Finding** | F-CS-017 — SBC ReplaceRoute IAM Lacks Route-Entry Granularity |
| **Source Document** | AudioCodes SBC — Unified Deployment & Configuration Guide v2.6 |

---

## Purpose and Context

### Why This Decision Pack Exists

Cybersecurity finding **F-CS-017** identified that the AWS IAM permission `ec2:ReplaceRoute` — required by AudioCodes SBCs to perform internal Virtual IP (VIP) failover in a High Availability configuration — cannot be scoped to individual route entries within a route table. AWS IAM exposes no condition keys for destination CIDR or target ENI parameters. The SBC IAM policy is already at **maximum IAM granularity** (specific route table ARN + environment tag condition).

This creates a security concern: a compromised SBC instance could theoretically replace *any* route entry within the permitted route table, not just the VIP routes it legitimately manages.

### What Is Not Affected

The **external EIP failover path** (`ec2:AssociateAddress`) is **not affected** by this finding. It is already tightly scoped to a specific EIP allocation ARN with dual tag conditions (`aws:ResourceTag/App` + `aws:ResourceTag/Env`). A compromised SBC can only reassign that one Elastic IP — not arbitrary addresses.

### Decision Required

Four architectural options exist with different security, availability, and cost trade-offs. This pack presents them objectively for a decision by IT management and cybersecurity.

---

## The Core Security Question

### Two Failover Paths — Only One Is Affected

| | Internal (VIP / ReplaceRoute) | External (EIP / AssociateAddress) |
|---|---|---|
| **IP type** | Private (`10.x.x.x/32`) | Public (Elastic IP) |
| **Failover API** | `ec2:ReplaceRoute` | `ec2:AssociateAddress` |
| **What moves** | VPC route table entry | EIP association |
| **Connects to** | Downstream SBCs, PBX, SIP providers | Microsoft Teams |
| **IAM scoping** | Route table ARN + `Env` tag | EIP allocation ARN + `App` + `Env` tags |
| **Granularity concern** | **Cannot restrict to specific route entries** | Already scoped to specific EIP — **no concern** |

### What the Risk Is

A compromised SBC instance with the `ec2:ReplaceRoute` permission could inject arbitrary routes into the VPC route table, potentially redirecting non-voice traffic through the compromised instance. This could enable man-in-the-middle attacks or denial of service to other workloads sharing the VPC.

### What the Risk Is Not

- This is **not an internet-facing attack surface** — exploiting this requires the SBC instance itself to be compromised first
- The blast radius is bounded to a **single route table** in a **single tagged environment**
- The external (Teams-facing) failover path is **entirely unaffected**
- Read-only Describe actions (`DescribeAddresses`, `DescribeNetworkInterfaces`) have no modification capability

---

## Option 1: HA with Retrospective Guardrails

### 1+1 Active/Standby — Full AudioCodes HA with Compensating Controls

**Architecture:** Standard AudioCodes HA deployment (1+1 Active/Standby across two Availability Zones) with a multi-layered compensating control architecture to address the `ReplaceRoute` granularity gap.

### HA Mechanism

- SBCs deployed in a true HA pair via AudioCodes Stack Manager
- Failover handled by SBC firmware calling AWS APIs directly
- Internal VIP failover via `ec2:ReplaceRoute`
- External EIP failover via `ec2:AssociateAddress`
- Active calls survive failover (session state synchronised between HA pair)

### Compensating Controls (4 Layers)

| Layer | Control | Function |
|-------|---------|----------|
| 1 | **Dedicated VIP route table** | Only VIP routes (`10.x.x.x/32`) in the table the SBC policy references — blast radius limited to VIP entries only |
| 2 | **EventBridge + Lambda containment** | Validates every `ReplaceRoute` call against a strict allowlist; automatically reverts, strips IAM, quarantines instance, and raises P1 alert on any violation |
| 3 | **Scheduled canary Lambda** | Independent 60-second polling of route table state against VIP allowlist — backstop if event-driven path fails |
| 4 | **AWS Config + VPC Flow Logs** | Tertiary detection via custom Config rule on route table changes and Flow Log anomaly detection |

### Exposure Window

- EventBridge delivers CloudTrail management events in **5–15 seconds**
- Lambda with provisioned concurrency executes containment in **~2–3 seconds**
- Total time from malicious API call to full containment: **~7–18 seconds**
- 60-second canary provides independent backstop

### Guardrail Cost

| Component | Monthly Cost |
|-----------|-------------|
| Containment Lambda | ~$1 |
| Canary Lambda | ~$1 |
| Provisioned concurrency (1) | ~$3 |
| CloudWatch Log Group (365-day retention) | ~$1 |
| EventBridge, SSM, SNS, quarantine SG | Free tier |
| **Total** | **~$6/month per region** |

### Key Characteristics

- Seamless failover — active calls survive
- AudioCodes-supported HA configuration
- Requires Stack Manager for initial deployment
- Requires TTO estimate for guardrail implementation
- Internal-facing SBC traffic routed through east-west inspection firewall

---

## Option 2: Standalone SBC (No HA)

### Single SBC Per Region — No High Availability

**Architecture:** A single AudioCodes SBC instance per region with no HA pairing, no Virtual IP, and no route table manipulation.

### What This Eliminates

- `ec2:ReplaceRoute` permission — **removed entirely**
- Stack Manager component — not required for standalone deployment
- HA heartbeat subnet and interface
- VIP routing infrastructure

### What This Introduces

- **Single point of failure** — if the SBC instance fails, all voice services in that region are down
- Recovery requires manual intervention (instance restart, replacement, or failover to alternate region)
- No call survivability — all active calls drop on failure

### Critical Consideration

> **Kapila (AudioCodes) has confirmed that migrating from a standalone SBC to an HA pair is a TOTAL rebuild.** The HA architecture requires the Stack Manager to deploy the SBC pair from scratch via CloudFormation — you cannot retrofit HA onto an existing standalone instance. This means choosing Option 2 now and wanting HA later requires tearing down and rebuilding the entire SBC infrastructure.

### Key Characteristics

- Fastest to deploy — simplest architecture
- Zero IAM risk from `ReplaceRoute`
- Single point of failure per region
- Total rebuild required if HA is needed later
- Lower licensing cost (single SBC licence per region)

---

## Option 3: Non-Seamless HA (2x Standalone SBCs)

### Two Independent SBCs Per Region — No HA Pairing

**Architecture:** Two standalone SBC instances per region operating independently (not an AudioCodes HA pair). Failover is handled externally via DNS or SIP proxy primary/secondary configuration rather than VIP/EIP switching.

### How Failover Works

- SIP provider or downstream systems configured with primary and secondary SBC addresses
- On primary SBC failure, traffic fails over to secondary via:
  - DNS-based failover (TTL-dependent)
  - SIP proxy primary/secondary configuration
  - Microsoft Teams Direct Routing priority/weight settings
- No route table manipulation — each SBC has its own fixed IP addresses

### What This Eliminates

- `ec2:ReplaceRoute` permission — **removed entirely**
- `ec2:AssociateAddress` permission — **removed entirely**
- Stack Manager component — not required
- HA heartbeat subnet and interface
- VIP and EIP failover infrastructure

### What This Introduces

- **Double licensing** — two SBC licences per region
- **Active calls drop on failure** — no session state synchronisation between SBCs
- Failover is **not seamless** — dependent on DNS TTL or SIP retry timers
- Each SBC maintains independent configuration (configuration drift risk)
- No AudioCodes HA support — this is a custom resilience pattern

### Key Characteristics

- Eliminates all route table and EIP IAM permissions
- No rebuild risk — can add a third SBC or convert to HA later without tearing down existing instances
- Double SBC licensing cost per region
- Active calls drop on primary failure
- Failover speed dependent on DNS TTL or SIP retry behaviour

---

## Option 4: On-Premises SBC in HA

### Physical AudioCodes Mediant Appliance — Traditional HA

**Architecture:** Physical AudioCodes Mediant appliance (e.g., Mediant 800/1000/2600) deployed on-premises in a traditional HA configuration using VRRP or proprietary AudioCodes HA mechanisms.

### What This Eliminates

- All AWS IAM concerns — no cloud API permissions required for failover
- Cloud infrastructure complexity — traditional networking with physical interfaces
- Dependency on AWS API availability for HA failover

### What This Introduces

- **Against cloud-first strategy** — moves voice infrastructure back on-premises
- **Hardware procurement lead time** — physical appliance ordering, shipping, rack-and-stack
- **Data centre dependency** — requires physical rack space, power, cooling, network connectivity
- **Physical security domain** — security concerns shift from IAM to physical access controls
- **Direct Connect or VPN required** — must connect back to AWS for Teams integration

### Key Characteristics

- Proven HA mechanism (VRRP/AudioCodes native) — no cloud API dependency
- No cloud IAM security concerns
- Hardware procurement and deployment timeline
- Ongoing hardware maintenance and lifecycle management
- Against organisational cloud-first direction
- Active calls survive failover (traditional HA)
- Requires physical data centre presence

---

## Comparison Matrix

| Category | Option 1: HA + Guardrails | Option 2: Standalone | Option 3: 2x Standalone | Option 4: On-Premises |
|----------|--------------------------|---------------------|------------------------|----------------------|
| **HA Capability** | Full 1+1 Active/Standby | None — single instance | External failover (DNS/SIP) | Full HA (VRRP/native) |
| **Effort to Build** | Moderate + guardrail effort | Low — simplest path | Moderate — 2x config | Variable — hardware lead time |
| **Business Risk (failure impact)** | Low — seamless failover | High — total voice outage on failure | Medium — calls drop, failover not seamless | Low — seamless failover |
| **Security Risk Profile** | Residual: 7–18s exposure window with 4-layer defence | Zero IAM risk | Zero IAM risk | Shifts to physical security domain |
| **Timeline Impact** | Needs TTO estimate for guardrails | Fastest to deploy | Moderate | Variable — hardware procurement |
| **Support & Operations** | AudioCodes-supported HA | Standard AudioCodes support | Custom pattern — not AudioCodes HA support | AudioCodes hardware support |
| **Licensing & Cost** | 2x SBC licence + ~$6/mo guardrails | 1x SBC licence | 2x SBC licence per region | Hardware appliance + SmartTAP |
| **Future Flexibility** | Already at target HA state | Total rebuild for HA | Can convert to HA (rebuild one SBC) | Locked to on-premises |
| **Cyber Approval Likelihood** | Depends on risk appetite | High — no IAM concern | High — no IAM concern | High — no cloud IAM concern |
| **Call Survivability** | Active calls survive | All calls drop | Active calls drop | Active calls survive |

---

## Security Risk Deep Dive

### Option 1: HA with Retrospective Guardrails

| Aspect | Detail |
|--------|--------|
| **IAM risk** | `ec2:ReplaceRoute` scoped to route table level — cannot restrict to specific route entries |
| **Exposure window** | 7–18 seconds from malicious API call to full containment |
| **Defence layers** | 4: dedicated route table, EventBridge+Lambda, canary, Config+Flow Logs |
| **Blast radius** | Limited to VIP routes in dedicated route table |
| **Containment actions** | Automatic: route revert, IAM revocation, SG quarantine, P1 alert |
| **Pre-condition for exploitation** | SBC instance must be compromised first |
| **Residual risk** | Bounded 7–18s window where a compromised SBC could manipulate VIP routes before containment executes |

### Option 2: Standalone SBC

| Aspect | Detail |
|--------|--------|
| **IAM risk** | Zero — `ec2:ReplaceRoute` not granted |
| **Exposure window** | N/A |
| **Defence layers** | N/A |
| **Blast radius** | N/A |
| **Trade-off** | Single point of failure; total rebuild required for future HA |

### Option 3: Non-Seamless HA (2x Standalone)

| Aspect | Detail |
|--------|--------|
| **IAM risk** | Zero — no route table or EIP manipulation |
| **Exposure window** | N/A |
| **Defence layers** | N/A |
| **Blast radius** | N/A |
| **Trade-off** | Double licensing; active calls drop on failure; configuration drift risk |

### Option 4: On-Premises SBC

| Aspect | Detail |
|--------|--------|
| **IAM risk** | Zero — no cloud IAM involved |
| **Exposure window** | N/A |
| **Defence layers** | Physical security controls, network ACLs |
| **Blast radius** | Shifts to physical access domain |
| **Trade-off** | Against cloud-first; hardware lifecycle; data centre dependency |

### Context

All options require the SBC instance (or physical appliance) to be **compromised first** before any route manipulation is possible. The `ReplaceRoute` risk is not an internet-facing attack surface — it exists only in the context of a post-compromise lateral movement scenario from within the SBC's IAM role.

---

## Business Continuity Impact

### What Happens When an SBC Fails?

| Scenario | Option 1: HA + Guardrails | Option 2: Standalone | Option 3: 2x Standalone | Option 4: On-Premises |
|----------|--------------------------|---------------------|------------------------|----------------------|
| **Active calls** | Survive — session state synchronised | All drop | All drop on primary | Survive — session state synchronised |
| **New calls during failover** | Brief interruption (seconds) | Unavailable until recovery | Route to secondary (DNS/SIP dependent) | Brief interruption (seconds) |
| **Recovery mechanism** | Automatic — SBC firmware handles failover | Manual — restart or replace instance | Automatic — but dependent on DNS TTL or SIP retry | Automatic — VRRP/native HA |
| **Estimated recovery time** | Seconds | Minutes to hours (depending on failure mode) | Seconds to minutes (DNS TTL dependent) | Seconds |
| **User impact** | Minimal — brief blip for new calls | Total voice outage for region | Dropped calls on primary; new calls route to secondary | Minimal — brief blip for new calls |
| **Provider reconfiguration** | Not required | May be required if IP changes | Not required (both IPs registered) | Not required |

### Voice Is a Critical Business Service

Voice outages directly impact:

- External customer communication
- Internal collaboration and emergency communications
- Regulatory compliance (recorded lines, emergency calling)
- Business operations dependent on telephony

The acceptable Recovery Time Objective (RTO) for voice services is a key input to this decision.

---

## Timeline and Effort

### Relative Build Effort

| Option | Build Effort | Key Dependencies | Notes |
|--------|-------------|-----------------|-------|
| **Option 1: HA + Guardrails** | Moderate–High | TTO estimate required for guardrail implementation; Stack Manager deployment; HA testing | Standard HA deployment plus EventBridge/Lambda/Config guardrail stack |
| **Option 2: Standalone** | Low | Standard SBC deployment only | Fastest path to production; no HA infrastructure |
| **Option 3: 2x Standalone** | Moderate | Dual SBC deployment; SIP provider and Teams configuration for primary/secondary | Two independent SBC configurations; no Stack Manager |
| **Option 4: On-Premises** | Variable | Hardware procurement lead time; data centre readiness; Direct Connect/VPN | Timeline heavily dependent on hardware availability and data centre logistics |

### Key Timeline Questions

- **Option 1:** What is TTO's estimated effort for the EventBridge + Lambda + Config guardrail stack?
- **Option 2:** Can be deployed immediately with existing SBC build procedures
- **Option 3:** Requires coordination with SIP providers and Microsoft for primary/secondary configuration
- **Option 4:** What is the lead time for AudioCodes physical appliance procurement?

---

## Licensing and Cost Summary

| Cost Element | Option 1: HA + Guardrails | Option 2: Standalone | Option 3: 2x Standalone | Option 4: On-Premises |
|-------------|--------------------------|---------------------|------------------------|----------------------|
| **SBC licences** | 2x per region (HA pair) | 1x per region | 2x per region | Hardware appliance licence |
| **EC2 instances** | 2x SBC + 1x Stack Manager per region | 1x SBC per region | 2x SBC per region | N/A |
| **Guardrail infrastructure** | ~$6/month per region | N/A | N/A | N/A |
| **Hardware appliance** | N/A | N/A | N/A | Mediant appliance cost |
| **Data centre costs** | N/A | N/A | N/A | Rack space, power, cooling |
| **Direct Connect / VPN** | N/A | N/A | N/A | Required for Teams integration |
| **Stack Manager** | 1x t3.medium per environment | N/A | N/A | N/A |

**Note:** Specific licensing costs should be confirmed with AudioCodes. EC2 instance costs depend on the selected instance type and region.

---

## Future Flexibility

### What Happens When Requirements Change?

| Scenario | Option 1 | Option 2 | Option 3 | Option 4 |
|----------|----------|----------|----------|----------|
| **"We need HA now"** | Already at target state | **TOTAL rebuild required** (Kapila confirmed) | Rebuild one SBC into HA pair (partial rebuild) | Already at target state |
| **"Add another region"** | Deploy new HA pair — repeatable pattern | Deploy single SBC — fast | Deploy 2x SBCs — repeatable | Procure and ship hardware |
| **"Move to cloud-first"** | Already cloud-native | Already cloud-native | Already cloud-native | Requires migration project |
| **"Scale capacity"** | Upgrade instance type or add HA pair | Upgrade instance type | Upgrade instance types | Hardware upgrade or additional appliance |
| **"Cyber changes position"** | Remove guardrails if no longer required | Add HA (total rebuild) | Convert to HA pair (partial rebuild) | N/A |

### Critical Consideration for Option 2

> Choosing a standalone SBC now and needing HA later is **not an incremental change**. AudioCodes (Kapila) has confirmed this requires a total rebuild — the Stack Manager must deploy the HA pair from scratch via CloudFormation. The existing standalone SBC cannot be retrofitted into an HA configuration.

---

## Decision Framework

### Factors to Consider

The following factors should be scored or discussed during the decision meeting to guide the selection:

| # | Factor | Question |
|---|--------|----------|
| 1 | **Risk appetite** | Is a 7–18 second exposure window with automated containment acceptable, or must `ReplaceRoute` be eliminated entirely? |
| 2 | **Voice criticality** | What is the acceptable RTO for voice services? Is a single point of failure tolerable? |
| 3 | **Cloud-first commitment** | Does the organisation's cloud-first strategy preclude an on-premises SBC deployment? |
| 4 | **Build vs. rebuild** | Is the risk of a total rebuild later (Option 2) acceptable given current timeline pressures? |
| 5 | **Cyber's position** | What is cybersecurity's formal position on the compensating controls proposed in Option 1? |
| 6 | **Timeline pressure** | How urgently must Direct Routing be in production? Does this favour a faster deployment option? |
| 7 | **Licensing budget** | Is double SBC licensing (Options 1 and 3) within budget, or does single licensing (Option 2) materially change the business case? |

---

## Questions for the Decision Meeting

The following questions should be answered before or during the decision meeting:

### For Cybersecurity

1. What is the formal position on the 7–18 second exposure window with 4-layer automated containment (Option 1)?
2. Is the compensating control architecture (EventBridge + Lambda + Config + Flow Logs) sufficient to close finding F-CS-017?
3. If Option 1 is not acceptable, is the position permanent or subject to review after guardrails are demonstrated in non-production?

### For IT Management

4. What is the acceptable RTO for voice services? Does this rule out Option 2 (single point of failure)?
5. Is the risk of a total rebuild later (Option 2 → HA) acceptable?
6. Does the cloud-first strategy rule out Option 4 (on-premises)?

### For Cloud Platform / TTO

7. What is the estimated effort to build the EventBridge + Lambda + Config guardrail stack (Option 1)?
8. Can the guardrail stack be built and tested in non-production before a final decision?

### For Voice Engineering

9. Can regional SIP providers support primary/secondary SBC configuration (Option 3)?
10. What is the hardware lead time for an AudioCodes physical appliance (Option 4)?
11. What is the expected call volume and concurrency per region to inform licensing?

### For All Stakeholders

12. Is this decision per-region (e.g., Option 1 for Australia, Option 2 for US) or must it be consistent across all regions?
13. What is the target date for Microsoft Teams Direct Routing go-live?

---

## Appendix: References

| Document | Relevance |
|----------|-----------|
| AudioCodes SBC — Unified Deployment & Configuration Guide v2.6 (Section 19: HA, Section 20: IAM) | HA failover mechanism, SBC IAM policy, ReplaceRoute and AssociateAddress scoping |
| Cybersecurity Analyst Review Report (F-CS-017) | Full finding detail, containment architecture, cost estimate, architecture diagrams |
| Cybersecurity Analyst Review Report (Appendix: F-CS-017 Containment Architecture) | EventBridge + Lambda containment design, validation logic, exposure window analysis |
| AWS IAM Service Authorisation Reference — ec2:ReplaceRoute | Confirms no condition keys for destination CIDR or target ENI parameters |
| Cross-Cutting Findings — CC-02 (IAM Privilege) | Broader IAM privilege concerns including Stack Manager |
| Solution Architect Review (F-SA series) | Architectural considerations including ARM HA, Stack Manager resilience |

---

*Generated 5 March 2026*
