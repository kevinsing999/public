# AudioCodes AWS Deployment Guide

## Cloud Operations & Project Team Reference Document

**Document Version:** 1.0
**Date:** February 2026
**Classification:** Internal Use

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Critical Finding: Stack Manager Requirement for Cross-AZ HA](#critical-finding-stack-manager-requirement-for-cross-az-ha)
3. [Architecture Overview](#architecture-overview)
4. [Component Specifications](#component-specifications)
5. [Non-Production Environment Deployment](#non-production-environment-deployment)
6. [Production Environment Deployment](#production-environment-deployment)
7. [AWS Infrastructure Requirements](#aws-infrastructure-requirements)
8. [Deployment Methodology](#deployment-methodology)
9. [High Availability Considerations](#high-availability-considerations)
10. [Network Architecture](#network-architecture)
11. [IAM Permissions and Security](#iam-permissions-and-security)
12. [Licensing Considerations](#licensing-considerations)
13. [References and Documentation](#references-and-documentation)

---

## Executive Summary

This document provides deployment guidance for the AudioCodes voice infrastructure stack on Amazon Web Services (AWS). It covers the deployment of:

- **Mediant Virtual Edition (VE) Session Border Controllers (SBCs)** in High Availability configuration
- **AudioCodes Stack Manager** for HA lifecycle management
- **AudioCodes Routing Manager (ARM)** for centralized call routing
- **AudioCodes One Voice Operations Center (OVOC)** for management and monitoring

**Key Takeaway:** The AudioCodes Stack Manager is a **mandatory component** for deploying Mediant VE SBCs in High Availability across multiple Availability Zones. This is not optional—it is the mechanism by which failover is achieved through VPC route table manipulation.

---

## Critical Finding: Stack Manager Requirement for Cross-AZ HA

### Why Stack Manager is Required

When deploying AudioCodes Mediant VE SBCs in High Availability across two Availability Zones in AWS, the **Stack Manager is a mandatory separate VM** that performs the following critical functions:

1. **Route Table Manipulation:** During failover, the Stack Manager updates AWS VPC route table entries to redirect traffic from the failed Active SBC to the Standby SBC.

2. **Virtual IP Address Management:** The Stack Manager allocates and manages Virtual IP addresses (by default from the `169.254.64.0/24` subnet) that exist outside the VPC CIDR range. These Virtual IPs are used for traffic that traverses AWS Transit Gateway or communicates with external networks.

3. **Cluster Lifecycle Management:** The Stack Manager handles initial deployment, topology updates, and "stack healing" in case of underlying cloud resource corruption.

### How the Failover Mechanism Works

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AWS VPC                                          │
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

### Virtual IP Address Mechanism

1. **Virtual IP addresses are special IP addresses that must reside outside the VPC address space.** The Stack Manager allocates them by default from `169.254.64.0/24`.

2. **Stack Manager "plugs" these Virtual IP addresses into AWS route tables** attached to the corresponding network interfaces of both deployed SBC instances.

3. **During switchover:** The route destination for the Virtual IP is updated from the Active SBC's ENI to the (former) Standby SBC's ENI.

4. **For cross-VPC communication:** Regular VPC peering does NOT support Virtual IP addresses. You MUST use AWS Transit Gateway.

### API Access Requirements

The Stack Manager requires **internet access** (via Internet Gateway or NAT Gateway) to communicate with AWS APIs:
- EC2 API
- CloudFormation API
- IAM API
- Elastic Load Balancing API (if using NLB)

---

## Architecture Overview

### Non-Production Environment

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
│  │   │  ARM Configurator        │    │  ARM Router #1           │          │   │
│  │   │  (m4.xlarge)             │    │  (m4.large)              │          │   │
│  │   │  Single Instance         │    │  Active-Active HA        │          │   │
│  │   └──────────────────────────┘    └──────────────────────────┘          │   │
│  │                                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        UNITED STATES REGION (us-east-1)                  │   │
│  │                                                                          │   │
│  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐  │   │
│  │   │ Mediant VE   │    │ Mediant VE   │    │  ARM Router #2           │  │   │
│  │   │ SBC #1       │◄──►│ SBC #2       │    │  (m4.large)              │  │   │
│  │   │ (AZ-A)       │    │ (AZ-B)       │    │  Active-Active HA        │  │   │
│  │   │ Active       │    │ Standby      │    │  (with AUS Router)       │  │   │
│  │   └──────────────┘    └──────────────┘    └──────────────────────────┘  │   │
│  │                                                                          │   │
│  │   NOTE: Stack Manager Required for US SBCs if cross-AZ HA is deployed   │   │
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
│  │   │  (m5.2xlarge or m5.4xlarge)  │    │  (m4.xlarge)             │      │   │
│  │   │  Device Manager included     │    │                          │      │   │
│  │   └──────────────────────────────┘    └──────────────────────────┘      │   │
│  │                                                                          │   │
│  │   ┌──────────────────────────┐                                          │   │
│  │   │  ARM Router               │                                          │   │
│  │   │  (m4.large)               │                                          │   │
│  │   │  Active-Active with US    │                                          │   │
│  │   └──────────────────────────┘                                          │   │
│  │                                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        UNITED STATES REGION (us-east-1/us-west-2)        │   │
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
│  │   │  Active-Active with AUS   │                                          │   │
│  │   └──────────────────────────┘                                          │   │
│  │                                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. Mediant Virtual Edition (VE) SBC

| Specification | Details |
|--------------|---------|
| **Purpose** | Session Border Controller for SIP trunking, security, media handling |
| **HA Mode** | 1+1 Active/Standby across Availability Zones |
| **Minimum Version for Cross-AZ HA** | Version 7.4.500 |
| **Deployment Method** | Via Stack Manager (required for multi-AZ HA) |

#### Recommended EC2 Instance Types

| Use Case | Instance Type | vCPUs | Memory | Notes |
|----------|--------------|-------|--------|-------|
| Without Transcoding | m5.large | 2 | 8 GiB | Basic SIP proxy |
| Without Transcoding (Higher capacity) | r4.large | 2 | 15.25 GiB | Memory optimized |
| With Transcoding | c5.2xlarge | 8 | 16 GiB | Compute optimized for DSP |
| With Transcoding (High capacity) | c5.9xlarge | 36 | 72 GiB | High session count with transcoding |

**Note:** Refer to the [SBC Series Release Notes](https://www.audiocodes.com/solutions-products/products/session-border-controllers-sbcs/mediant-vese) for exact session capacity per instance type.

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
| **Router** | m4.large | 2 | 8 GiB | 2+ (Active-Active HA) |
| **Router (>1M users)** | m4.large (16GB RAM) | 2 | 16 GiB | 2+ |

#### Deployment Requirements

- **All ARM VMs must be in the same VPC and subnet**
- Configurator: Single instance only
- Router: Deploy minimum 2 for HA (Active-Active, NOT Active-Standby)
- Security Group: Allow all outgoing traffic, incoming from VPC, SSH/HTTP/HTTPS from enterprise subnets

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

---

## Non-Production Environment Deployment

### Component Inventory

| Component | Region | Quantity | Instance Type | Purpose |
|-----------|--------|----------|---------------|---------|
| Mediant VE SBC | AUS (ap-southeast-2) | 2 | m5.large or c5.2xlarge | HA Pair across AZs |
| Stack Manager | AUS (ap-southeast-2) | 1 | t3.medium | HA Management |
| Mediant VE SBC | US (us-east-1) | 2 | m5.large or c5.2xlarge | HA Pair across AZs |
| **Stack Manager** | **US (us-east-1)** | **1** | **t3.medium** | **HA Management (MISSING FROM ORIGINAL PLAN)** |
| ARM Configurator | AUS (ap-southeast-2) | 1 | m4.xlarge | Routing configuration |
| ARM Router | AUS (ap-southeast-2) | 1 | m4.large | Call routing |
| ARM Router | US (us-east-1) | 1 | m4.large | Call routing |

### Critical Gap Identified

**Your non-production plan is missing a Stack Manager for the US region.** If you intend to deploy SBCs in HA across two Availability Zones in the US region, you **must** deploy a Stack Manager in that region as well.

---

## Production Environment Deployment

### Component Inventory

| Component | Region | Quantity | Instance Type | Purpose |
|-----------|--------|----------|---------------|---------|
| Mediant VE SBC | AUS (ap-southeast-2) | 2 | m5.large or c5.2xlarge | HA Pair across AZs |
| Stack Manager | AUS (ap-southeast-2) | 1 | t3.medium | HA Management |
| OVOC | AUS (ap-southeast-2) | 1 | m5.2xlarge | Management & Monitoring |
| ARM Configurator | AUS (ap-southeast-2) | 1 | m4.xlarge | Routing configuration |
| ARM Router | AUS (ap-southeast-2) | 1 | m4.large | Call routing |
| Mediant VE SBC | US | 2 | m5.large or c5.2xlarge | HA Pair across AZs |
| Stack Manager | US | 1 | t3.medium | HA Management |
| ARM Router | US | 1 | m4.large | Call routing |

### Note on Device Manager

OVOC includes Device Manager functionality. A separate "Device Manager" deployment is not required—it is part of OVOC.

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
│  - Used by Stack Manager for failover routing                               │
│  - Plugged into route tables pointing to active SBC ENI                    │
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
| Outbound | All | All | 0.0.0.0/0 | All traffic |

---

## Deployment Methodology

### Deployment Sequence

```
Phase 1: Infrastructure Preparation
├── 1.1 Create VPC and Subnets (if not existing)
├── 1.2 Create Internet Gateway / NAT Gateway
├── 1.3 Create Security Groups
├── 1.4 Create IAM Role for Stack Manager
└── 1.5 Create Key Pairs

Phase 2: Stack Manager Deployment
├── 2.1 Deploy Stack Manager EC2 instance (t3.medium)
├── 2.2 Attach IAM Role to Stack Manager
├── 2.3 Configure Stack Manager networking
└── 2.4 Verify AWS API connectivity

Phase 3: SBC HA Deployment (via Stack Manager)
├── 3.1 Use Stack Manager to deploy SBC pair
├── 3.2 Stack Manager creates CloudFormation stack
├── 3.3 SBC instances deployed across AZs
├── 3.4 Virtual IPs configured in route tables
└── 3.5 Verify HA failover functionality

Phase 4: ARM Deployment
├── 4.1 Deploy ARM Configurator (single instance)
├── 4.2 Deploy ARM Router #1
├── 4.3 Deploy ARM Router #2 (for HA)
├── 4.4 Configure ARM licensing
└── 4.5 Integrate ARM with SBCs

Phase 5: OVOC Deployment (Production only)
├── 5.1 Deploy OVOC EC2 instance
├── 5.2 Configure OVOC networking
├── 5.3 Add SBCs to OVOC management
├── 5.4 Configure Device Manager
└── 5.5 Set up monitoring and alerting

Phase 6: Validation
├── 6.1 Test SBC HA failover
├── 6.2 Verify ARM routing functionality
├── 6.3 Confirm OVOC visibility
└── 6.4 Document final configuration
```

### Deployment Methods by Component

| Component | Deployment Method | Source |
|-----------|------------------|--------|
| Stack Manager | AWS EC2 Console / CLI | AudioCodes AMI from AWS Marketplace |
| Mediant VE SBC | **Via Stack Manager only** (for HA) | Stack Manager orchestrates deployment |
| ARM Configurator | AWS EC2 Console using AudioCodes AMI | AWS Marketplace Community AMI |
| ARM Router | AWS EC2 Console using AudioCodes AMI | AWS Marketplace Community AMI |
| OVOC | AWS EC2 Console using AudioCodes AMI | AudioCodes provided AMI |

**Important:** For multi-AZ HA SBC deployment, you **cannot** use the CloudFormation template directly. You **must** use Stack Manager.

---

## High Availability Considerations

### SBC HA Architecture

| Aspect | Configuration |
|--------|---------------|
| Mode | 1+1 Active/Standby |
| Failover Trigger | Health check failure, manual trigger |
| Failover Mechanism | Stack Manager updates VPC route tables |
| Call Handling | Active IP calls maintained; PSTN calls dropped |
| Virtual IP Movement | Stack Manager redirects Virtual IP routes to new active |
| Elastic IP Movement | Transferred to new active SBC |

### What Happens During SBC Failover

1. **Active SBC fails** (detected via HA subnet heartbeat)
2. **Stack Manager detects failure**
3. **Stack Manager calls AWS EC2 API** to update route table
4. **Virtual IP route** changed from failed SBC's ENI to standby SBC's ENI
5. **Elastic IP** (if used) reassigned to standby SBC
6. **Standby becomes Active** and starts serving traffic
7. **Active IP calls are maintained** (signaling and media)

### ARM HA Architecture

| Aspect | Configuration |
|--------|---------------|
| Mode | Active-Active (NOT Active-Standby) |
| Routers | Deploy minimum 2 routers |
| Configurator | Single instance (no HA for Configurator) |
| Failure Handling | Routers continue serving with last known configuration |

### OVOC HA Considerations

- OVOC is typically deployed as a single instance
- For HA, consider deploying in a resilient architecture with regular backups
- Cross-region OVOC deployment is not standard—usually centralized

---

## Network Architecture

### Cross-Region Connectivity

#### AWS Transit Gateway Requirement

**Critical:** If SBCs need to communicate across VPCs (same region or cross-region) using Virtual IP addresses, you **must** use AWS Transit Gateway. Regular VPC peering does **NOT** support Virtual IP addresses.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Cross-Region Architecture                            │
│                                                                             │
│  ┌────────────────────────┐        ┌────────────────────────┐              │
│  │   AUS Region           │        │   US Region            │              │
│  │   (ap-southeast-2)     │        │   (us-east-1)          │              │
│  │                        │        │                        │              │
│  │  ┌──────────────────┐  │        │  ┌──────────────────┐  │              │
│  │  │ Transit Gateway  │◄─┼────────┼─►│ Transit Gateway  │  │              │
│  │  │ (ap-southeast-2) │  │Peering │  │ (us-east-1)      │  │              │
│  │  └────────┬─────────┘  │        │  └────────┬─────────┘  │              │
│  │           │            │        │           │            │              │
│  │  ┌────────▼─────────┐  │        │  ┌────────▼─────────┐  │              │
│  │  │ VPC (SBC + ARM)  │  │        │  │ VPC (SBC + ARM)  │  │              │
│  │  │                  │  │        │  │                  │  │              │
│  │  │ Virtual IPs:     │  │        │  │ Virtual IPs:     │  │              │
│  │  │ 169.254.64.1-2   │  │        │  │ 169.254.65.1-2   │  │              │
│  │  └──────────────────┘  │        │  └──────────────────┘  │              │
│  │                        │        │                        │              │
│  └────────────────────────┘        └────────────────────────┘              │
│                                                                             │
│  Transit Gateway Route Tables must include routes for Virtual IP ranges    │
│  pointing to the appropriate VPC attachment                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Network Load Balancer Alternative

Instead of Virtual IP addresses, you can use AWS Network Load Balancer (NLB):

| Option | Use Case | Pros | Cons |
|--------|----------|------|------|
| Virtual IP + Route Tables | Cross-VPC via Transit Gateway | No additional cost | Requires TGW for cross-VPC |
| Internal NLB | Intra-VPC traffic | AWS managed, highly available | Additional cost |
| Public NLB | Internet-facing traffic | Replaces Elastic IPs | Additional cost |

**AudioCodes Recommendation:** Internal NLB is recommended for deployments where NLB is preferred over Virtual IP addresses.

---

## IAM Permissions and Security

### Stack Manager IAM Policy

Create an IAM Policy with the following permissions:

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

#### Additional Permission for NLB Deployments

If using Network Load Balancer, add:

```json
{
    "Effect": "Allow",
    "Action": [
        "elasticloadbalancing:*"
    ],
    "Resource": "*"
}
```

### IAM Role Creation Steps

1. Navigate to AWS IAM Console → Policies → Create Policy
2. Select JSON tab and paste the policy above
3. Name the policy (e.g., `AudioCodes-StackManager-Policy`)
4. Navigate to Roles → Create Role
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

#### PAYG Metering Dimensions

- Call minutes (standard)
- Transcoding minutes (additional)
- Recording minutes (additional)

### ARM Licensing

- Obtained from AudioCodes
- Configured via ARM Configurator

### OVOC Licensing

- Obtained from AudioCodes
- Based on number of managed devices

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
| ARM User's Manual | 8.2 | [PDF](https://www.audiocodes.com/media/13441/arm-users-manual-ver-82.pdf) |
| OVOC IOM Manual | 8.2 | [PDF](https://www.audiocodes.com/media/zfkonbrb/one-voice-operations-center-iom-manual-ver-8-2.pdf) |
| OVOC Server Requirements | 8.4 | [Web](https://techdocs.audiocodes.com/one-voice-operations-center-ovoc/iom-manual/version-840/Content/OVOC%20IOM/OVOC%20Server%20Minimum%20Requirements.htm) |
| Device Manager Deployment Guide | 8.2 | [PDF](https://www.audiocodes.com/media/10xnige0/device-manager-deployment-guide-v82.pdf) |

### AudioCodes Product Pages

| Product | URL |
|---------|-----|
| Mediant VE SBC | [Product Page](https://www.audiocodes.com/solutions-products/products/session-border-controllers-sbcs/mediant-vese) |
| Mediant VE SBC on AWS | [AWS Solution](https://www.audiocodes.com/solutions-products/public-clouds/solutions-for-amazon-web-services-aws/mediant-ve-session-border-controller-sbc-on-aws) |
| ARM | [Product Page](https://www.audiocodes.com/solutions-products/products/management-products-solutions/audiocodes-routing-manager) |
| OVOC | [Product Page](https://www.audiocodes.com/solutions-products/products/management-products-solutions/one-voice-operations-center) |

### AWS Marketplace

| Product | URL |
|---------|-----|
| Mediant VE SBC (BYOL) | [AWS Marketplace](https://aws.amazon.com/marketplace/pp/prodview-lzov3dr64koi2) |
| Mediant VE SBC (PAYG) | [AWS Marketplace](https://aws.amazon.com/marketplace/pp/prodview-4wxi3q2ixfcz2) |
| AudioCodes Seller Profile | [AWS Marketplace](https://aws.amazon.com/marketplace/seller-profile?id=7b9276f4-6534-45d6-aa96-ea518cdf0b75) |

### AudioCodes Technical Documentation Portal

- [TechDocs Portal](https://techdocs.audiocodes.com/)
- [HA Overview](https://techdocs.audiocodes.com/session-border-controller-sbc/mediant-800-sbc/user-manual/version-760/Content/UM/HA-Overview.htm)

---

## Appendix A: Deployment Checklist

### Pre-Deployment

- [ ] AWS Account access confirmed for both regions
- [ ] VPC and subnet design finalized
- [ ] CIDR ranges confirmed (no overlap)
- [ ] Internet Gateway or NAT Gateway available for Stack Manager
- [ ] Key pairs created for each region
- [ ] IAM policy and role created for Stack Manager
- [ ] Security groups designed and documented
- [ ] AudioCodes licensing obtained (or PAYG decision made)
- [ ] AMI IDs obtained from AudioCodes for OVOC (region-specific)

### Stack Manager Deployment

- [ ] EC2 instance launched (t3.medium)
- [ ] IAM role attached
- [ ] Security group applied
- [ ] Network connectivity verified (can reach AWS APIs)
- [ ] Stack Manager accessible via SSH/HTTPS

### SBC HA Deployment

- [ ] SBC pair deployed via Stack Manager
- [ ] Both SBCs in different AZs
- [ ] HA subnet communication verified
- [ ] Virtual IPs configured in route tables
- [ ] Failover tested successfully
- [ ] SBC licensing applied

### ARM Deployment

- [ ] Configurator deployed
- [ ] Router #1 deployed
- [ ] Router #2 deployed (same VPC/subnet as Configurator)
- [ ] All VMs can communicate
- [ ] ARM licensing applied
- [ ] SBCs registered with ARM

### OVOC Deployment (Production)

- [ ] OVOC instance deployed
- [ ] OVOC accessible via HTTPS
- [ ] SBCs added to OVOC
- [ ] Device Manager configured
- [ ] SNMP traps verified
- [ ] Monitoring dashboards configured

### Post-Deployment Validation

- [ ] End-to-end call test successful
- [ ] HA failover test documented
- [ ] ARM routing test completed
- [ ] OVOC monitoring verified
- [ ] Documentation updated with actual IPs and configurations

---

## Appendix B: Troubleshooting

### Stack Manager Cannot Access AWS APIs

**Symptom:** Stack Manager deployment fails or cannot manage SBCs

**Cause:** No internet access for API calls

**Solution:**
1. Verify Internet Gateway or NAT Gateway is attached to subnet
2. Verify route table has route to IGW/NAT
3. Verify security group allows outbound HTTPS (443)

### Virtual IP Addresses Not Working

**Symptom:** Traffic doesn't reach SBC via Virtual IP after failover

**Cause:** Route table not updated or Transit Gateway not configured

**Solution:**
1. Check VPC route table for Virtual IP entry
2. Verify Stack Manager has IAM permissions
3. If cross-VPC: Verify Transit Gateway configuration
4. If using VPC peering: This is not supported—migrate to Transit Gateway

### ARM Routers Cannot Connect to Configurator

**Symptom:** ARM Routers show disconnected in Configurator

**Cause:** Network connectivity or security group issue

**Solution:**
1. Verify all ARM VMs are in same VPC and subnet
2. Check security group allows internal VPC traffic
3. Verify no NACLs blocking traffic

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | February 2026 | Cloud Operations Team | Initial release |

---

**End of Document**
