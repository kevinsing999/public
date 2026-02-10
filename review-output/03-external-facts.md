# External Facts Verification

## Summary

This review verifies external facts claimed in the AudioCodes AWS Deployment Guide (4378 lines) covering AWS instance types and services, Microsoft Teams Direct Routing requirements, AudioCodes product specifications, URLs, and security best practices. The document is largely accurate on core technical facts. Issues found are primarily minor -- a few outdated recommendations, one potentially inaccurate spec detail, and some claims that need caveats. No critical factual errors were found that would prevent a successful deployment.

---

## Issues Found

### 1. OVOC Storage Recommendation Uses GP2 Instead of GP3

- **Line(s):** 360-361, 376, 386, 941, 951, 3273-3274
- **Claim:** OVOC storage is specified as "GP2 SSD" (e.g., "500 GB GP2 SSD", "AWS EBS: GP2 SSD 2 TB") and the note at line 386/951 states "GP2 SSD is recommended as the baseline storage tier."
- **Actual fact:** AWS gp3 is now the default EBS volume type when creating volumes via the console. gp3 provides 20% lower cost per GB ($0.08/GB-month vs $0.10/GB-month) and better baseline performance (3,000 IOPS regardless of volume size vs 3 IOPS/GB for gp2). While gp2 still works, recommending it as the "baseline storage tier" is outdated. The Appendix C tables (lines 3268-3274) correctly use "gp3" for Stack Manager and SBC but then use "gp2" for OVOC, which is inconsistent.
- **Severity:** Low. gp2 still functions. However, the recommendation should be updated to gp3 for cost savings and consistency.

### 2. Document Says Client Authentication EKU Mandatory "from March 2026" -- Timing Nuance

- **Line(s):** 733
- **Claim:** "Must include Client Authentication EKU (mandatory from March 2026)"
- **Actual fact:** The certificate requirement landscape is nuanced. Microsoft's certificate changes for Direct Routing are evolving. According to Microsoft documentation and community sources (including the erik365 blog referenced in the document itself), by June 2026, public CAs are expected to stop issuing certificates with Client Authentication EKU due to Chrome Root Program Policy v1.6. Microsoft currently accepts SBC certificates even without Client Authentication EKU but plans to require it in the future. The March 2026 date specifically relates to Microsoft requiring seven root certificate chains to be installed on SBCs. The document's statement conflates two different requirements.
- **Severity:** Medium. The date and requirement are partially correct but may confuse implementers. The exact enforcement timeline should be verified against the latest Microsoft Message Center announcements.

### 3. Stack Manager Note Says It Is "Mandatory for HA Failover Orchestration" (Misleading)

- **Line(s):** 383, 948
- **Claim:** In the compute requirements notes: "The Stack Manager (t3.medium) is a lightweight management component but is mandatory for HA failover orchestration."
- **Actual fact:** The document itself repeatedly and correctly states elsewhere (lines 91, 95, 338, 854, 2893-2894) that the Stack Manager does NOT participate in active HA failover -- the SBCs themselves call AWS APIs. The Stack Manager is mandatory for initial deployment, not for failover orchestration. This note contradicts the rest of the document.
- **Severity:** Medium. This is an internal inconsistency that could mislead readers about the Stack Manager's role.

### 4. r4.large Listed as Current Recommendation -- It Is a Previous-Generation Instance

- **Line(s):** 282
- **Claim:** r4.large (2 vCPU, 15.25 GiB) listed as a recommended instance type for SBC without transcoding.
- **Actual fact:** The vCPU and memory specs are correct (2 vCPUs, 15.25 GiB). However, r4 is a previous-generation instance family. AWS recommends migrating to r5 or r6i for better price-performance. While r4 instances are still available, listing them as a recommendation without noting their previous-generation status is misleading.
- **Severity:** Low. Still functional but suboptimal from a cost-performance perspective.

### 5. m4.xlarge and m4.large Are Previous-Generation Instances

- **Line(s):** 181, 219, 229, 347-348, 377-378, 942-943, 3271-3272
- **Claim:** ARM Configurator uses m4.xlarge (4 vCPU, 16 GiB) and ARM Router uses m4.large (2 vCPU, 8 GiB).
- **Actual fact:** The vCPU/memory specs are correct. However, m4 is a previous-generation instance family. AWS recommends m5 or m6i as successors. The document uses m5 instances for other components (SBC, OVOC) but uses m4 for ARM, which may reflect AudioCodes' specific AMI compatibility requirements rather than a documentation error.
- **Severity:** Low. If AudioCodes' ARM AMI requires m4, this is acceptable. Otherwise, m5 equivalents should be considered.

