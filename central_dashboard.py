import json
from pathlib import Path

import streamlit as st


DATA_DIR = Path("endpoint-data")


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


def load_endpoint_reports():
    reports = []

    if not DATA_DIR.exists():
        return reports

    for file_path in DATA_DIR.glob("*-assessment.json"):

        try:
            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as file:

                report = json.load(file)

                report["_source_file"] = file_path.name

                reports.append(report)

        except Exception:
            continue

    return reports


reports = load_endpoint_reports()


if not reports:

    st.warning(
        "No endpoint assessment files were found."
    )

    st.write(
        "Run endpoint_agent.py on one or more systems "
        "and place the generated JSON files inside:"
    )

    st.code(
        "endpoint-data\\",
        language="text"
    )

else:

    total_devices = len(reports)

    total_pass = sum(
        report.get(
            "summary",
            {}
        ).get(
            "pass",
            0
        )
        for report in reports
    )

    total_review = sum(
        report.get(
            "summary",
            {}
        ).get(
            "review",
            0
        )
        for report in reports
    )

    total_fail = sum(
        report.get(
            "summary",
            {}
        ).get(
            "fail",
            0
        )
        for report in reports
    )


    # ========================================================
    # ORGANIZATION SUMMARY
    # ========================================================

    st.subheader(
        "Organization Overview"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Endpoints",
        total_devices
    )

    col2.metric(
        "PASS",
        total_pass
    )

    col3.metric(
        "REVIEW",
        total_review
    )

    col4.metric(
        "FAIL",
        total_fail
    )


    # ========================================================
    # ENDPOINT INVENTORY
    # ========================================================

    st.subheader(
        "Endpoint Inventory"
    )

    inventory = []

    for report in reports:

        endpoint = report.get(
            "endpoint",
            {}
        )

        summary = report.get(
            "summary",
            {}
        )

        inventory.append(
            {
                "Hostname":
                    endpoint.get(
                        "hostname",
                        "N/A"
                    ),

                "Operating System":
                    endpoint.get(
                        "operating_system",
                        "N/A"
                    ),

                "RAM (GB)":
                    endpoint.get(
                        "ram_gb",
                        "N/A"
                    ),

                "Disk Free (GB)":
                    endpoint.get(
                        "disk_free_gb",
                        "N/A"
                    ),

                "PASS":
                    summary.get(
                        "pass",
                        0
                    ),

                "REVIEW":
                    summary.get(
                        "review",
                        0
                    ),

                "FAIL":
                    summary.get(
                        "fail",
                        0
                    )
            }
        )

    st.dataframe(
        inventory,
        width="stretch",
        hide_index=True
    )


    # ========================================================
    # DEVICE DETAILS
    # ========================================================

    st.subheader(
        "Endpoint Details"
    )

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
        ).get(
            "hostname"
        )

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

        col1, col2, col3 = st.columns(3)

        col1.write(
            "**Operating System**"
        )

        col1.write(
            endpoint.get(
                "operating_system",
                "N/A"
            )
        )

        col2.write(
            "**RAM**"
        )

        col2.write(
            f"{endpoint.get('ram_gb', 'N/A')} GB"
        )

        col3.write(
            "**Disk Free**"
        )

        col3.write(
            f"{endpoint.get('disk_free_gb', 'N/A')} GB"
        )


        col1, col2, col3 = st.columns(3)

        col1.metric(
            "PASS",
            summary.get(
                "pass",
                0
            )
        )

        col2.metric(
            "REVIEW",
            summary.get(
                "review",
                0
            )
        )

        col3.metric(
            "FAIL",
            summary.get(
                "fail",
                0
            )
        )


        # ====================================================
        # FINDINGS
        # ====================================================

        st.write(
            "### Findings"
        )

        findings = selected_report.get(
            "findings",
            []
        )

        findings_table = []

        for finding in findings:

            findings_table.append(
                {
                    "Status":
                        finding.get(
                            "status",
                            "N/A"
                        ),

                    "Check":
                        finding.get(
                            "check",
                            "N/A"
                        ),

                    "Category":
                        finding.get(
                            "category",
                            "N/A"
                        ),

                    "Current":
                        finding.get(
                            "current_value",
                            "N/A"
                        ),

                    "Expected":
                        finding.get(
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


        st.write(
            "### Recommended Actions"
        )

        for finding in findings:

            if finding.get(
                "status"
            ) in [
                "REVIEW",
                "FAIL"
            ]:

                with st.expander(
                    f"[{finding.get('status')}] "
                    f"{finding.get('check')}"
                ):

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