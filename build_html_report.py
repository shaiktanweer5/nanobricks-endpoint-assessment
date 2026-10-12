import argparse
import html
import json
from pathlib import Path
from datetime import datetime


APP_NAME = "Nanobricks Endpoint Assessment"
REPORT_VERSION = "2.0.0"


def esc(value):
    if value is None:
        return "N/A"
    return html.escape(str(value))


def status_class(status):
    status = str(status).upper()

    if status == "PASS":
        return "status-pass"

    if status == "REVIEW":
        return "status-review"

    if status == "FAIL":
        return "status-fail"

    return "status-neutral"


def format_bool(value):
    if value is True:
        return "Enabled"

    if value is False:
        return "Disabled"

    return "Unknown"


def load_json(json_path):
    with open(json_path, "r", encoding="utf-8") as file:
        return json.load(file)


def build_findings_rows(findings):
    rows = []

    for finding in findings:
        status = finding.get("status", "UNKNOWN")

        rows.append(
            f"""
            <tr>
                <td>{esc(finding.get("category"))}</td>
                <td>
                    <strong>{esc(finding.get("check"))}</strong>
                </td>
                <td>
                    <span class="status-badge {status_class(status)}">
                        {esc(status)}
                    </span>
                </td>
                <td>{esc(finding.get("current_value"))}</td>
                <td>{esc(finding.get("expected"))}</td>
                <td>{esc(finding.get("recommendation"))}</td>
            </tr>
            """
        )

    return "\n".join(rows)


def build_recommendations(findings):
    actionable = [
        finding
        for finding in findings
        if str(finding.get("status", "")).upper() in {"REVIEW", "FAIL"}
    ]

    if not actionable:
        return """
        <div class="empty-state">
            No remediation actions are currently required.
        </div>
        """

    cards = []

    for number, finding in enumerate(actionable, start=1):
        status = str(finding.get("status", "UNKNOWN")).upper()

        cards.append(
            f"""
            <div class="recommendation-card">
                <div class="recommendation-number">
                    {number}
                </div>

                <div class="recommendation-content">
                    <div class="recommendation-top">
                        <h3>{esc(finding.get("check"))}</h3>

                        <span class="status-badge {status_class(status)}">
                            {esc(status)}
                        </span>
                    </div>

                    <p>
                        <strong>Current:</strong>
                        {esc(finding.get("current_value"))}
                    </p>

                    <p>
                        <strong>Recommendation:</strong>
                        {esc(finding.get("recommendation"))}
                    </p>
                </div>
            </div>
            """
        )

    return "\n".join(cards)


def build_firewall_rows(firewall):
    profiles = firewall.get("profiles", [])

    if not profiles:
        return """
        <tr>
            <td colspan="2">No firewall profile data available.</td>
        </tr>
        """

    rows = []

    for profile in profiles:
        enabled = profile.get("enabled")

        rows.append(
            f"""
            <tr>
                <td>{esc(profile.get("name"))}</td>
                <td>{format_bool(enabled)}</td>
            </tr>
            """
        )

    return "\n".join(rows)


def build_local_users_rows(local_users):
    users = local_users.get("users", [])

    if not users:
        return """
        <tr>
            <td colspan="3">No local-user information available.</td>
        </tr>
        """

    rows = []

    for user in users:
        rows.append(
            f"""
            <tr>
                <td>{esc(user.get("Name"))}</td>
                <td>{format_bool(user.get("Enabled"))}</td>
                <td>{esc(user.get("PasswordRequired"))}</td>
            </tr>
            """
        )

    return "\n".join(rows)


def build_admin_rows(local_users):
    admins = local_users.get("administrators", [])

    if not admins:
        return """
        <tr>
            <td colspan="2">No local administrator information available.</td>
        </tr>
        """

    rows = []

    for admin in admins:
        rows.append(
            f"""
            <tr>
                <td>{esc(admin.get("Name"))}</td>
                <td>{esc(admin.get("ObjectClass"))}</td>
            </tr>
            """
        )

    return "\n".join(rows)