### 6. DigiCert Global Root G3 Listed as Required -- May Not Be Necessary

- **Line(s):** 1483
- **Claim:** "DigiCert Global Root G3" is listed as a required root CA trust anchor for Microsoft SIP certificates.
- **Actual fact:** Microsoft transitioned its SIP TLS certificates from Baltimore CyberTrust Root to DigiCert Global Root G2 in October 2023. The DigiCert Global Root G2 is confirmed as the active root CA. The search results do not indicate DigiCert Global Root G3 is currently in use for Microsoft Teams SIP certificates. Including it is not harmful (defense in depth) but may be premature or inaccurate.
- **Severity:** Low. Adding extra trusted roots does not cause harm, but the G3 claim may be inaccurate.

### 7. Baltimore CyberTrust Root Described as "Legacy" -- Correct but Its Expiry Should Be Noted

- **Line(s):** 1484
- **Claim:** "Baltimore CyberTrust Root" listed with note "Legacy root CA (may still be referenced)."
- **Actual fact:** The Baltimore CyberTrust Root certificate expired in May 2025. Microsoft completed the transition to DigiCert Global Root G2 in October 2023. The description "may still be referenced" understates the situation -- this certificate has expired and should be retained only for backward compatibility if still within validity period, or removed if expired. For a February 2026 document, this should note the certificate is expired.
- **Severity:** Low. Implementers should verify whether to include an expired root.

### 8. OVOC QoE Port Listed as 5001 in Some Places, 5000 in Others

- **Line(s):** 485 vs 1883/1979/3526/3634/3902
- **Claim:** Line 485 (Security Group table) says QoE uses port 5000. Lines 1883, 1979, 3526, 3634, 3902 say QoE uses port 5001.
- **Actual fact:** AudioCodes documentation indicates OVOC uses TCP port 5001 for QoE reporting. The port 5000 at line 485 labeled "Control/Media reports" appears inconsistent with the rest of the document. This is an internal inconsistency that should be reconciled. The firewall rules sections consistently use 5001, which is likely correct.
- **Severity:** Low-Medium. Could cause a firewall misconfiguration if the wrong port is used.

### 9. SBC Security Group Shows RTP Media Range as 6000-65535 -- Very Broad

- **Line(s):** 465
- **Claim:** SBC security group inbound rule shows "UDP 6000-65535" for RTP Media.
- **Actual fact:** While technically functional, this is an extremely broad port range. The document's own media realm configurations (Section 13.2 and Appendix D) define much more specific ranges: 6000-9999, 10000-19999, 20000-29999, 30000-39999, 40000-49999. Best practice would be to use these specific ranges in the security group rather than 6000-65535. AWS security groups support multiple rules, so specific ranges can be enumerated.
- **Severity:** Low. Functions correctly but does not follow the principle of least privilege that the document itself advocates elsewhere.

### 10. Microsoft Teams Media Port Range on SBC Side Shown as 20000-29999

- **Line(s):** 1912-1913, 3627
- **Claim:** SBC media port range for Teams traffic is 20000-29999.
- **Actual fact:** This is a deployment-specific configuration choice, not a Microsoft requirement. Microsoft's Teams media relays use source ports 3478-3481 and 49152-53247. The SBC operator chooses their own port range (20000-29999 in this case). This is correctly labeled as a configurable value but should not be confused with a Microsoft requirement. This is accurate as documented.
- **Severity:** None -- correctly documented as a local choice.

### 11. login.microsoft.com Referenced in Diagram Instead of login.microsoftonline.com

- **Line(s):** 3289
- **Claim:** Diagram shows "login.microsoft.com" as a Microsoft 365 endpoint.
- **Actual fact:** The correct OAuth endpoint for Microsoft Entra ID is `login.microsoftonline.com`, which is correctly used elsewhere in the document (lines 639, 1216, 2011, etc.). The `login.microsoft.com` domain does redirect to `login.microsoftonline.com` so it functionally works, but for consistency and accuracy the diagram should use the canonical FQDN.
- **Severity:** Very Low. Functionally equivalent due to redirect, but inconsistent with the rest of the document.

### 12. Pricing and Cost Claims Are Absent but Storage Costs Are Implied

