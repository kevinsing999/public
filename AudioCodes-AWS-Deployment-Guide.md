# AudioCodes AWS Deployment Guide

## Cloud Operations & Project Team Reference Document

**Document Version:** 2.0
**Date:** February 2026
**Classification:** Public

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Critical Finding: Stack Manager Requirement for Cross-AZ HA](#critical-finding-stack-manager-requirement-for-cross-az-ha)
3. [Architecture Overview](#architecture-overview)
4. [Component Specifications](#component-specifications)
5. [Non-Production Environment Deployment](#non-production-environment-deployment)
6. [Production Environment Deployment](#production-environment-deployment)
7. [AWS Infrastructure Requirements](#aws-infrastructure-requirements)
8. [Microsoft Entra ID (Azure AD) Integration](#microsoft-entra-id-azure-ad-integration)
9. [Microsoft Graph API Permissions](#microsoft-graph-api-permissions)
10. [Microsoft Teams Direct Routing Requirements](#microsoft-teams-direct-routing-requirements)
11. [Break Glass Accounts](#break-glass-accounts)
12. [Deployment Methodology](#deployment-methodology)
13. [High Availability Considerations](#high-availability-considerations)
14. [IAM Permissions and Security](#iam-permissions-and-security)
15. [Licensing Considerations](#licensing-considerations)
16. [References and Documentation](#references-and-documentation)

---

## Executive Summary

This document provides deployment guidance for the AudioCodes voice infrastructure stack on Amazon Web Services (AWS). It covers the deployment of:

- **Mediant Virtual Edition (VE) Session Border Controllers (SBCs)** in High Availability configuration
- **AudioCodes Stack Manager** for HA lifecycle management
- **AudioCodes Routing Manager (ARM)** for centralized call routing
- **AudioCodes One Voice Operations Center (OVOC)** for management and monitoring

### Key Takeaways

1. **Stack Manager is Mandatory:** The AudioCodes Stack Manager is a **mandatory component** for deploying Mediant VE SBCs in High Availability across multiple Availability Zones. It manipulates VPC route tables to facilitate failover.

2. **HA Scope:** High Availability is configured **within a single VPC across two Availability Zones**. This deployment does NOT use cross-VPC HA or AWS Transit Gateway for Virtual IP routing.

3. **Microsoft Integration Required:** All components require integration with Microsoft Entra ID (Azure AD) for authentication and Microsoft Graph API for Teams call quality data and user information.

4. **Break Glass Accounts:** Each workload requires a dedicated local break glass account for emergency access when identity provider integration fails.

---

## Critical Finding: Stack Manager Requirement for Cross-AZ HA

### Why Stack Manager is Required

When deploying AudioCodes Mediant VE SBCs in High Availability across two Availability Zones in AWS, the **Stack Manager is a mandatory separate VM** that performs the following critical functions:

1. **Route Table Manipulation:** During failover, the Stack Manager updates AWS VPC route table entries to redirect traffic from the failed Active SBC to the Standby SBC.

2. **Virtual IP Address Management:** The Stack Manager allocates and manages Virtual IP addresses (by default from the `169.254.64.0/24` subnet) that exist outside the VPC CIDR range.

3. **Cluster Lifecycle Management:** The Stack Manager handles initial deployment, topology updates, and "stack healing" in case of underlying cloud resource corruption.

### HA Scope Clarification

**Important:** This deployment uses HA **within a single VPC across two Availability Zones only**. We are NOT implementing:
- Cross-VPC HA
- Cross-region HA for SBCs
- AWS Transit Gateway for Virtual IP routing between VPCs

The Virtual IP addresses are used for failover routing **within the same VPC**, where the route table is updated to point traffic to the newly active SBC's ENI.

### How the Failover Mechanism Works

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AWS VPC (Single Region)                          │
│                                                                          │
│   ┌─────────────────────┐          ┌─────────────────────┐              │
│   │  Availability Zone A │          │  Availability Zone B │              │
│   │                      │          │                      │              │
│   │  ┌────────────────┐  │          │  ┌────────────────┐  │              │
│   │  │  Mediant VE    │  │          │  │  Mediant VE    │  │              │
│   │  │  SBC (Active)  │  │   HA     │  │  SBC (Standby) │  │              │
│   │  │                │◄─┼──Subnet──┼─►│                │  │              │
│   │  │  ENI: 10.0.1.x │  │          │  │  ENI: 10.0.2.x │  │              │
│   │  └────────────────┘  │          │  └────────────────┘  │              │
│   │                      │          │                      │              │
│   └─────────────────────┘          └─────────────────────┘              │
│                                                                          │
│   ┌────────────────────────────────────────────────────────────────┐    │
│   │                     Stack Manager VM                            │    │
│   │                                                                 │    │
│   │  - Monitors SBC health via HA subnet                           │    │
│   │  - On failover: Updates VPC Route Tables                       │    │
│   │  - Manages Virtual IPs (169.254.64.x) in route tables          │    │
│   │  - Requires EC2, CloudFormation, IAM API access                │    │
│   └────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│   ┌────────────────────────────────────────────────────────────────┐    │
│   │  VPC Route Table (Updated by Stack Manager on Failover)        │    │
│   │                                                                 │    │
│   │  169.254.64.1/32 → eni-xxxx (Active SBC's ENI)                 │    │
│   │                    ↓ (On failover, Stack Manager updates to)   │    │
│   │  169.254.64.1/32 → eni-yyyy (Standby SBC's ENI, now Active)   │    │
│   └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### API Access Requirements

The Stack Manager requires **internet access** (via Internet Gateway or NAT Gateway) to communicate with AWS APIs:
- EC2 API
- CloudFormation API
- IAM API
- Elastic Load Balancing API (if using NLB)

---

## Architecture Overview

### Non-Production Environment (Australia Region Only)

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           NON-PRODUCTION AWS ACCOUNT                            │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        AUSTRALIA REGION (ap-southeast-2)                 │   │
│  │                                                                          │   │
│  │   ┌──────────────┐    ┌──────────────┐    ┌─────────────────────┐       │   │
│  │   │ Mediant VE   │    │ Mediant VE   │    │   Stack Manager     │       │   │
│  │   │ SBC #1       │◄──►│ SBC #2       │    │   (t3.medium)       │       │   │
│  │   │ (AZ-A)       │    │ (AZ-B)       │    │                     │       │   │
│  │   │ Active       │    │ Standby      │    │ Manages HA failover │       │   │
│  │   └──────────────┘    └──────────────┘    └─────────────────────┘       │   │
│  │                                                                          │   │
│  │   ┌──────────────────────────┐    ┌──────────────────────────┐          │   │
│  │   │  ARM Configurator        │    │  ARM Router              │          │   │
│  │   │  (m4.xlarge)             │    │  (m4.large)              │          │   │
│  │   │  Single Instance         │    │  Single Instance         │          │   │
│  │   └──────────────────────────┘    └──────────────────────────┘          │   │
│  │                                                                          │   │
│  │   Total VMs: 5                                                          │   │
│  │   - 2x SBC (HA pair)                                                    │   │
│  │   - 1x Stack Manager                                                    │   │
│  │   - 1x ARM Configurator                                                 │   │
│  │   - 1x ARM Router                                                       │   │
│  │                                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

### Production Environment

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                            PRODUCTION AWS ACCOUNT                               │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        AUSTRALIA REGION (ap-southeast-2)                 │   │
│  │                                                                          │   │
│  │   ┌──────────────┐    ┌──────────────┐    ┌─────────────────────┐       │   │
│  │   │ Mediant VE   │    │ Mediant VE   │    │   Stack Manager     │       │   │
│  │   │ SBC #1       │◄──►│ SBC #2       │    │   (t3.medium)       │       │   │
│  │   │ (AZ-A)       │    │ (AZ-B)       │    │                     │       │   │
│  │   │ Active       │    │ Standby      │    │ Manages HA failover │       │   │
│  │   └──────────────┘    └──────────────┘    └─────────────────────┘       │   │
│  │                                                                          │   │
│  │   ┌──────────────────────────────┐    ┌──────────────────────────┐      │   │
│  │   │  OVOC Server                 │    │  ARM Configurator        │      │   │
│  │   │  (m5.2xlarge)                │    │  (m4.xlarge)             │      │   │
│  │   │  Includes Device Manager     │    │                          │      │   │
│  │   └──────────────────────────────┘    └──────────────────────────┘      │   │
│  │                                                                          │   │
│  │   ┌──────────────────────────┐                                          │   │
│  │   │  ARM Router               │                                          │   │
│  │   │  (m4.large)               │                                          │   │
│  │   └──────────────────────────┘                                          │   │
│  │                                                                          │   │
│  │   Total AUS VMs: 6                                                      │   │
│  │   - 2x SBC (HA pair)                                                    │   │
│  │   - 1x Stack Manager                                                    │   │
│  │   - 1x OVOC (includes Device Manager)                                   │   │
│  │   - 1x ARM Configurator                                                 │   │
│  │   - 1x ARM Router                                                       │   │
│  │                                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        UNITED STATES REGION (us-east-1)                  │   │
│  │                                                                          │   │
│  │   ┌──────────────┐    ┌──────────────┐    ┌─────────────────────┐       │   │
│  │   │ Mediant VE   │    │ Mediant VE   │    │   Stack Manager     │       │   │
│  │   │ SBC #1       │◄──►│ SBC #2       │    │   (t3.medium)       │       │   │
│  │   │ (AZ-A)       │    │ (AZ-B)       │    │                     │       │   │
│  │   │ Active       │    │ Standby      │    │ US Region Manager   │       │   │
│  │   └──────────────┘    └──────────────┘    └─────────────────────┘       │   │
│  │                                                                          │   │
│  │   ┌──────────────────────────┐                                          │   │
│  │   │  ARM Router               │                                          │   │
│  │   │  (m4.large)               │                                          │   │
│  │   └──────────────────────────┘                                          │   │
│  │                                                                          │   │
│  │   Total US VMs: 4                                                       │   │
│  │   - 2x SBC (HA pair)                                                    │   │
│  │   - 1x Stack Manager                                                    │   │
│  │   - 1x ARM Router                                                       │   │
│  │                                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  PRODUCTION TOTAL: 10 VMs                                                      │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. Mediant Virtual Edition (VE) SBC

| Specification | Details |
|--------------|---------|
| **Purpose** | Session Border Controller for SIP trunking, security, media handling |
| **HA Mode** | 1+1 Active/Standby across Availability Zones (within single VPC) |
| **Minimum Version for Cross-AZ HA** | Version 7.4.500 |
| **Deployment Method** | Via Stack Manager (required for multi-AZ HA) |

#### Recommended EC2 Instance Types

| Use Case | Instance Type | vCPUs | Memory | Notes |
|----------|--------------|-------|--------|-------|
| Without Transcoding | m5.large | 2 | 8 GiB | Basic SIP proxy |
| Without Transcoding (Higher capacity) | r4.large | 2 | 15.25 GiB | Memory optimized |
| With Transcoding | c5.2xlarge | 8 | 16 GiB | Compute optimized for DSP |
| With Transcoding (High capacity) | c5.9xlarge | 36 | 72 GiB | High session count with transcoding |

#### Network Interfaces Required (per SBC)

| Interface | Purpose | Subnet Type |
|-----------|---------|-------------|
| eth0 | Management, Signaling, Media (Main) | Main Subnet |
| eth1 | HA Communication | HA Subnet (dedicated) |
| eth2+ | Additional Signaling/Media (optional) | Additional Subnets |

---

### 2. AudioCodes Stack Manager

| Specification | Details |
|--------------|---------|
| **Purpose** | HA cluster deployment, lifecycle management, route table failover |
| **EC2 Instance Type** | t3.medium |
| **Storage** | 8 GiB gp3 (default) |
| **Deployment** | One per region where SBC HA is deployed |

#### Critical Requirements

- **Must reside in the same VPC** as the SBC instances it manages
- **Requires internet access** (via IGW or NAT Gateway) for AWS API calls
- **IAM Role** with EC2, CloudFormation, IAM, and optionally ELB permissions

---

### 3. AudioCodes Routing Manager (ARM)

| Component | Instance Type | vCPUs | Memory | Quantity |
|-----------|--------------|-------|--------|----------|
| **Configurator** | m4.xlarge | 4 | 16 GiB | 1 (single instance) |
| **Router** | m4.large | 2 | 8 GiB | 1+ per region |

#### Deployment Requirements

- **All ARM VMs must be in the same VPC and subnet**
- Configurator: Single instance only (centralized in AUS)
- Router: Deploy one per region for local routing decisions

---

### 4. AudioCodes One Voice Operations Center (OVOC)

| Profile | Instance Type | vCPUs | Memory | Storage |
|---------|--------------|-------|--------|---------|
| **Low Profile** | m5.2xlarge | 8 | 32 GiB | 500 GB GP2 SSD |
| **High Profile** | m5.4xlarge | 16 | 64 GiB | 2 TB GP2 SSD |

#### Includes

- Device Manager functionality (manages IP phones and SBCs)
- Quality of Experience monitoring
- Network topology management
- **Microsoft Teams Call Quality Dashboard integration**

---

## Non-Production Environment Deployment

### Component Inventory (Australia Region Only)

| Component | Region | Quantity | Instance Type | Purpose |
|-----------|--------|----------|---------------|---------|
| Mediant VE SBC | AUS (ap-southeast-2) | 2 | m5.large or c5.2xlarge | HA Pair across AZs |
| Stack Manager | AUS (ap-southeast-2) | 1 | t3.medium | HA Management |
| ARM Configurator | AUS (ap-southeast-2) | 1 | m4.xlarge | Routing configuration |
| ARM Router | AUS (ap-southeast-2) | 1 | m4.large | Call routing |

**Total Non-Production VMs: 5**

---

## Production Environment Deployment

### Component Inventory

#### Australia Region (ap-southeast-2)

| Component | Quantity | Instance Type | Purpose |
|-----------|----------|---------------|---------|
| Mediant VE SBC | 2 | m5.large or c5.2xlarge | HA Pair across AZs |
| Stack Manager | 1 | t3.medium | HA Management |
| OVOC | 1 | m5.2xlarge | Management, Monitoring, Device Manager |
| ARM Configurator | 1 | m4.xlarge | Routing configuration |
| ARM Router | 1 | m4.large | Call routing |

**AUS Region Total: 6 VMs**

#### United States Region (us-east-1)

| Component | Quantity | Instance Type | Purpose |
|-----------|----------|---------------|---------|
| Mediant VE SBC | 2 | m5.large or c5.2xlarge | HA Pair across AZs |
| Stack Manager | 1 | t3.medium | HA Management |
| ARM Router | 1 | m4.large | Call routing |

**US Region Total: 4 VMs**

**Production Grand Total: 10 VMs**

### Note on Device Manager

OVOC includes Device Manager functionality. A separate "Device Manager" deployment is not required.

---

## AWS Infrastructure Requirements

### VPC Configuration

#### Per Region Requirements

| Resource | Requirement | Notes |
|----------|-------------|-------|
| VPC | 1 per region | Dedicated or shared |
| Subnets | Minimum 2 per AZ (Main + HA) | Plus optional additional subnets |
| Internet Gateway or NAT Gateway | Required | For Stack Manager API access |
| Route Tables | One per subnet minimum | Stack Manager will modify these |

### Subnet Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              VPC: 10.0.0.0/16                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────────┐    ┌────────────────────────────┐          │
│  │   Availability Zone A      │    │   Availability Zone B      │          │
│  │                            │    │                            │          │
│  │  Main Subnet: 10.0.1.0/24  │    │  Main Subnet: 10.0.2.0/24  │          │
│  │  - SBC eth0                │    │  - SBC eth0                │          │
│  │  - Stack Manager           │    │                            │          │
│  │  - OVOC (if deployed)      │    │                            │          │
│  │  - ARM (all components)    │    │                            │          │
│  │                            │    │                            │          │
│  │  HA Subnet: 10.0.11.0/24   │    │  HA Subnet: 10.0.12.0/24   │          │
│  │  - SBC eth1 (HA traffic)   │    │  - SBC eth1 (HA traffic)   │          │
│  │                            │    │                            │          │
│  └────────────────────────────┘    └────────────────────────────┘          │
│                                                                             │
│  Virtual IP Range (outside VPC CIDR): 169.254.64.0/24                      │
│  - Used by Stack Manager for failover routing within this VPC              │
│  - Routes updated to point to active SBC ENI                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Security Groups

#### Stack Manager Security Group

| Direction | Protocol | Port | Source/Destination | Purpose |
|-----------|----------|------|-------------------|---------|
| Inbound | TCP | 22 | Admin CIDR | SSH Management |
| Inbound | TCP | 443 | Admin CIDR | HTTPS Management |
| Outbound | TCP | 443 | 0.0.0.0/0 | AWS API Access |
| Outbound | All | All | VPC CIDR | SBC Communication |

#### SBC Security Group

| Direction | Protocol | Port | Source/Destination | Purpose |
|-----------|----------|------|-------------------|---------|
| Inbound | TCP | 22 | Admin CIDR | SSH |
| Inbound | TCP | 80/443 | Admin CIDR | Web Management |
| Inbound | TCP/UDP | 5060/5061 | SIP Endpoints | SIP Signaling |
| Inbound | UDP | 6000-65535 | Media Sources | RTP Media |
| Inbound | All | All | HA Subnet CIDR | HA Communication |
| Outbound | All | All | 0.0.0.0/0 | All traffic |

#### ARM Security Group

| Direction | Protocol | Port | Source/Destination | Purpose |
|-----------|----------|------|-------------------|---------|
| Inbound | TCP | 22 | Admin CIDR | SSH |
| Inbound | TCP | 80/443 | Enterprise CIDR | HTTP/HTTPS |
| Inbound | All | All | VPC CIDR | Internal communication |
| Outbound | All | All | 0.0.0.0/0 | All traffic |

#### OVOC Security Group

| Direction | Protocol | Port | Source/Destination | Purpose |
|-----------|----------|------|-------------------|---------|
| Inbound | TCP | 22 | Admin CIDR | SSH |
| Inbound | TCP | 443 | Admin CIDR | HTTPS Web UI |
| Inbound | UDP | 162 | SBC CIDR | SNMP Traps |
| Inbound | UDP | 1161 | SBC CIDR | Keep-alive (NAT traversal) |
| Inbound | TCP | 5000 | SBC CIDR | Control/Media reports |
| Outbound | TCP | 443 | 0.0.0.0/0 | Microsoft Graph API |
| Outbound | All | All | VPC CIDR | Internal traffic |

---

## Microsoft Entra ID (Azure AD) Integration

### Overview

All AudioCodes components require integration with Microsoft Entra ID (formerly Azure AD) for:
- User authentication (OAuth 2.0)
- Microsoft Teams Direct Routing
- Call quality data retrieval
- User directory information

### Required App Registrations Summary

| App Registration | Used By | Purpose |
|-----------------|---------|---------|
| AudioCodes-OVOC-Teams-Integration | OVOC | Teams QoE data, user information |
| AudioCodes-ARM-WebUI | ARM | Web UI authentication |
| AudioCodes-ARM-REST-API | ARM | REST API authentication |
| AudioCodes-SBC-DirectRouting | SBC | Teams Direct Routing SBA (if applicable) |

---

### App Registration 1: OVOC Teams Integration

**Purpose:** Enables OVOC to retrieve Microsoft Teams call quality data and user information via Microsoft Graph API.

#### Registration Steps

1. Navigate to **Azure Portal** > **Microsoft Entra ID** > **App registrations** > **New registration**
2. Configure:
   - **Name:** `AudioCodes-OVOC-Teams-Integration`
   - **Supported account types:** Accounts in this organizational directory only (Single tenant)
   - **Redirect URI:** Leave blank (not required for application permissions)
3. Click **Register**

#### Credentials to Capture

| Credential | Location | Usage |
|------------|----------|-------|
| Application (Client) ID | Overview blade | OVOC configuration |
| Directory (Tenant) ID | Overview blade | OVOC configuration |
| Client Secret | Certificates & secrets blade | OVOC configuration |

#### Client Secret Creation

1. Navigate to **Certificates & secrets** > **Client secrets** > **New client secret**
2. Description: `OVOC-Teams-QoE-Integration`
3. Expiry: Select appropriate expiry (recommend 24 months with calendar reminder)
4. **IMPORTANT:** Copy the secret value immediately - it cannot be retrieved later

#### API Permissions Required

| API | Permission | Type | Purpose |
|-----|------------|------|---------|
| Microsoft Graph | `CallRecords.Read.All` | Application | Read all call records (CDR/QoE) |
| Microsoft Graph | `User.Read.All` | Application | Read user profiles |

#### Grant Admin Consent

1. Navigate to **API permissions**
2. Click **Grant admin consent for [Tenant Name]**
3. Verify both permissions show green checkmarks under "Status"

#### OVOC Configuration

Configure in OVOC under **System** > **Administration** > **External Servers** > **Microsoft 365**:

| Field | Value |
|-------|-------|
| Tenant ID | `<Directory (Tenant) ID>` |
| Client ID | `<Application (Client) ID>` |
| Client Secret | `<Secret Value>` |

---

### App Registration 2: ARM Web UI Authentication

**Purpose:** Enables OAuth 2.0 authentication for ARM web interface users.

#### Registration Steps

1. Navigate to **Azure Portal** > **Microsoft Entra ID** > **App registrations** > **New registration**
2. Configure:
   - **Name:** `AudioCodes-ARM-WebUI`
   - **Supported account types:** Accounts in this organizational directory only
   - **Redirect URI:** `https://<ARM-FQDN>/ARM/armui/login`
3. Click **Register**

#### Authentication Configuration

1. Navigate to **Authentication**
2. Under **Implicit grant and hybrid flows**, enable:
   - [x] Access tokens
   - [x] ID tokens

#### API Permissions Required

| API | Permission | Type | Purpose |
|-----|------------|------|---------|
| Microsoft Graph | `User.Read` | Delegated | Sign in and read user profile |
| Microsoft Graph | `User.Read.All` | Application | Read all users' full profiles |
| Microsoft Graph | `Group.Read.All` | Application | Read all groups |
| Microsoft Graph | `Application.Read.All` | Application | Read all applications |

#### Create App Roles

Navigate to **App roles** > **Create app role** for each role:

| Display Name | Value | Description |
|--------------|-------|-------------|
| Security Administrator | `SecurityAdmin` | Full administrative access |
| Administrator | `Admin` | Standard administrative access |
| Monitor | `Monitor` | Read-only monitoring access |

#### Enterprise Application Assignment

1. Navigate to **Enterprise applications** > **AudioCodes-ARM-WebUI**
2. Under **Users and groups**, assign users/groups to appropriate roles

---

### App Registration 3: ARM REST API Authentication

**Purpose:** Enables service-to-service authentication for ARM REST API calls.

#### Registration Steps

1. Navigate to **Azure Portal** > **Microsoft Entra ID** > **App registrations** > **New registration**
2. Configure:
   - **Name:** `AudioCodes-ARM-REST-API`
   - **Supported account types:** Accounts in this organizational directory only
   - **Redirect URI:** Leave blank
3. Click **Register**

#### API Permissions Required

| API | Permission | Type | Purpose |
|-----|------------|------|---------|
| AudioCodes-ARM-WebUI | `user_impersonation` | Delegated | Access ARM API |

#### Client Credentials

Create a client secret as described above for API authentication.

#### Token Endpoint

```
POST https://login.microsoftonline.com/{TenantID}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id={ARM-REST-API-ClientID}
&client_secret={ARM-REST-API-Secret}
&scope=api://{ARM-WebUI-ClientID}/.default
```

---

### App Registration 4: SBC Teams Direct Routing (If Using SBA)

**Purpose:** Required if using Survivable Branch Appliance (SBA) functionality with Teams Direct Routing.

#### Registration Steps

1. Navigate to **Azure Portal** > **Microsoft Entra ID** > **App registrations** > **New registration**
2. Configure:
   - **Name:** `AudioCodes-SBC-DirectRouting`
   - **Supported account types:** Accounts in this organizational directory only
   - **Redirect URI:** `https://login.microsoftonline.com/common/oauth2/nativeclient`
3. Click **Register**

#### Authentication Configuration

1. Navigate to **Authentication**
2. Under **Implicit grant and hybrid flows**, enable:
   - [x] Access tokens
   - [x] ID tokens

#### API Permissions Required

| API | Permission | Type | Purpose |
|-----|------------|------|---------|
| Skype and Teams Tenant Admin API | `application_access_custom_sba_appliance` | Application | SBA appliance access |

**Note:** Admin consent is required for this permission.

---

## Microsoft Graph API Permissions

### Complete Permissions Matrix

| Component | API | Permission | Type | Admin Consent | Purpose |
|-----------|-----|------------|------|---------------|---------|
| **OVOC** | Microsoft Graph | `CallRecords.Read.All` | Application | Required | Teams call quality data |
| **OVOC** | Microsoft Graph | `User.Read.All` | Application | Required | User profile information |
| **ARM** | Microsoft Graph | `User.Read` | Delegated | Not Required | User sign-in |
| **ARM** | Microsoft Graph | `User.Read.All` | Application | Required | Read all user profiles |
| **ARM** | Microsoft Graph | `Group.Read.All` | Application | Required | Group membership for RBAC |
| **ARM** | Microsoft Graph | `Application.Read.All` | Application | Required | App role retrieval |
| **SBC** | Skype and Teams Tenant Admin | `application_access_custom_sba_appliance` | Application | Required | SBA functionality |

### Graph API Endpoints Used

| Component | Endpoint | Purpose |
|-----------|----------|---------|
| OVOC | `https://graph.microsoft.com/v1.0/communications/callRecords` | Call records subscription |
| OVOC | `https://graph.microsoft.com/v1.0/users` | User information |
| ARM | `https://graph.microsoft.com/v1.0/me` | Current user profile |
| ARM | `https://graph.microsoft.com/v1.0/users` | User directory |
| ARM | `https://graph.microsoft.com/v1.0/groups` | Group membership |

### OVOC Teams Integration Requirements

#### Prerequisites

1. **OVOC Version:** 8.0 or later (8.0.114+ recommended)
2. **License:** Active "Analytics" license for Teams QoE monitoring
3. **Certificate:** OVOC must have a **valid public CA certificate** (not self-signed)
4. **Network:** Outbound HTTPS (443) to Microsoft Graph API endpoints
5. **FQDN:** Static public IP and properly configured FQDN (e.g., `ovoc.yourdomain.com`)

#### Data Retrieved from Microsoft

| Data Type | Graph API | Retention |
|-----------|-----------|-----------|
| Call Detail Records (CDR) | CallRecords API | Per OVOC retention policy |
| Call Quality Metrics (QoE) | CallRecords API | Per OVOC retention policy |
| User Display Names | Users API | Cached |
| User Principal Names | Users API | Cached |

---

## Microsoft Teams Direct Routing Requirements

### Certificate Requirements

| Requirement | Details |
|-------------|---------|
| **Certificate Authority** | Must be signed by a CA in the [Microsoft Trusted Root Certificate Program](https://docs.microsoft.com/en-us/security/trusted-root/participants-list) |
| **Subject Name (CN) or SAN** | Must contain the SBC FQDN (e.g., `sbc.yourdomain.com`) |
| **Extended Key Usage** | Must include Client Authentication EKU (mandatory from March 2026) |
| **TLS Version** | TLS 1.2 minimum (TLS 1.3 recommended) |
| **Mutual TLS (mTLS)** | Required for SBC-to-Teams connectivity |

#### Approved Certificate Authorities (Examples)

- DigiCert
- GlobalSign
- Comodo/Sectigo
- Entrust
- GoDaddy

**Note:** Self-signed certificates are NOT supported.

### DNS Requirements

| Record Type | Name | Value | Purpose |
|------------|------|-------|---------|
| A | `sbc.yourdomain.com` | `<SBC Public IP>` | SBC endpoint resolution |

**Domain Registration:** The domain used for the SBC FQDN must be registered and verified in your Microsoft 365 tenant.

### Microsoft SIP Endpoints

The SBC connects outbound to these Microsoft endpoints (allow in firewall):

| FQDN | Port | Protocol | Purpose |
|------|------|----------|---------|
| `sip.pstnhub.microsoft.com` | 5061 | TLS | Primary SIP endpoint |
| `sip2.pstnhub.microsoft.com` | 5061 | TLS | Secondary SIP endpoint |
| `sip3.pstnhub.microsoft.com` | 5061 | TLS | Tertiary SIP endpoint |

### Microsoft 365 Admin Roles Required

| Role | Purpose |
|------|---------|
| **Global Administrator** | Grant admin consent for app registrations |
| **Teams Administrator** | Configure Direct Routing, voice policies |
| **Teams Communications Administrator** | Manage calling policies |

### PowerShell Configuration Requirements

#### Required Modules

```powershell
# Install MicrosoftTeams module
Install-Module -Name MicrosoftTeams -Force -AllowClobber

# Connect to Teams (interactive)
Connect-MicrosoftTeams

# Or connect with service principal (for automation)
Connect-MicrosoftTeams -TenantId "<TenantId>" -ApplicationId "<AppId>" -CertificateThumbprint "<Thumbprint>"
```

#### Key PowerShell Commands

```powershell
# Register SBC in Teams
New-CsOnlinePSTNGateway -Fqdn "sbc.yourdomain.com" -SipSignalingPort 5061 -Enabled $true

# View registered SBCs
Get-CsOnlinePSTNGateway

# Create voice routing policy
New-CsOnlineVoiceRoutingPolicy -Identity "AU-VoicePolicy" -OnlinePstnUsages @{Add="AU-Usage"}

# Enable user for Direct Routing
Set-CsPhoneNumberAssignment -Identity user@domain.com -PhoneNumber "+61XXXXXXXXX" -PhoneNumberType DirectRouting
```

---

## Break Glass Accounts

### Overview

Each AudioCodes workload **must** have a dedicated local break glass account for emergency access when:
- Microsoft Entra ID is unavailable
- OAuth authentication fails
- Identity provider integration is misconfigured
- Emergency maintenance is required

### Break Glass Account Requirements

| Requirement | Details |
|-------------|---------|
| **Account Type** | Local account on each appliance |
| **Naming Convention** | `breakglass-<component>-<environment>` |
| **Password Policy** | Minimum 20 characters, complex |
| **Storage** | Secure secret repository of your choice |
| **Access** | Documented procedure, dual-control access |
| **Audit** | All usage must be logged and reviewed |

### Break Glass Accounts Per Workload

#### Non-Production Environment

| Component | Username | Purpose |
|-----------|----------|---------|
| Stack Manager | `breakglass-stackmgr-nonprod` | Emergency Stack Manager access |
| SBC #1 (AZ-A) | `breakglass-sbc1-nonprod` | Emergency SBC access |
| SBC #2 (AZ-B) | `breakglass-sbc2-nonprod` | Emergency SBC access |
| ARM Configurator | `breakglass-armcfg-nonprod` | Emergency ARM Configurator access |
| ARM Router | `breakglass-armrtr-nonprod` | Emergency ARM Router access |

**Non-Production Total: 5 break glass accounts**

#### Production Environment - Australia

| Component | Username | Purpose |
|-----------|----------|---------|
| Stack Manager | `breakglass-stackmgr-prod-aus` | Emergency Stack Manager access |
| SBC #1 (AZ-A) | `breakglass-sbc1-prod-aus` | Emergency SBC access |
| SBC #2 (AZ-B) | `breakglass-sbc2-prod-aus` | Emergency SBC access |
| OVOC | `breakglass-ovoc-prod` | Emergency OVOC access |
| ARM Configurator | `breakglass-armcfg-prod` | Emergency ARM Configurator access |
| ARM Router (AUS) | `breakglass-armrtr-prod-aus` | Emergency ARM Router access |

**Production AUS Total: 6 break glass accounts**

#### Production Environment - United States

| Component | Username | Purpose |
|-----------|----------|---------|
| Stack Manager | `breakglass-stackmgr-prod-us` | Emergency Stack Manager access |
| SBC #1 (AZ-A) | `breakglass-sbc1-prod-us` | Emergency SBC access |
| SBC #2 (AZ-B) | `breakglass-sbc2-prod-us` | Emergency SBC access |
| ARM Router (US) | `breakglass-armrtr-prod-us` | Emergency ARM Router access |

**Production US Total: 4 break glass accounts**

### Break Glass Account Management

#### Password Storage

Store break glass credentials in a secure, access-controlled secret repository of your choice (e.g., enterprise password vault, secrets manager, or equivalent secure storage solution).

**Recommended folder/path structure:**

| Environment | Path/Folder |
|-------------|-------------|
| Non-Production | `/audiocodes/nonprod/` |
| Production - Australia | `/audiocodes/prod-aus/` |
| Production - United States | `/audiocodes/prod-us/` |

#### Access Procedure

1. **Dual Control:** Two authorized personnel required to retrieve credentials
2. **Incident Ticket:** Create incident ticket before retrieval
3. **Time-Limited:** Credentials retrieved for specific maintenance window
4. **Audit Trail:** Log all access to secrets manager
5. **Post-Use:** Rotate password after each use (recommended)

#### Password Rotation Schedule

| Frequency | Action |
|-----------|--------|
| Quarterly | Review break glass account status |
| Semi-Annually | Rotate all break glass passwords |
| After Each Use | Rotate used account password |
| Annually | Full break glass procedure test |

---

## Deployment Methodology

### Deployment Sequence

```
Phase 1: Infrastructure Preparation
├── 1.1 Create VPC and Subnets (if not existing)
├── 1.2 Create Internet Gateway / NAT Gateway
├── 1.3 Create Security Groups
├── 1.4 Create IAM Role for Stack Manager
├── 1.5 Create Key Pairs
└── 1.6 Create Break Glass Accounts in Secret Repository

Phase 2: Microsoft Entra ID Configuration
├── 2.1 Create OVOC App Registration
├── 2.2 Create ARM WebUI App Registration
├── 2.3 Create ARM REST API App Registration
├── 2.4 Create SBC App Registration (if SBA required)
├── 2.5 Configure API Permissions
├── 2.6 Grant Admin Consent
└── 2.7 Document all credentials securely

Phase 3: Stack Manager Deployment
├── 3.1 Deploy Stack Manager EC2 instance (t3.medium)
├── 3.2 Attach IAM Role to Stack Manager
├── 3.3 Configure Stack Manager networking
├── 3.4 Configure break glass account
└── 3.5 Verify AWS API connectivity

Phase 4: SBC HA Deployment (via Stack Manager)
├── 4.1 Use Stack Manager to deploy SBC pair
├── 4.2 Stack Manager creates CloudFormation stack
├── 4.3 SBC instances deployed across AZs
├── 4.4 Virtual IPs configured in route tables
├── 4.5 Configure break glass accounts on both SBCs
├── 4.6 Install TLS certificates for Teams Direct Routing
└── 4.7 Verify HA failover functionality

Phase 5: ARM Deployment
├── 5.1 Deploy ARM Configurator (single instance)
├── 5.2 Configure ARM OAuth with Entra ID
├── 5.3 Configure ARM break glass account
├── 5.4 Deploy ARM Router(s)
├── 5.5 Configure ARM licensing
└── 5.6 Integrate ARM with SBCs

Phase 6: OVOC Deployment (Production only)
├── 6.1 Deploy OVOC EC2 instance
├── 6.2 Install public CA certificate on OVOC
├── 6.3 Configure OVOC networking
├── 6.4 Configure Microsoft Teams integration
├── 6.5 Configure break glass account
├── 6.6 Add SBCs to OVOC management
└── 6.7 Verify Teams QoE data ingestion

Phase 7: Teams Direct Routing Configuration
├── 7.1 Register SBC in Teams Admin Center
├── 7.2 Configure voice routing policies
├── 7.3 Configure PSTN usages
├── 7.4 Assign phone numbers to users
└── 7.5 Test end-to-end calling

Phase 8: Validation
├── 8.1 Test SBC HA failover
├── 8.2 Test OAuth authentication for all components
├── 8.3 Test break glass account access
├── 8.4 Verify ARM routing functionality
├── 8.5 Confirm OVOC visibility and Teams QoE data
└── 8.6 Document final configuration
```

### Deployment Methods by Component

| Component | Deployment Method | Source |
|-----------|------------------|--------|
| Stack Manager | AWS EC2 Console / CLI | AudioCodes AMI from AWS Marketplace |
| Mediant VE SBC | **Via Stack Manager only** (for HA) | Stack Manager orchestrates deployment |
| ARM Configurator | AWS EC2 Console using AudioCodes AMI | AWS Marketplace Community AMI |
| ARM Router | AWS EC2 Console using AudioCodes AMI | AWS Marketplace Community AMI |
| OVOC | AWS EC2 Console using AudioCodes AMI | AudioCodes provided AMI |

---

## High Availability Considerations

### SBC HA Architecture

| Aspect | Configuration |
|--------|---------------|
| Mode | 1+1 Active/Standby |
| Scope | Within single VPC, across two Availability Zones |
| Failover Trigger | Health check failure, manual trigger |
| Failover Mechanism | Stack Manager updates VPC route tables |
| Call Handling | Active IP calls maintained; PSTN calls dropped |

### What Happens During SBC Failover

1. **Active SBC fails** (detected via HA subnet heartbeat)
2. **Stack Manager detects failure**
3. **Stack Manager calls AWS EC2 API** to update route table
4. **Virtual IP route** changed from failed SBC's ENI to standby SBC's ENI
5. **Elastic IP** (if used) reassigned to standby SBC
6. **Standby becomes Active** and starts serving traffic

### ARM HA Architecture

| Aspect | Configuration |
|--------|---------------|
| Mode | Active-Active for Routers |
| Configurator | Single instance (no HA) |
| Failure Handling | Routers continue with last known configuration |

---

## IAM Permissions and Security

### Stack Manager IAM Policy

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:*",
                "cloudformation:*",
                "cloudwatch:DeleteAlarms",
                "cloudwatch:PutMetricAlarm",
                "iam:PassRole",
                "iam:ListInstanceProfiles",
                "iam:CreateServiceLinkedRole"
            ],
            "Resource": "*"
        }
    ]
}
```

### IAM Role Creation Steps

1. Navigate to AWS IAM Console > Policies > Create Policy
2. Select JSON tab and paste the policy above
3. Name the policy (e.g., `AudioCodes-StackManager-Policy`)
4. Navigate to Roles > Create Role
5. Select EC2 as the trusted entity
6. Attach the policy created above
7. Name the role (e.g., `AudioCodes-StackManager-Role`)
8. Attach this role to the Stack Manager EC2 instance

---

## Licensing Considerations

### Mediant VE SBC Licensing

| Model | Description | Procurement |
|-------|-------------|-------------|
| BYOL | Bring Your Own License | Purchase from AudioCodes, request via [BYOL form](https://online.audiocodes.com/aws-license) |
| PAYG | Pay-As-You-Go | Consumed via AWS Marketplace billing |

### ARM Licensing

- Obtained from AudioCodes
- Configured via ARM Configurator

### OVOC Licensing

- Obtained from AudioCodes
- Based on number of managed devices
- **Analytics license required for Teams QoE integration**

---

## References and Documentation

### Official AudioCodes Documentation

| Document | Version | URL |
|----------|---------|-----|
| Mediant VE SBC for AWS Installation Manual | 7.4 | [PDF](https://www.audiocodes.com/media/15887/mediant-virtual-edition-sbc-for-amazon-aws-installation-manual-ver-74.pdf) |
| Mediant VE SBC for AWS Installation Manual | 7.6 | [PDF](https://www.audiocodes.com/media/eiwnmvt1/mediant-virtual-edition-sbc-for-amazon-aws-installation-manual-ver-76.pdf) |
| Stack Manager User's Manual | 7.4 | [PDF](https://www.audiocodes.com/media/15907/stack-manager-for-mediant-ve-ce-sbc-users-manual-ver-74.pdf) |
| Stack Manager User's Manual | 7.6 | [PDF](https://www.audiocodes.com/media/etznhxaq/stack-manager-for-mediant-ve-ce-sbc-users-manual-ver-76.pdf) |
| ARM Installation Manual | 10.0 | [PDF](https://www.audiocodes.com/media/vgknljog/audiocodes-routing-manager-arm-installation-manual-ver-100.pdf) |
| ARM User's Manual | 9.8 | [Web](https://techdocs.audiocodes.com/arm/user-manual/version-980/) |
| ARM Azure AD Configuration | 10.0 | [Web](https://techdocs.audiocodes.com/arm/user-manual/version-10/Content/ARM%20UM/Configuring%20the%20ARM%20in%20the%20Azure%20Portal.htm) |
| OVOC IOM Manual | 8.2 | [PDF](https://www.audiocodes.com/media/zfkonbrb/one-voice-operations-center-iom-manual-ver-8-2.pdf) |
| OVOC Server Requirements | 8.4 | [Web](https://techdocs.audiocodes.com/one-voice-operations-center-ovoc/iom-manual/version-840/Content/OVOC%20IOM/OVOC%20Server%20Minimum%20Requirements.htm) |
| Configure Microsoft Graph API | - | [Web](https://techdocs.audiocodes.com/live/customer-all-um/Content/PS%20Installation/Step%202%20Configure%20Microsoft.htm) |
| SBC Teams Direct Routing Config | - | [PDF](https://www.audiocodes.com/media/13253/connecting-audiocodes-sbc-to-microsoft-teams-direct-routing-enterprise-model-configuration-note.pdf) |

### Microsoft Documentation

| Document | URL |
|----------|-----|
| Plan Direct Routing | [Microsoft Learn](https://learn.microsoft.com/en-us/microsoftteams/direct-routing-plan) |
| Connect SBC to Direct Routing | [Microsoft Learn](https://learn.microsoft.com/en-us/microsoftteams/direct-routing-connect-the-sbc) |
| Configure Direct Routing | [Microsoft Learn](https://learn.microsoft.com/en-us/microsoftteams/direct-routing-configure) |
| Direct Routing SIP Protocol | [Microsoft Learn](https://learn.microsoft.com/en-us/microsoftteams/direct-routing-protocols-sip) |
| Enable Users for Direct Routing | [Microsoft Learn](https://learn.microsoft.com/en-us/microsoftteams/direct-routing-enable-users) |
| Teams Administrator Roles | [Microsoft Learn](https://learn.microsoft.com/en-us/microsoftteams/using-admin-roles) |
| Microsoft Graph CallRecords API | [Microsoft Learn](https://learn.microsoft.com/en-us/graph/api/resources/callrecords-api-overview) |
| Microsoft Trusted Root Certificate Program | [Microsoft Learn](https://docs.microsoft.com/en-us/security/trusted-root/participants-list) |

### AudioCodes Product Pages

| Product | URL |
|---------|-----|
| Mediant VE SBC | [Product Page](https://www.audiocodes.com/solutions-products/products/session-border-controllers-sbcs/mediant-vese) |
| ARM | [Product Page](https://www.audiocodes.com/solutions-products/products/management-products-solutions/audiocodes-routing-manager) |
| OVOC | [Product Page](https://www.audiocodes.com/solutions-products/products/management-products-solutions/one-voice-operations-center) |

### AWS Marketplace

| Product | URL |
|---------|-----|
| Mediant VE SBC (BYOL) | [AWS Marketplace](https://aws.amazon.com/marketplace/pp/prodview-lzov3dr64koi2) |
| Mediant VE SBC (PAYG) | [AWS Marketplace](https://aws.amazon.com/marketplace/pp/prodview-4wxi3q2ixfcz2) |

### Third-Party References

| Source | URL |
|--------|-----|
| Enabling Teams QoE in OVOC | [Shawn Harry Blog](https://shawnharry.co.uk/2021/07/21/enabling-teams-qoe-reports-in-audiocodes-ovoc/) |
| Installing OVOC Guide | [CanUCThis](https://canucthis.com/2021/02/installing-and-configuring-audiocodes-one-voice-operations-center-ovoc/) |
| Teams Direct Routing Certificate Changes (2026) | [Erik365 Blog](https://erik365.blog/2025/12/18/upcoming-certificate-changes-for-microsoft-teams-direct-routing-and-operator-connect-june-2026/) |

---

## Appendix A: Deployment Checklist

### Pre-Deployment

- [ ] AWS Account access confirmed
- [ ] VPC and subnet design finalized
- [ ] Security groups designed and documented
- [ ] IAM policy and role created for Stack Manager
- [ ] Key pairs created
- [ ] AudioCodes licensing obtained (or PAYG decision made)
- [ ] Public CA certificates procured for SBCs and OVOC
- [ ] Domain registered and verified in Microsoft 365 tenant

### Microsoft Entra ID Configuration

- [ ] OVOC App Registration created
- [ ] ARM WebUI App Registration created
- [ ] ARM REST API App Registration created
- [ ] SBC App Registration created (if SBA required)
- [ ] All API permissions configured
- [ ] Admin consent granted for all app registrations
- [ ] All credentials documented securely

### Break Glass Accounts

- [ ] Secret repository structure created
- [ ] All break glass accounts created on appliances
- [ ] All passwords stored securely in secret repository
- [ ] Access procedures documented
- [ ] Dual-control access configured

### Component Deployment

- [ ] Stack Manager deployed and verified
- [ ] SBC HA pair deployed via Stack Manager
- [ ] TLS certificates installed on SBCs
- [ ] ARM Configurator deployed
- [ ] ARM Router(s) deployed
- [ ] OVOC deployed (production only)
- [ ] All break glass accounts tested

### Integration Verification

- [ ] OAuth authentication working for all components
- [ ] OVOC receiving Teams QoE data
- [ ] SBCs registered in Teams Admin Center
- [ ] End-to-end calling tested
- [ ] HA failover tested

---

## Appendix B: Credentials Reference Template

### App Registration Credentials

| App Registration | Tenant ID | Client ID | Secret Expiry |
|-----------------|-----------|-----------|---------------|
| AudioCodes-OVOC-Teams-Integration | `________` | `________` | `________` |
| AudioCodes-ARM-WebUI | `________` | `________` | `________` |
| AudioCodes-ARM-REST-API | `________` | `________` | `________` |
| AudioCodes-SBC-DirectRouting | `________` | `________` | `________` |

### Break Glass Account Reference

| Component | Username | Secret Path |
|-----------|----------|-------------|
| Stack Manager (Non-Prod) | `breakglass-stackmgr-nonprod` | `/audiocodes/nonprod/breakglass-stackmgr-nonprod` |
| ... | ... | ... |

**Note:** Never store actual credentials in this document. Use the secret repository paths to retrieve credentials when needed.

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | February 2026 | KS | Initial release |
| 2.0 | February 2026 | KS | Removed US from non-prod; Added Microsoft integration section; Added break glass accounts; Clarified HA scope |

---

**End of Document**
