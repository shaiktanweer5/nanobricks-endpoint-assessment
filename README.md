# Nanobricks Endpoint Assessment

A lightweight Windows endpoint assessment tool that collects system and security information, evaluates the device against a simple baseline, and presents results as PASS, REVIEW, or FAIL.

## Overview

Nanobricks Endpoint Assessment is designed for small businesses, offices, and authorized IT assessments where manually checking every Windows system becomes difficult as the number of endpoints grows.

The tool currently evaluates:

- Windows version
- System memory
- Disk capacity and available free space
- Microsoft Defender status
- Real-time protection
- Windows Firewall profiles
- Windows Update status
- Microsoft Office / Microsoft 365 installation
- Local Windows users
- Built-in Administrator status
- Basic account authentication review

## How It Works

The project is divided into four main components:

### collector.py

Collects endpoint information from the local Windows system using Python and PowerShell.

### assessor.py

Compares collected information against a baseline and generates:

- PASS
- REVIEW
- FAIL

Each finding also includes:

- Current value
- Expected value
- Recommended action

### report.py

Generates a structured JSON assessment report.

The generated file:

```text
endpoint-report.json
```

is excluded from Git because it may contain local system information.

### app.py

Provides a Streamlit dashboard for running the assessment and reviewing the results visually.

## Example Assessment

```text
PASS    Operating System
PASS    System Memory
FAIL    Disk Free Space
PASS    Microsoft Defender
PASS    Windows Firewall
REVIEW  Windows Update
PASS    Microsoft Office
REVIEW  Account Authentication
PASS    Built-in Administrator Account
```

## Requirements

- Windows 10/11
- Python 3
- PowerShell
- Microsoft Defender commands available on the endpoint

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Run from Command Line

Collect endpoint information:

```powershell
python collector.py
```

Run the assessment:

```powershell
python assessor.py
```

Generate the JSON report:

```powershell
python report.py
```

## Run the Web Dashboard

```powershell
python -m streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

Click:

**Run Endpoint Assessment**

## Current Baseline

| Check | Expected |
|---|---|
| Operating System | Windows 11 |
| Memory | 8 GB or higher |
| Disk Free Space | At least 15% free |
| Microsoft Defender | Enabled |
| Real-Time Protection | Enabled |
| Windows Firewall | Domain, Private and Public enabled |
| Windows Update | No pending updates |
| Microsoft Office | Installed where required |
| Built-in Administrator | Disabled when not required |
| User Authentication | Password, Windows Hello, PIN, or approved authentication |

## Security and Privacy

This tool is intended for systems that you own or are explicitly authorized to assess.

The tool does not intentionally collect user documents or file contents.

Generated endpoint reports may contain system details such as hostname, hardware information, software configuration, and local account information. These reports should be handled securely.

## Current Limitations

This is an early version intended for learning, demonstration, and small-scale endpoint assessment.

Current limitations include:

- Windows only
- Assessment is performed on the machine where the tool runs
- Windows Update check may take additional time
- Local account properties may not fully represent Microsoft Account or Windows Hello authentication
- No centralized multi-device management yet

## Roadmap

Planned improvements include:

- Better Windows edition and build detection
- Cleaner Defender signature date handling
- Software inventory
- Office update posture
- Security baseline customization
- Endpoint scoring
- HTML / PDF reporting
- Multi-device assessment
- Central dashboard
- Agent-based endpoint collection
- Export to CSV
- Remediation tracking
- Organization-level endpoint inventory

## Use Case

The project was created to demonstrate how manual endpoint checks can be converted into a repeatable assessment workflow.

Instead of manually inspecting every device, the goal is:

```text
Endpoint
   ↓
Data Collection
   ↓
Baseline Evaluation
   ↓
PASS / REVIEW / FAIL
   ↓
Recommended Action
   ↓
Structured Report / Dashboard
```

## Project Structure

```text
nanobricks-endpoint-assessment/
│
├── collector.py
├── assessor.py
├── report.py
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Future Direction

The long-term goal is to evolve this project from a single-endpoint assessment utility into a lightweight centralized endpoint assessment platform for small businesses.

A future architecture could look like:

```text
Windows Endpoints
        ↓
Lightweight Collector
        ↓
Secure Assessment API
        ↓
Central Nanobricks Dashboard
        ↓
Organization Device Inventory
        ↓
Security Findings
        ↓
Remediation Tracking
```

The focus is not to replace enterprise endpoint management platforms, but to provide a simple, understandable assessment workflow for smaller environments that may not have dedicated security tooling.

## Disclaimer

This project is an independent endpoint assessment and learning tool.

It is not a replacement for enterprise endpoint management, EDR, MDM, vulnerability management, or commercial endpoint security platforms.

Use only on systems you are authorized to assess.
