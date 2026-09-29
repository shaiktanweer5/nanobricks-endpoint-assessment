import json
from pathlib import Path

import requests
import streamlit as st

LOCAL_DATA_DIR = Path("endpoint-data")
API_URL = "http://127.0.0.1:8000/api/endpoints"

st.set_page_config(
    page_title="Nanobricks Endpoint Central Dashboard",
    page_icon="🖥️",
    layout="wide"
)

st.title("🖥️ Nanobricks Endpoint Central Dashboard")
st.write(
    "Central view of endpoint assessment results collected "
    "from multiple Windows systems."
)

def load_local_reports():
    reports = []

    if not LOCAL_DATA_DIR.exists():
        return reports

    for file_path in LOCAL_DATA_DIR.glob("*-assessment.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                report = json.load(file)

            report["_source_file"] = file_path.name
            report["_source_type"] = "Local"
            reports.append(report)

        except Exception:
            continue

    return reports


def load_api_reports():
    try:
        response = requests.get(
            API_URL,
            timeout=5
        )

        if response.status_code != 200:
            return [], (
                f"API returned status "
                f"{response.status_code}"
            )

        data = response.json()
        reports = data.get("endpoints", [])

        for report in reports:
            report["_source_type"] = "Database API"

        return reports, None

    except requests.RequestException as error:
        return [], str(error)


def load_uploaded_reports(uploaded_files):
    reports = []

    for uploaded_file in uploaded_files:
        try:
            uploaded_file.seek(0)
            report = json.load(uploaded_file)

            report["_source_file"] = uploaded_file.name
            report["_source_type"] = "Uploaded"

            reports.append(report)

        except Exception:
            st.error(
                f"Unable to read: {uploaded_file.name}"
            )

    return reports


st.subheader("Import Endpoint Assessments")

st.write(
    "Endpoint data is loaded automatically from the "
    "Nanobricks Endpoint API. You can also upload JSON "
    "assessment files manually when needed."
)

uploaded_files = st.file_uploader(
    "Upload endpoint assessment files",
    type=["json"],
    accept_multiple_files=True
)

local_reports = load_local_reports()
api_reports, api_error = load_api_reports()

uploaded_reports = []

if uploaded_files:
    uploaded_reports = load_uploaded_reports(
        uploaded_files
    )

if api_error:
    st.warning(
        "Central API is currently unavailable. "
        "Local or uploaded assessment files will still be shown."
    )

    with st.expander("API connection details"):
        st.write(api_error)

else:
    st.success(
        f"Connected to Nanobricks Endpoint API. "
        f"{len(api_reports)} endpoint(s) loaded from database."
    )

all_reports = (
    local_reports
    + api_reports
    + uploaded_reports
)

reports_by_hostname = {}

for report in all_reports:
    hostname = report.get(
        "endpoint",
        {}
    ).get(
        "hostname",
        "Unknown"
    )

    reports_by_hostname[hostname] = report

reports = list(
    reports_by_hostname.values()
)

if not reports:
    st.warning(
        "No endpoint assessment data is available."
    )

    st.write(
        "Run endpoint_agent.py on a Windows endpoint, "
        "submit data through the API, or upload an "
        "assessment JSON file."
    )

else:
    total_devices = len(reports)

    total_pass = sum(
        report.get("summary", {}).get("pass", 0)
        for report in reports
    )

    total_review = sum(
        report.get("summary", {}).get("review", 0)
        for report in reports
    )

    total_fail = sum(
        report.get("summary", {}).get("fail", 0)
        for report in reports
    )

    st.subheader("Organization Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Endpoints", total_devices)
    col2.metric("PASS", total_pass)
    col3.metric("REVIEW", total_review)
    col4.metric("FAIL", total_fail)

    st.subheader("Endpoint Inventory")

    inventory = []

    for report in reports:
        endpoint = report.get("endpoint", {})
        summary = report.get("summary", {})

        inventory.append(
            {
                "Hostname": endpoint.get("hostname", "N/A"),
                "Operating System": endpoint.get(
                    "operating_system",
                    "N/A"
                ),
                "RAM (GB)": str(
                    endpoint.get(
                        "ram_gb",
                        "N/A"
                    )
                ),
                "Disk Free (GB)": str(
                    endpoint.get(
                        "disk_free_gb",
                        "N/A"
                    )
                ),
                "PASS": summary.get("pass", 0),
                "REVIEW": summary.get("review", 0),
                "FAIL": summary.get("fail", 0),
                "Source": report.get(
                    "_source_type",
                    "Unknown"
                )
            }
        )

    st.dataframe(
        inventory,
        width="stretch",
        hide_index=True
    )

    st.subheader("Endpoint Details")

    endpoint_names = [
        report.get(
            "endpoint",
            {}
        ).get(
            "hostname",
            "Unknown"
        )
        for report in reports
    ]

    selected_endpoint = st.selectbox(
        "Select endpoint",
        endpoint_names
    )

    selected_report = None

    for report in reports:
        hostname = report.get(
            "endpoint",
            {}
        ).get("hostname")

        if hostname == selected_endpoint:
            selected_report = report
            break

    if selected_report:
        endpoint = selected_report.get(
            "endpoint",
            {}
        )

        summary = selected_report.get(
            "summary",
            {}
        )

        st.write(
            f"### {endpoint.get('hostname', 'Unknown')}"
        )

        st.caption(
            f"Source: "
            f"{selected_report.get('_source_type', 'Unknown')}"
        )

        col1, col2, col3 = st.columns(3)

        col1.write("**Operating System**")
        col1.write(
            endpoint.get(
                "operating_system",
                "N/A"
            )
        )

        col2.write("**RAM**")
        col2.write(
            f"{endpoint.get('ram_gb', 'N/A')} GB"
        )

        col3.write("**Disk Free**")
        col3.write(
            f"{endpoint.get('disk_free_gb', 'N/A')} GB"
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "PASS",
            summary.get("pass", 0)
        )

        col2.metric(
            "REVIEW",
            summary.get("review", 0)
        )

        col3.metric(
            "FAIL",
            summary.get("fail", 0)
        )

        st.write("### Findings")

        findings = selected_report.get(
            "findings",
            []
        )

        findings_table = []

        for finding in findings:
            findings_table.append(
                {
                    "Status": finding.get(
                        "status",
                        "N/A"
                    ),
                    "Check": finding.get(
                        "check",
                        "N/A"
                    ),
                    "Category": finding.get(
                        "category",
                        "N/A"
                    ),
                    "Current": finding.get(
                        "current_value",
                        "N/A"
                    ),
                    "Expected": finding.get(
                        "expected",
                        "N/A"
                    )
                }
            )

        st.dataframe(
            findings_table,
            width="stretch",
            hide_index=True
        )

        st.write("### Recommended Actions")

        actionable_findings = [
            finding
            for finding in findings
            if finding.get("status")
            in ["REVIEW", "FAIL"]
        ]

        if not actionable_findings:
            st.success(
                "No remediation actions required."
            )

        else:
            for finding in actionable_findings:
                with st.expander(
                    f"[{finding.get('status')}] "
                    f"{finding.get('check')}"
                ):
                    st.write(
                        "**Current:**",
                        finding.get(
                            "current_value",
                            "N/A"
                        )
                    )

                    st.write(
                        "**Expected:**",
                        finding.get(
                            "expected",
                            "N/A"
                        )
                    )

                    st.write(
                        "**Recommended Action:**"
                    )

                    st.write(
                        finding.get(
                            "recommendation",
                            "No recommendation available."
                        )
                    )

st.divider()

st.caption(
    "Nanobricks Endpoint Central Dashboard | "
    "Use only with endpoint assessment data "
    "from authorized systems."
)
