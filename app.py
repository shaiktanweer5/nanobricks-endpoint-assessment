import json
import subprocess
import sys
from pathlib import Path

import streamlit as st


REPORT_FILE = Path("endpoint-report.json")


st.set_page_config(
    page_title="Nanobricks Endpoint Assessment",
    page_icon="🛡️",
    layout="wide"
)


st.title("🛡️ Nanobricks Endpoint Assessment")

st.write(
    "Assess Windows endpoint configuration, security posture, "
    "software readiness, and baseline compliance."
)


if st.button(
    "Run Endpoint Assessment",
    type="primary"
):

    with st.spinner(
        "Assessing this Windows endpoint..."
    ):

        result = subprocess.run(
            [sys.executable, "report.py"],
            capture_output=True,
            text=True
        )

    if result.returncode != 0:

        st.error(
            "Endpoint assessment failed."
        )

        st.code(
            result.stderr,
            language="text"
        )

    elif not REPORT_FILE.exists():

        st.error(
            "Assessment completed but endpoint-report.json "
            "was not generated."
        )

    else:

        st.session_state["assessment_completed"] = True


if (
    st.session_state.get("assessment_completed")
    and REPORT_FILE.exists()
):

    with open(
        REPORT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        report = json.load(file)

    st.success(
        "Endpoint assessment completed successfully."
    )


    # ========================================================
    # ENDPOINT OVERVIEW
    # ========================================================

    endpoint = report.get(
        "endpoint",
        {}
    )

    st.subheader(
        "Endpoint Overview"
    )

    col1, col2, col3 = st.columns(3)

    col1.write(
        "**Hostname**"
    )
    col1.write(
        endpoint.get(
            "hostname",
            "N/A"
        )
    )

    col2.write(
        "**Operating System**"
    )
    col2.write(
        endpoint.get(
            "operating_system",
            "N/A"
        )
    )

    col3.write(
        "**Architecture**"
    )
    col3.write(
        endpoint.get(
            "architecture",
            "N/A"
        )
    )


    col1, col2, col3 = st.columns(3)

    col1.write(
        "**RAM**"
    )
    col1.write(
        f"{endpoint.get('ram_gb', 'N/A')} GB"
    )

    col2.write(
        "**Disk Total**"
    )
    col2.write(
        f"{endpoint.get('disk_total_gb', 'N/A')} GB"
    )

    col3.write(
        "**Disk Free**"
    )
    col3.write(
        f"{endpoint.get('disk_free_gb', 'N/A')} GB"
    )


    # ========================================================
    # SUMMARY
    # ========================================================

    summary = report.get(
        "summary",
        {}
    )

    st.subheader(
        "Assessment Summary"
    )

    col1, col2, col3, col4 = st.columns(4)

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

    col4.metric(
        "TOTAL",
        summary.get(
            "total",
            0
        )
    )


    # ========================================================
    # FINDINGS TABLE
    # ========================================================

    findings = report.get(
        "findings",
        []
    )

    st.subheader(
        "Assessment Findings"
    )

    table_data = []

    for finding in findings:

        table_data.append(
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
        table_data,
        width="stretch",
        hide_index=True
    )


    # ========================================================
    # DETAILED FINDINGS
    # ========================================================

    st.subheader(
        "Finding Details"
    )

    for finding in findings:

        status = finding.get(
            "status",
            "UNKNOWN"
        )

        check = finding.get(
            "check",
            "N/A"
        )

        with st.expander(
            f"[{status}] {check}"
        ):

            st.write(
                "**Category:**",
                finding.get(
                    "category",
                    "N/A"
                )
            )

            st.write(
                "**Current Value:**",
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
                    "N/A"
                )
            )


    # ========================================================
    # EXPORT
    # ========================================================

    st.subheader(
        "Export Report"
    )

    st.download_button(
        label="Download Endpoint Assessment JSON",
        data=json.dumps(
            report,
            indent=4
        ),
        file_name="endpoint-assessment-report.json",
        mime="application/json"
    )


st.divider()

st.caption(
    "Nanobricks Endpoint Assessment | "
    "Use only on systems you are authorized to assess."
)