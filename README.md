# Nanobricks Endpoint Assessment

A simple Windows endpoint assessment tool that collects system and security information, checks it against a basic baseline, and creates a consolidated Excel report.

## What It Does

The tool can be used on one or many Windows computers.

For each computer, it collects information such as:

- Windows version
- Processor and architecture
- RAM
- Disk size and free space
- Microsoft Defender status
- Real-time protection
- Windows Firewall status
- Pending Windows Updates
- Microsoft Office / Microsoft 365 information
- Local Windows users
- Local administrator accounts

The collected information is then checked against a simple endpoint baseline and marked as:

- **PASS** - meets the expected baseline
- **REVIEW** - needs verification or attention
- **FAIL** - does not meet the expected baseline

## Simple Workflow

```text
Windows PC
   ↓
Nanobricks Endpoint Collector
   ↓
Collect system and security information
   ↓
Check against endpoint baseline
   ↓
Create <PC-NAME>-assessment.json
   ↓
Collect JSON files from all computers
   ↓
Run build_excel_report.py
   ↓
Nanobricks_Endpoint_Assessment.xlsx
```

The same process can be used for 1, 10, 100, or more endpoints.

## Main Components

### `collector.py`

Collects Windows system and security information using Python and PowerShell.

### `assessor.py`

Checks the collected information against the endpoint baseline and creates PASS, REVIEW, and FAIL findings.

### `endpoint_agent.py`

Runs the collector and assessment together and creates an endpoint JSON file.

Example:

```text
endpoint-data\PC-01-assessment.json
```

### `build_excel_report.py`

Reads all endpoint assessment JSON files inside:

```text
endpoint-data\
```

and creates:

```text
Nanobricks_Endpoint_Assessment.xlsx
```

### `app.py`

Optional Streamlit dashboard for viewing a single endpoint assessment.

### `central_dashboard.py`

Optional dashboard for viewing multiple endpoint assessments.

## Portable Windows Collector

The collector can be packaged as a Windows executable using PyInstaller.

Example:

```text
NanobricksEndpointCollector.exe
```

The customer computer does not need Python installed when using the packaged executable.

When the executable runs, it creates:

```text
endpoint-data\
    <PC-NAME>-assessment.json
```

beside the executable.

## Excel Report

The generated Excel workbook contains four sheets.

### Endpoint Inventory

One row per computer with system, security, patching, Office, account, and assessment information.

### Assessment Summary

Shows PASS, REVIEW, FAIL, total checks, and overall status for each endpoint.

### Findings

Shows each individual check with:

- Status
- Category
- Current value
- Expected value
- Recommended action

### Local Users

Shows local Windows users, account status, password-required information, and administrator membership.

## Current Baseline

| Check | Expected |
|---|---|
| Operating System | Windows 11 |
| RAM | 8 GB or higher |
| Disk Free Space | At least 15% free |
| Microsoft Defender | Enabled |
| Real-Time Protection | Enabled |
| Windows Firewall | Domain, Private, and Public profiles enabled |
| Windows Update | No pending updates |
| Microsoft Office | Installed where required |
| Built-in Administrator | Disabled when not required |
| User Authentication | Password, Windows Hello, PIN, or approved authentication |

## Install Dependencies

For development:

```powershell
python -m pip install -r requirements.txt
```

## Run the Endpoint Collector with Python

```powershell
python .\endpoint_agent.py
```

Example output:

```text
=================================================================
NANOBRICKS ENDPOINT COLLECTOR
=================================================================
Hostname: PC-01
Operating System: Windows 11
-----------------------------------------------------------------
PASS:   7
REVIEW: 1
FAIL:   1
TOTAL:  9
-----------------------------------------------------------------
Assessment file created:
...\endpoint-data\PC-01-assessment.json
=================================================================
```

## Build the Windows EXE

Install PyInstaller:

```powershell
python -m pip install pyinstaller
```

Build:

```powershell
python -m PyInstaller --onefile --clean --name NanobricksEndpointCollector endpoint_agent.py
```

The executable will be created at:

```text
dist\NanobricksEndpointCollector.exe
```

## Generate the Master Excel Report

Place all endpoint JSON files inside:

```text
endpoint-data\
```

Example:

```text
endpoint-data\
    PC-01-assessment.json
    PC-02-assessment.json
    PC-03-assessment.json
```

Then run:

```powershell
python .\build_excel_report.py
```

Output:

```text
Nanobricks_Endpoint_Assessment.xlsx
```

Open it with:

```powershell
start .\Nanobricks_Endpoint_Assessment.xlsx
```

## Optional Dashboard

Run the Streamlit dashboard:

```powershell
python -m streamlit run app.py
```

or the multi-endpoint dashboard:

```powershell
python -m streamlit run central_dashboard.py
```

## Project Structure

```text
nanobricks-endpoint-assessment/
│
├── collector.py
├── assessor.py
├── endpoint_agent.py
├── build_excel_report.py
├── report.py
├── app.py
├── central_dashboard.py
├── api_server.py
├── database.py
├── requirements.txt
├── .gitignore
└── README.md
```

Generated reports, local databases, build folders, and endpoint data are excluded from Git.

## Security and Privacy

Use this tool only on systems you own or are authorized to assess.

The tool does not intentionally read user documents or file contents.

Endpoint reports may contain:

- Hostname
- Hardware information
- Windows configuration
- Security configuration
- Office information
- Local account names

These reports should be stored and shared securely.

## Current Scope

Version 1 focuses on:

- Local Windows endpoint assessment
- Offline JSON output
- PASS / REVIEW / FAIL evaluation
- Multi-endpoint Excel consolidation
- Portable Windows executable
- Optional dashboards

The API and database components in the repository are experimental and are not required for the current offline Excel workflow.

## Future Improvements

Possible future improvements include:

- Better Windows edition and build detection
- Software inventory
- Improved Office update and licensing checks
- Custom assessment baselines
- HTML / PDF reports
- Centralized endpoint collection
- Authentication and organization-level dashboards
- Remediation tracking

## Disclaimer

Nanobricks Endpoint Assessment is a lightweight assessment utility.

It is not a replacement for enterprise EDR, MDM, vulnerability management, patch management, or endpoint security platforms.

Use only on systems you are authorized to assess.