def generate_report(data):
    agent = data.get("agent", {})
    endpoint = data.get("endpoint", {})
    raw_data = data.get("raw_data", {})
    summary = data.get("summary", {})
    findings = data.get("findings", [])

    defender = raw_data.get("defender", {})
    firewall = raw_data.get("firewall", {})
    windows_update = raw_data.get("windows_update", {})
    office = raw_data.get("office", {})
    local_users = raw_data.get("local_users", {})

    hostname = endpoint.get("hostname", "Unknown Endpoint")

    pass_count = summary.get("pass", 0)
    review_count = summary.get("review", 0)
    fail_count = summary.get("fail", 0)
    total_count = summary.get("total", len(findings))

    if fail_count > 0:
        overall_status = "FAIL"
    elif review_count > 0:
        overall_status = "REVIEW"
    else:
        overall_status = "PASS"

    generated_at = datetime.now().strftime("%d %b %Y, %I:%M %p")

    findings_rows = build_findings_rows(findings)
    recommendations = build_recommendations(findings)
    firewall_rows = build_firewall_rows(firewall)
    user_rows = build_local_users_rows(local_users)
    admin_rows = build_admin_rows(local_users)

    return f"""<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>
    {esc(hostname)} - Nanobricks Endpoint Assessment
</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    background: #f5f7f6;
    color: #24352b;
    font-family:
        "Segoe UI",
        Arial,
        sans-serif;
}}

.container {{
    width: min(1180px, 94%);
    margin: 40px auto;
}}

.header {{
    background:
        linear-gradient(
            135deg,
            #153d28,
            #238b45
        );
    color: white;
    border-radius: 18px;
    padding: 36px;
    box-shadow:
        0 15px 40px rgba(0, 0, 0, 0.12);
}}

.brand {{
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 1px;
    opacity: 0.9;
}}

.header h1 {{
    margin: 12px 0 8px;
    font-size: 34px;
}}

.header p {{
    margin: 0;
    opacity: 0.9;
    line-height: 1.6;
}}

.overall {{
    margin-top: 24px;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    background: rgba(255,255,255,.12);
    padding: 11px 16px;
    border-radius: 40px;
}}

.section {{
    margin-top: 28px;
    background: white;
    border-radius: 16px;
    padding: 28px;
    border: 1px solid #e3e9e5;
    box-shadow:
        0 8px 25px rgba(0,0,0,.04);
}}

.section h2 {{
    margin-top: 0;
    margin-bottom: 22px;
    font-size: 23px;
}}

.summary-grid {{
    display: grid;
    grid-template-columns:
        repeat(4, minmax(0, 1fr));
    gap: 16px;
}}

.summary-card {{
    border: 1px solid #e4ebe6;
    border-radius: 14px;
    padding: 22px;
}}

.summary-card .number {{
    font-size: 32px;
    font-weight: 800;
    margin-bottom: 5px;
}}

.summary-card .label {{
    color: #6b756f;
    font-size: 14px;
}}

.pass-card {{
    border-left: 5px solid #249447;
}}

.review-card {{
    border-left: 5px solid #d69e00;
}}

.fail-card {{
    border-left: 5px solid #cc3d3d;
}}

.total-card {{
    border-left: 5px solid #3867a6;
}}

.info-grid {{
    display: grid;
    grid-template-columns:
        repeat(3, minmax(0, 1fr));
    gap: 15px;
}}

.info-item {{
    background: #f8faf9;
    border-radius: 12px;
    padding: 17px;
    border: 1px solid #e8ece9;
}}

.info-label {{
    font-size: 12px;
    text-transform: uppercase;
    color: #738079;
    font-weight: 700;
    letter-spacing: .4px;
}}

.info-value {{
    margin-top: 7px;
    font-size: 16px;
    font-weight: 600;
    overflow-wrap: anywhere;
}}

.status-badge {{
    display: inline-block;
    border-radius: 999px;
    padding: 6px 11px;
    font-size: 12px;
    font-weight: 800;
}}

.status-pass {{
    background: #e8f7ed;
    color: #167b36;
}}

.status-review {{
    background: #fff4d5;
    color: #956900;
}}

.status-fail {{
    background: #fde9e9;
    color: #b32626;
}}

.status-neutral {{
    background: #edf1ef;
    color: #58635d;
}}

.table-wrap {{
    width: 100%;
    overflow-x: auto;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    min-width: 760px;
}}

th {{
    text-align: left;
    padding: 13px;
    background: #f2f6f3;
    border-bottom: 2px solid #dce5df;
    font-size: 13px;
}}

td {{
    padding: 14px 13px;
    border-bottom: 1px solid #edf0ee;
    vertical-align: top;
    line-height: 1.5;
    font-size: 14px;
}}

tr:last-child td {{
    border-bottom: none;
}}

.recommendation-card {{
    display: flex;
    gap: 18px;
    padding: 20px 0;
    border-bottom: 1px solid #edf0ee;
}}

.recommendation-card:last-child {{
    border-bottom: none;
}}

.recommendation-number {{
    flex: 0 0 42px;
    width: 42px;
    height: 42px;
    background: #1f6f2b;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
}}

.recommendation-content {{
    flex: 1;
}}

.recommendation-top {{
    display: flex;
    align-items: center;
    gap: 12px;
    justify-content: space-between;
}}

.recommendation-top h3 {{
    margin: 0;
    font-size: 17px;
}}

.recommendation-content p {{
    margin: 7px 0 0;
    line-height: 1.6;
}}

.two-column {{
    display: grid;
    grid-template-columns:
        repeat(2, minmax(0, 1fr));
    gap: 22px;
}}

.sub-card {{
    border: 1px solid #e4ebe6;
    border-radius: 14px;
    padding: 20px;
}}

.sub-card h3 {{
    margin-top: 0;
}}

.empty-state {{
    padding: 20px;
    background: #f4faf5;
    border-radius: 12px;
}}

.footer {{
    text-align: center;
    color: #78827c;
    margin: 30px 0 50px;
    font-size: 13px;
    line-height: 1.7;
}}

.disclaimer {{
    color: #6d7771;
    line-height: 1.7;
    font-size: 14px;
}}

@media (max-width: 900px) {{

    .summary-grid {{
        grid-template-columns:
            repeat(2, minmax(0, 1fr));
    }}

    .info-grid {{
        grid-template-columns:
            repeat(2, minmax(0, 1fr));
    }}

    .two-column {{
        grid-template-columns: 1fr;
    }}

}}

@media (max-width: 600px) {{

    .container {{
        width: 94%;
        margin-top: 18px;
    }}

    .header {{
        padding: 25px;
    }}

    .header h1 {{
        font-size: 27px;
    }}

    .summary-grid,
    .info-grid {{
        grid-template-columns: 1fr;
    }}

}}

</style>

</head>


<body>

<div class="container">


<section class="header">

    <div class="brand">
        NANOBRICKS
    </div>

    <h1>
        Endpoint Assessment Report
    </h1>

    <p>
        Endpoint:
        <strong>{esc(hostname)}</strong>
        &nbsp; • &nbsp;
        Report Version {REPORT_VERSION}
    </p>

    <div class="overall">

        Overall Assessment:

        <span class="status-badge {status_class(overall_status)}">
            {overall_status}
        </span>

    </div>

</section>


<section class="section">

    <h2>
        Assessment Summary
    </h2>

    <div class="summary-grid">

        <div class="summary-card pass-card">

            <div class="number">
                {pass_count}
            </div>

            <div class="label">
                Passed Checks
            </div>

        </div>


        <div class="summary-card review-card">

            <div class="number">
                {review_count}
            </div>

            <div class="label">
                Review Required
            </div>

        </div>


        <div class="summary-card fail-card">

            <div class="number">
                {fail_count}
            </div>

            <div class="label">
                Failed Checks
            </div>

        </div>


        <div class="summary-card total-card">

            <div class="number">
                {total_count}
            </div>

            <div class="label">
                Total Checks
            </div>

        </div>

    </div>

</section>


<section class="section">

    <h2>
        Endpoint Overview
    </h2>

    <div class="info-grid">

        <div class="info-item">

            <div class="info-label">
                Hostname
            </div>

            <div class="info-value">
                {esc(endpoint.get("hostname"))}
            </div>

        </div>


        <div class="info-item">

            <div class="info-label">
                Operating System
            </div>

            <div class="info-value">
                {esc(endpoint.get("operating_system"))}
            </div>

        </div>


        <div class="info-item">

            <div class="info-label">
                OS Version
            </div>

            <div class="info-value">
                {esc(endpoint.get("os_version"))}
            </div>

        </div>


        <div class="info-item">

            <div class="info-label">
                Architecture
            </div>

            <div class="info-value">
                {esc(endpoint.get("architecture"))}
            </div>

        </div>


        <div class="info-item">

            <div class="info-label">
                RAM
            </div>

            <div class="info-value">
                {esc(endpoint.get("ram_gb"))} GB
            </div>

        </div>


        <div class="info-item">

            <div class="info-label">
                Disk Capacity
            </div>

            <div class="info-value">
                {esc(endpoint.get("disk_total_gb"))} GB
            </div>

        </div>


        <div class="info-item">

            <div class="info-label">
                Disk Free
            </div>

            <div class="info-value">
                {esc(endpoint.get("disk_free_gb"))} GB
            </div>

        </div>


        <div class="info-item">

            <div class="info-label">
                Disk Used
            </div>

            <div class="info-value">
                {esc(endpoint.get("disk_used_percent"))}%
            </div>

        </div>


        <div class="info-item">

            <div class="info-label">
                Processor
            </div>

            <div class="info-value">
                {esc(endpoint.get("processor"))}
            </div>

        </div>

    </div>

</section>


<section class="section">

    <h2>
        Assessment Findings
    </h2>

    <div class="table-wrap">

        <table>

            <thead>

                <tr>
                    <th>Category</th>
                    <th>Check</th>
                    <th>Status</th>
                    <th>Current Value</th>
                    <th>Expected</th>
                    <th>Recommendation</th>
                </tr>

            </thead>

            <tbody>

                {findings_rows}

            </tbody>

        </table>

    </div>

</section>


<section class="section">

    <h2>
        Recommended Actions
    </h2>

    {recommendations}

</section>


<section class="section">

    <h2>
        Security & Software Details
    </h2>

    <div class="two-column">


        <div class="sub-card">

            <h3>
                Microsoft Defender
            </h3>

            <p>
                <strong>Antivirus:</strong>
                {format_bool(defender.get("antivirus_enabled"))}
            </p>

            <p>
                <strong>Real-time protection:</strong>
                {format_bool(defender.get("realtime_protection"))}
            </p>

            <p>
                <strong>Signature information:</strong>
                {esc(defender.get("signature_updated"))}
            </p>

        </div>


        <div class="sub-card">

            <h3>
                Windows Update
            </h3>

            <p>
                <strong>Pending updates:</strong>
                {esc(windows_update.get("pending_updates"))}
            </p>

        </div>


        <div class="sub-card">

            <h3>
                Microsoft Office
            </h3>

            <p>
                <strong>Installed:</strong>
                {esc(office.get("installed"))}
            </p>

            <p>
                <strong>Product:</strong>
                {esc(office.get("product"))}
            </p>

            <p>
                <strong>Version:</strong>
                {esc(office.get("version"))}
            </p>

            <p>
                <strong>Platform:</strong>
                {esc(office.get("platform"))}
            </p>

        </div>


        <div class="sub-card">

            <h3>
                Windows Firewall
            </h3>

            <div class="table-wrap">

                <table>

                    <thead>

                        <tr>
                            <th>Profile</th>
                            <th>Status</th>
                        </tr>

                    </thead>

                    <tbody>
                        {firewall_rows}
                    </tbody>

                </table>

            </div>

        </div>

    </div>

</section>


<section class="section">

    <h2>
        Local Accounts
    </h2>

    <div class="table-wrap">

        <table>

            <thead>

                <tr>
                    <th>User</th>
                    <th>Enabled</th>
                    <th>Password Required</th>
                </tr>

            </thead>

            <tbody>
                {user_rows}
            </tbody>

        </table>

    </div>

</section>


<section class="section">

    <h2>
        Local Administrators
    </h2>

    <div class="table-wrap">

        <table>

            <thead>

                <tr>
                    <th>Account</th>
                    <th>Type</th>
                </tr>

            </thead>

            <tbody>
                {admin_rows}
            </tbody>

        </table>

    </div>

</section>


<section class="section">

    <h2>
        Assessment Information
    </h2>

    <div class="info-grid">

        <div class="info-item">

            <div class="info-label">
                Collector
            </div>

            <div class="info-value">
                {esc(agent.get("name"))}
            </div>

        </div>


        <div class="info-item">

            <div class="info-label">
                Collector Version
            </div>

            <div class="info-value">
                {esc(agent.get("version"))}
            </div>

        </div>


        <div class="info-item">

            <div class="info-label">
                Collected UTC
            </div>

            <div class="info-value">
                {esc(agent.get("collected_at_utc"))}
            </div>

        </div>

    </div>

</section>


<section class="section">

    <h2>
        Scope & Disclaimer
    </h2>

    <p class="disclaimer">

        Nanobricks Endpoint Assessment V2 is a lightweight
        endpoint configuration, security posture and readiness
        assessment utility.

        It is not an EDR, antivirus replacement,
        vulnerability scanner or complete enterprise
        endpoint-management platform.

        Assessment results are informational and should be
        reviewed based on your organization's security,
        operational and compliance requirements.

    </p>

</section>


<div class="footer">

    Generated by {APP_NAME} V{REPORT_VERSION}

    <br>

    Report generated: {generated_at}

    <br>

    © 2026 Nanobricks

</div>


</div>

</body>

</html>
"""


def main():
    parser = argparse.ArgumentParser(
        description="Generate Nanobricks Endpoint Assessment V2 HTML report."
    )

    parser.add_argument(
        "json_file",
        help="Path to an endpoint assessment JSON file."
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Optional output HTML path."
    )

    args = parser.parse_args()

    json_path = Path(args.json_file)

    if not json_path.exists():
        raise SystemExit(
            f"JSON file not found: {json_path}"
        )

    data = load_json(json_path)

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = json_path.with_suffix(".html")

    report_html = generate_report(data)

    output_path.write_text(
        report_html,
        encoding="utf-8"
    )

    print()
    print("Nanobricks Endpoint Assessment V2")
    print("---------------------------------")
    print(f"Input : {json_path}")
    print(f"Output: {output_path}")
    print()
    print("HTML report generated successfully.")


if __name__ == "__main__":
    main()