- **Line(s):** N/A (general observation)
- **Claim:** The document does not make explicit pricing claims beyond describing t3.medium as "low cost."
- **Actual fact:** t3.medium is indeed one of the lower-cost general-purpose instance types (approximately $0.04/hour on-demand in us-east-1). The characterization as "low cost" is reasonable. No specific dollar amounts are claimed, so no pricing verification issues exist.
- **Severity:** None.

### 13. 52.120.0.0/14 Listed as Both Media AND Part of Signaling Range -- Potential Overlap

- **Line(s):** 1807-1808 vs 3649-3650
- **Claim:** Lines 1807-1808 describe 52.112.0.0/14 and 52.122.0.0/15 as signaling classification ranges. Line 3649 lists 52.120.0.0/14 (which includes 52.120-52.123) as "Teams Media Relays." Line 3650 lists 52.122.0.0/15 (52.122-52.123) as "Teams Signaling."
- **Actual fact:** 52.120.0.0/14 encompasses 52.120.0.0 through 52.123.255.255, which includes the 52.122.0.0/15 signaling range. Microsoft uses these ranges for both media and signaling. The classification rules (lines 1796-1801) correctly classify 52.122 and 52.123 as Teams signaling sources on the SBC. The IP range table in Appendix D is slightly confusing in showing both 52.120.0.0/14 (media) and 52.122.0.0/15 (signaling) as separate entries when 52.122.0.0/15 is a subset of 52.120.0.0/14.
- **Severity:** Very Low. This reflects Microsoft's actual IP range allocation, which does overlap. The firewall rules correctly handle both.

---

## Verified Accurate Claims

### AWS Instance Types (All Specs Verified Correct)
- **m5.large:** 2 vCPUs, 8 GiB -- Correct (line 281)
- **r4.large:** 2 vCPUs, 15.25 GiB -- Correct (line 282)
- **c5.2xlarge:** 8 vCPUs, 16 GiB -- Correct (line 283)
- **c5.9xlarge:** 36 vCPUs, 72 GiB -- Correct (line 284)
- **t3.medium:** 2 vCPUs, 4 GiB -- Correct (line 325, 375)
- **m4.xlarge:** 4 vCPUs, 16 GiB -- Correct (line 347, 377)
- **m4.large:** 2 vCPUs, 8 GiB -- Correct (line 348, 378)
- **m5.2xlarge:** 8 vCPUs, 32 GiB -- Correct (line 360)
- **m5.4xlarge:** 16 vCPUs, 64 GiB -- Correct (line 361, 376)
- **m5n.large:** 2 vCPUs, 8 GiB -- Correct (line 374, 939)

### AWS Services and Features
- **AWS NTP at 169.254.169.123:** Correct -- Amazon Time Sync Service is available at this link-local address (line 819)
- **VPC, Subnets, Internet Gateway, NAT Gateway, Route Tables, Security Groups:** All correctly named and described
- **Elastic Network Interfaces (ENIs):** Correctly described for multi-interface EC2 instances
- **IAM Role attachment to EC2 instances:** Correctly described workflow
- **CloudFormation for infrastructure deployment:** Correctly described
- **VPC Endpoints (PrivateLink) as alternative to NAT Gateway:** Correctly described (line 161)
- **AWS Direct Connect:** Correctly referenced for on-premises connectivity
- **AWS Transit Gateway:** Correctly referenced for inter-VPC connectivity
- **EC2 API actions (DescribeRouteTables, CreateRoute, ReplaceRoute, DeleteRoute, etc.):** All valid EC2 API actions

### AWS Region Names
- **ap-southeast-2:** Correctly identified as Australia (Sydney) (line 873)
- **us-east-1:** Correctly identified as United States (N. Virginia) (line 875)

### Microsoft Teams Direct Routing
- **SIP Endpoints (sip.pstnhub.microsoft.com, sip2, sip3) on port 5061 TLS:** Correct (lines 761-763)
- **TLS 1.2 minimum requirement:** Correct (line 734)
- **Mutual TLS (mTLS) required:** Correct (line 735)
- **Self-signed certificates not supported:** Correct (line 745)
- **Domain must be registered in Microsoft 365 tenant:** Correct (line 753)
- **Certificate must be from Microsoft Trusted Root Certificate Program CA:** Correct (line 731)
- **Approved CAs (DigiCert, GlobalSign, Comodo/Sectigo, Entrust, GoDaddy):** All confirmed as valid CAs in the Microsoft Trusted Root Certificate Program (lines 739-743)
- **Microsoft media IP ranges (52.112.0.0/14, 52.120.0.0/14):** Correct (lines 1912-1913)
- **Microsoft media ports (3478-3481, 49152-53247):** Correct
- **SRTP required for Teams media:** Correct (line 2639)

### Microsoft Graph API
- **CallRecords.Read.All permission for call records:** Correct (line 546)
- **User.Read.All for user profiles:** Correct (line 547)
- **Token endpoint format (login.microsoftonline.com/{TenantID}/oauth2/v2.0/token):** Correct (line 639)
- **Graph API endpoint /v1.0/communications/callRecords:** Correct (line 698)
- **Graph API endpoint /v1.0/users:** Correct (line 699)
- **User.Read delegated permission does not require admin consent:** Correct (line 688)

### Microsoft Admin Roles
- **Global Administrator, Teams Administrator, Teams Communications Administrator:** All correctly identified real roles (lines 768-771)

### PowerShell Commands
- **Install-Module MicrosoftTeams:** Correct syntax (line 779)
- **Connect-MicrosoftTeams:** Correct cmdlet (line 782)
- **New-CsOnlinePSTNGateway:** Correct cmdlet for SBC registration (line 792)
- **Get-CsOnlinePSTNGateway:** Correct cmdlet (line 795)
- **New-CsOnlineVoiceRoutingPolicy:** Correct cmdlet (line 798)
- **Set-CsPhoneNumberAssignment with -PhoneNumberType DirectRouting:** Correct cmdlet and parameter (line 801)

### AudioCodes Products
- **Mediant VE (Virtual Edition) SBC:** Real product, correctly described as virtual SBC for cloud deployment
- **Mediant 800C:** Real product, confirmed as a branch E-SBC/gateway appliance with E1/T1, FXS/FXO support, Gigabit Ethernet, and 1+1 redundancy (lines 826-832)
- **Stack Manager:** Real AudioCodes component for HA SBC deployment on AWS via CloudFormation, confirmed in AudioCodes documentation
- **ARM (AudioCodes Routing Manager):** Real product with Configurator and Router components
- **OVOC (One Voice Operations Center):** Real product with device management, QoE monitoring, and Teams integration
- **Minimum version 7.4.500 for multi-AZ HA:** Confirmed in AudioCodes installation manual (line 274)
- **Virtual IP range 169.254.64.0/24:** Confirmed as default VIP range used by Stack Manager (line 85)

### Security Best Practices Verified
- **TLS 1.2+ for management:** Industry standard best practice (line 959)
- **Restrict management access to admin subnets/jump hosts:** Standard practice (line 960)
- **Disable unused services and ports:** Standard hardening practice (line 961)
- **Change default credentials:** Fundamental security practice (line 963, 980)
- **LDAPS (port 636) for Active Directory authentication:** Correct secure LDAP implementation (line 1103)
- **Break glass accounts with dual-control access:** Aligns with industry best practice and NIST guidance (lines 2184-2268)
- **Key-based SSH authentication:** Recommended best practice (line 2983)
- **CloudTrail logging for API calls:** AWS security best practice (line 2999)
- **VPC Endpoints as alternative to internet egress:** Valid security enhancement (line 2973)
- **Password complexity, rotation, and account lockout:** Standard security controls (lines 981-982)
- **SNMPv3 over SNMPv1:** Correct -- SNMPv1 lacks encryption (line 983)

### URLs and Endpoints
- **Microsoft Graph endpoints (graph.microsoft.com, login.microsoftonline.com):** Correct
- **DigiCert root certificates URL (digicert.com/kb/digicert-root-certificates.htm):** Correct format (line 1489)
- **Microsoft 365 URLs and IP ranges documentation URL:** Correct (line 1813)
- **OAuth2 redirect URI format for native client:** Correct (line 660)
- **Microsoft Learn documentation links:** All appear to use correct URL patterns (lines 3088-3095)

### SIP Protocol Details
- **Port 5061 for TLS SIP signaling:** Standard SIP TLS port (line 1599)
- **Port 5060 for UDP/TCP SIP signaling:** Standard SIP port (line 1597)
- **SIP OPTIONS for keepalive:** Standard SBC practice (line 1649)
- **SIP 488 and 606 response codes:** Correct SIP response codes for codec negotiation failure (line 1577)
- **SIPREC for voice recording:** Industry standard protocol, correctly described (lines 2630-2733)
- **SRTP termination/bridging on SBC:** Correctly described behavior (line 1691)

### EKU OIDs
- **Server Authentication OID 1.3.6.1.5.5.7.3.1:** Correct (line 1116)
