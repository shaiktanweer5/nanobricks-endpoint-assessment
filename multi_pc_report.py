import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import (
    Alignment,
    Border,
    Font,
    PatternFill,
    Side,
)


APP_NAME = "Nanobricks Multi-PC Endpoint Consolidator"
APP_VERSION = "1.0.1"
EXPECTED_COLLECTOR_VERSION = "3.0.0"


# ============================================================
# COLORS
# ============================================================

GREEN_DARK = "14532D"
GREEN_LIGHT = "E8F7ED"
BLUE = "3867A6"

PASS_FILL = "E8F7ED"
PASS_TEXT = "167B36"

REVIEW_FILL = "FFF4D5"
REVIEW_TEXT = "956900"

FAIL_FILL = "FDE9E9"
FAIL_TEXT = "B32626"

NEUTRAL_FILL = "F1F4F2"

WHITE = "FFFFFF"
MUTED = "66756D"
BORDER_COLOR = "DFE8E2"

THIN_BORDER = Border(
    left=Side(style="thin", color=BORDER_COLOR),
    right=Side(style="thin", color=BORDER_COLOR),
    top=Side(style="thin", color=BORDER_COLOR),
    bottom=Side(style="thin", color=BORDER_COLOR),
)


# ============================================================
# GENERAL HELPERS
# ============================================================

def safe_text(value):
    if value is None:
        return ""
    return str(value)


def safe_customer_name(value):
    cleaned = "".join(
        character
        if character.isalnum() or character in " -_"
        else "_"
        for character in value
    )

    return cleaned.strip() or "Customer"


def yes_no(value):
    if value is True:
        return "Yes"

    if value is False:
        return "No"

    return "Unknown"


def enabled_disabled(value):
    if value is True:
        return "Enabled"

    if value is False:
        return "Disabled"

    return "Unknown"


def get_overall_status(summary):
    if summary.get("fail", 0) > 0:
        return "FAIL"

    if summary.get("review", 0) > 0:
        return "REVIEW"

    return "PASS"


def format_defender_signature(value):
    if not value:
        return ""

    if not isinstance(value, str):
        return str(value)

    match = re.search(
        r"/Date\((-?\d+)(?:[+-]\d+)?\)/",
        value
    )

    if not match:
        return value

    try:
        milliseconds = int(
            match.group(1)
        )

        signature_time = datetime.fromtimestamp(
            milliseconds / 1000,
            tz=timezone.utc
        )

        return signature_time.strftime(
            "%d-%b-%Y %H:%M:%S UTC"
        )

    except (
        ValueError,
        OSError,
        OverflowError
    ):
        return value


def parse_collected_date(value):
    if not value:
        return ""

    try:
        dt = datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00"
            )
        )

        return dt.strftime(
            "%d-%b-%Y %H:%M UTC"
        )

    except (
        ValueError,
        TypeError
    ):
        return value


# ============================================================
# JSON LOADING
# ============================================================

def load_reports(input_dir):
    report_files = sorted(
        input_dir.glob(
            "*-assessment.json"
        )
    )

    reports = []
    errors = []

    for file_path in report_files:
        try:
            with file_path.open(
                "r",
                encoding="utf-8"
            ) as file:
                report = json.load(file)

            hostname = (
                report
                .get(
                    "endpoint",
                    {}
                )
                .get(
                    "hostname",
                    file_path.stem
                )
            )

            reports.append(
                {
                    "path": file_path,
                    "hostname": hostname,
                    "data": report,
                }
            )

        except (
            OSError,
            json.JSONDecodeError
        ) as error:
            errors.append(
                (
                    file_path.name,
                    str(error),
                )
            )

    return reports, errors


def get_collector_versions(reports):
    versions = {
        safe_text(
            item["data"]
            .get(
                "agent",
                {}
            )
            .get(
                "version",
                "Unknown"
            )
        ) or "Unknown"
        for item in reports
    }

    return sorted(
        versions
    )


def print_collector_version_warning(reports):
    versions = get_collector_versions(
        reports
    )

    warning_required = False

    if len(versions) > 1:
        warning_required = True

        print()
        print(
            "WARNING: Mixed collector versions detected:"
        )

        for version in versions:
            print(
                f"- {version}"
            )

        print()
        print(
            "For customer assessments, use reports "
            "generated from the same current V3 collector."
        )

    if (
        len(versions) == 1
        and versions[0]
        != EXPECTED_COLLECTOR_VERSION
    ):
        warning_required = True

        print()
        print(
            "WARNING: These reports were generated "
            f"with collector version {versions[0]}."
        )

        print(
            "Current recommended collector version is "
            f"{EXPECTED_COLLECTOR_VERSION}."
        )

    if (
        len(versions) > 1
        and EXPECTED_COLLECTOR_VERSION
        not in versions
    ):
        print(
            "None of the loaded reports use the current "
            "recommended collector version "
            f"{EXPECTED_COLLECTOR_VERSION}."
        )

    if warning_required:
        print()


# ============================================================
# V3 DATA HELPERS
# ============================================================

def get_firewall_profile(
    raw_data,
    profile_name
):
    firewall = raw_data.get(
        "firewall",
        {}
    )

    for profile in firewall.get(
        "profiles",
        []
    ):
        if (
            str(
                profile.get(
                    "name",
                    ""
                )
            ).lower()
            == profile_name.lower()
        ):
            return enabled_disabled(
                profile.get(
                    "enabled"
                )
            )

    return "Unknown"


def get_local_administrators(
    raw_data
):
    local_users = raw_data.get(
        "local_users",
        {}
    )

    administrators = local_users.get(
        "administrators",
        []
    )

    names = []

    for admin in administrators:
        name = admin.get(
            "Name"
        )

        if name:
            names.append(
                str(name)
            )

    return ", ".join(
        names
    )


def count_enabled_users(
    raw_data
):
    local_users = raw_data.get(
        "local_users",
        {}
    )

    return sum(
        1
        for user in local_users.get(
            "users",
            []
        )
        if user.get(
            "Enabled"
        ) is True
    )


# ============================================================
# WORKBOOK STYLING
# ============================================================

def set_fill(
    cell,
    color
):
    cell.fill = PatternFill(
        fill_type="solid",
        fgColor=color
    )


def style_status_cell(cell):
    value = (
        safe_text(
            cell.value
        )
        .strip()
        .upper()
    )

    cell.font = Font(
        bold=True
    )

    if value == "PASS":
        set_fill(
            cell,
            PASS_FILL
        )

        cell.font = Font(
            bold=True,
            color=PASS_TEXT
        )

    elif value == "REVIEW":
        set_fill(
            cell,
            REVIEW_FILL
        )

        cell.font = Font(
            bold=True,
            color=REVIEW_TEXT
        )

    elif value == "FAIL":
        set_fill(
            cell,
            FAIL_FILL
        )

        cell.font = Font(
            bold=True,
            color=FAIL_TEXT
        )


def style_table_header(
    sheet,
    row_number=1
):
    for cell in sheet[
        row_number
    ]:
        set_fill(
            cell,
            GREEN_DARK
        )

        cell.font = Font(
            color=WHITE,
            bold=True
        )

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True
        )

        cell.border = THIN_BORDER

    sheet.row_dimensions[
        row_number
    ].height = 32


def style_standard_sheet(
    sheet,
    freeze="A2",
    filter_data=True
):
    if freeze:
        sheet.freeze_panes = freeze

    if (
        filter_data
        and sheet.max_row >= 1
        and sheet.max_column >= 1
    ):
        sheet.auto_filter.ref = (
            sheet.dimensions
        )

    for row in sheet.iter_rows():
        for cell in row:
            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True
            )

            cell.border = THIN_BORDER


def set_column_widths(
    sheet,
    widths
):
    for column, width in widths.items():
        sheet.column_dimensions[
            column
        ].width = width


# ============================================================
# DATA AGGREGATION
# ============================================================

def aggregate_environment(
    reports
):
    endpoint_count = len(
        reports
    )

    total_pass = 0
    total_review = 0
    total_fail = 0
    total_checks = 0

    endpoint_pass = 0
    endpoint_review = 0
    endpoint_fail = 0

    for item in reports:
        summary = (
            item["data"]
            .get(
                "summary",
                {}
            )
        )

        total_pass += summary.get(
            "pass",
            0
        )

        total_review += summary.get(
            "review",
            0
        )

        total_fail += summary.get(
            "fail",
            0
        )

        total_checks += summary.get(
            "total",
            0
        )

        overall = get_overall_status(
            summary
        )

        if overall == "PASS":
            endpoint_pass += 1

        elif overall == "REVIEW":
            endpoint_review += 1

        else:
            endpoint_fail += 1

    return {
        "endpoint_count": endpoint_count,
        "total_pass": total_pass,
        "total_review": total_review,
        "total_fail": total_fail,
        "total_checks": total_checks,
        "endpoint_pass": endpoint_pass,
        "endpoint_review": endpoint_review,
        "endpoint_fail": endpoint_fail,
    }


def build_issue_summary(
    reports
):
    issues = {}

    for item in reports:
        hostname = item[
            "hostname"
        ]

        findings = (
            item["data"]
            .get(
                "findings",
                []
            )
        )

        for finding in findings:
            status = (
                safe_text(
                    finding.get(
                        "status"
                    )
                )
                .upper()
            )

            if status not in {
                "REVIEW",
                "FAIL",
            }:
                continue

            category = safe_text(
                finding.get(
                    "category"
                )
            )

            check = safe_text(
                finding.get(
                    "check"
                )
            )

            key = (
                status,
                category,
                check,
            )

            if key not in issues:
                issues[key] = {
                    "status": status,
                    "category": category,
                    "check": check,
                    "devices": [],
                    "recommendation": safe_text(
                        finding.get(
                            "recommendation"
                        )
                    ),
                }

            issues[
                key
            ][
                "devices"
            ].append(
                hostname
            )

    results = []

    for issue in issues.values():
        issue[
            "device_count"
        ] = len(
            issue[
                "devices"
            ]
        )

        results.append(
            issue
        )

    results.sort(
        key=lambda item: (
            0
            if item["status"] == "FAIL"
            else 1,
            -item["device_count"],
            item["category"],
            item["check"],
        )
    )

    return results


# ============================================================
# EXECUTIVE SUMMARY SHEET
# ============================================================

def build_executive_summary(
    workbook,
    reports,
    customer_name,
    generated_at
):
    sheet = workbook.active

    sheet.title = (
        "Executive Summary"
    )

    metrics = aggregate_environment(
        reports
    )

    issue_summary = build_issue_summary(
        reports
    )

    sheet.merge_cells(
        "A1:H1"
    )

    sheet["A1"] = (
        "NANOBRICKS BUSINESS ENDPOINT ASSESSMENT"
    )

    set_fill(
        sheet["A1"],
        GREEN_DARK
    )

    sheet["A1"].font = Font(
        color=WHITE,
        bold=True,
        size=18
    )

    sheet["A1"].alignment = Alignment(
        horizontal="center",
        vertical="center"
    )

    sheet.row_dimensions[
        1
    ].height = 36

    sheet["A3"] = (
        "Customer / Company"
    )

    sheet["B3"] = customer_name

    sheet["D3"] = (
        "Endpoints Assessed"
    )

    sheet["E3"] = metrics[
        "endpoint_count"
    ]

    sheet["G3"] = (
        "Report Generated"
    )

    sheet["H3"] = generated_at

    for cell_ref in [
        "A3",
        "D3",
        "G3",
    ]:
        sheet[
            cell_ref
        ].font = Font(
            bold=True,
            color=MUTED
        )

    sheet.merge_cells(
        "A5:H5"
    )

    sheet["A5"] = (
        "Environment Assessment Overview"
    )

    set_fill(
        sheet["A5"],
        GREEN_LIGHT
    )

    sheet["A5"].font = Font(
        bold=True,
        color=GREEN_DARK,
        size=13
    )

    sheet["A5"].alignment = Alignment(
        horizontal="left"
    )

    summary_cards = [
        (
            "A7",
            "B7",
            "Endpoints",
            metrics[
                "endpoint_count"
            ],
            BLUE,
        ),
        (
            "C7",
            "D7",
            "PASS",
            metrics[
                "total_pass"
            ],
            PASS_TEXT,
        ),
        (
            "E7",
            "F7",
            "REVIEW",
            metrics[
                "total_review"
            ],
            REVIEW_TEXT,
        ),
        (
            "G7",
            "H7",
            "FAIL",
            metrics[
                "total_fail"
            ],
            FAIL_TEXT,
        ),
    ]

    for (
        label_cell,
        value_cell,
        label,
        value,
        color
    ) in summary_cards:
        sheet[
            label_cell
        ] = label

        sheet[
            value_cell
        ] = value

        set_fill(
            sheet[
                label_cell
            ],
            NEUTRAL_FILL
        )

        set_fill(
            sheet[
                value_cell
            ],
            NEUTRAL_FILL
        )

        sheet[
            label_cell
        ].font = Font(
            bold=True,
            color=MUTED
        )

        sheet[
            value_cell
        ].font = Font(
            bold=True,
            color=color,
            size=18
        )

        sheet[
            value_cell
        ].alignment = Alignment(
            horizontal="center"
        )

    sheet.merge_cells(
        "A10:H10"
    )

    sheet["A10"] = (
        "Endpoint Overall Status"
    )

    set_fill(
        sheet["A10"],
        GREEN_LIGHT
    )

    sheet["A10"].font = Font(
        bold=True,
        color=GREEN_DARK,
        size=13
    )

    sheet["A12"] = "PASS Endpoints"

    sheet["B12"] = metrics[
        "endpoint_pass"
    ]

    sheet["D12"] = "REVIEW Endpoints"

    sheet["E12"] = metrics[
        "endpoint_review"
    ]

    sheet["G12"] = "FAIL Endpoints"

    sheet["H12"] = metrics[
        "endpoint_fail"
    ]

    sheet.merge_cells(
        "A15:H15"
    )

    sheet["A15"] = (
        "Priority Findings"
    )

    set_fill(
        sheet["A15"],
        GREEN_LIGHT
    )

    sheet["A15"].font = Font(
        bold=True,
        color=GREEN_DARK,
        size=13
    )

    headers = [
        "Priority",
        "Status",
        "Category",
        "Finding",
        "Affected Devices",
        "Device Count",
        "Recommendation",
        "Owner / Action",
    ]

    for column, header in enumerate(
        headers,
        start=1
    ):
        cell = sheet.cell(
            row=17,
            column=column
        )

        cell.value = header

    style_table_header(
        sheet,
        17
    )

    row_number = 18

    for issue in issue_summary[
        :15
    ]:
        priority = (
            "P1"
            if issue[
                "status"
            ] == "FAIL"
            else "P2"
        )

        sheet.cell(
            row=row_number,
            column=1
        ).value = priority

        sheet.cell(
            row=row_number,
            column=2
        ).value = issue[
            "status"
        ]

        sheet.cell(
            row=row_number,
            column=3
        ).value = issue[
            "category"
        ]

        sheet.cell(
            row=row_number,
            column=4
        ).value = issue[
            "check"
        ]

        sheet.cell(
            row=row_number,
            column=5
        ).value = ", ".join(
            issue[
                "devices"
            ]
        )

        sheet.cell(
            row=row_number,
            column=6
        ).value = issue[
            "device_count"
        ]

        sheet.cell(
            row=row_number,
            column=7
        ).value = issue[
            "recommendation"
        ]

        sheet.cell(
            row=row_number,
            column=8
        ).value = ""

        style_status_cell(
            sheet.cell(
                row=row_number,
                column=2
            )
        )

        row_number += 1

    if not issue_summary:
        sheet.merge_cells(
            start_row=18,
            start_column=1,
            end_row=18,
            end_column=8
        )

        sheet.cell(
            row=18,
            column=1
        ).value = (
            "No REVIEW or FAIL findings detected."
        )

    for row in sheet.iter_rows(
        min_row=3,
        max_row=sheet.max_row,
        min_col=1,
        max_col=8
    ):
        for cell in row:
            cell.border = THIN_BORDER

            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True
            )

    set_column_widths(
        sheet,
        {
            "A": 17,
            "B": 15,
            "C": 20,
            "D": 28,
            "E": 36,
            "F": 14,
            "G": 42,
            "H": 28,
        }
    )

    sheet.freeze_panes = "A17"

    return metrics


# ============================================================
# DEVICE INVENTORY SHEET
# ============================================================

def build_device_inventory(
    workbook,
    reports
):
    sheet = workbook.create_sheet(
        "Device Inventory"
    )

    headers = [
        "Hostname",
        "Customer",
        "Technician",
        "Operating System",
        "OS Version",
        "Architecture",
        "Processor",
        "RAM (GB)",
        "Disk Total (GB)",
        "Disk Free (GB)",
        "Disk Used (%)",
        "Defender",
        "Real-Time Protection",
        "Defender Signature",
        "Firewall Domain",
        "Firewall Private",
        "Firewall Public",
        "Pending Updates",
        "Office Installed",
        "Office Product",
        "Office Version",
        "Office Platform",
        "Enabled Local Users",
        "Local Administrators",
        "PASS",
        "REVIEW",
        "FAIL",
        "Total Checks",
        "Overall Status",
        "Collector Version",
        "Collected At UTC",
    ]

    sheet.append(
        headers
    )

    for item in reports:
        report = item[
            "data"
        ]

        endpoint = report.get(
            "endpoint",
            {}
        )

        raw_data = report.get(
            "raw_data",
            {}
        )

        summary = report.get(
            "summary",
            {}
        )

        agent = report.get(
            "agent",
            {}
        )

        context = report.get(
            "assessment_context",
            {}
        )

        defender = raw_data.get(
            "defender",
            {}
        )

        updates = raw_data.get(
            "windows_update",
            {}
        )

        office = raw_data.get(
            "office",
            {}
        )

        sheet.append(
            [
                endpoint.get(
                    "hostname",
                    ""
                ),
                context.get(
                    "customer_name",
                    ""
                ),
                context.get(
                    "technician_name",
                    ""
                ),
                endpoint.get(
                    "operating_system",
                    ""
                ),
                endpoint.get(
                    "os_version",
                    ""
                ),
                endpoint.get(
                    "architecture",
                    ""
                ),
                endpoint.get(
                    "processor",
                    ""
                ),
                endpoint.get(
                    "ram_gb",
                    ""
                ),
                endpoint.get(
                    "disk_total_gb",
                    ""
                ),
                endpoint.get(
                    "disk_free_gb",
                    ""
                ),
                endpoint.get(
                    "disk_used_percent",
                    ""
                ),
                enabled_disabled(
                    defender.get(
                        "antivirus_enabled"
                    )
                ),
                enabled_disabled(
                    defender.get(
                        "realtime_protection"
                    )
                ),
                format_defender_signature(
                    defender.get(
                        "signature_updated"
                    )
                ),
                get_firewall_profile(
                    raw_data,
                    "Domain"
                ),
                get_firewall_profile(
                    raw_data,
                    "Private"
                ),
                get_firewall_profile(
                    raw_data,
                    "Public"
                ),
                updates.get(
                    "pending_updates",
                    ""
                ),
                yes_no(
                    office.get(
                        "installed"
                    )
                ),
                office.get(
                    "product",
                    ""
                ),
                office.get(
                    "version",
                    ""
                ),
                office.get(
                    "platform",
                    ""
                ),
                count_enabled_users(
                    raw_data
                ),
                get_local_administrators(
                    raw_data
                ),
                summary.get(
                    "pass",
                    0
                ),
                summary.get(
                    "review",
                    0
                ),
                summary.get(
                    "fail",
                    0
                ),
                summary.get(
                    "total",
                    0
                ),
                get_overall_status(
                    summary
                ),
                agent.get(
                    "version",
                    ""
                ),
                parse_collected_date(
                    agent.get(
                        "collected_at_utc"
                    )
                ),
            ]
        )

    style_table_header(
        sheet
    )

    style_standard_sheet(
        sheet
    )

    for row in sheet.iter_rows(
        min_row=2
    ):
        style_status_cell(
            row[28]
        )

    set_column_widths(
        sheet,
        {
            "A": 20,
            "B": 22,
            "C": 20,
            "D": 24,
            "E": 24,
            "F": 16,
            "G": 36,
            "H": 12,
            "I": 15,
            "J": 15,
            "K": 15,
            "L": 15,
            "M": 20,
            "N": 25,
            "O": 18,
            "P": 18,
            "Q": 18,
            "R": 16,
            "S": 16,
            "T": 30,
            "U": 18,
            "V": 16,
            "W": 18,
            "X": 38,
            "Y": 10,
            "Z": 10,
            "AA": 10,
            "AB": 14,
            "AC": 16,
            "AD": 18,
            "AE": 24,
        }
    )


# ============================================================
# FINDINGS SHEET
# ============================================================

def build_findings_sheet(
    workbook,
    reports
):
    sheet = workbook.create_sheet(
        "All Findings"
    )

    headers = [
        "Hostname",
        "Customer",
        "Status",
        "Priority",
        "Category",
        "Check",
        "Current Value",
        "Expected",
        "Recommendation",
    ]

    sheet.append(
        headers
    )

    for item in reports:
        report = item[
            "data"
        ]

        hostname = item[
            "hostname"
        ]

        context = report.get(
            "assessment_context",
            {}
        )

        customer = context.get(
            "customer_name",
            ""
        )

        for finding in report.get(
            "findings",
            []
        ):
            status = safe_text(
                finding.get(
                    "status"
                )
            ).upper()

            if status == "FAIL":
                priority = "P1"

            elif status == "REVIEW":
                priority = "P2"

            else:
                priority = "P3"

            sheet.append(
                [
                    hostname,
                    customer,
                    status,
                    priority,
                    finding.get(
                        "category",
                        ""
                    ),
                    finding.get(
                        "check",
                        ""
                    ),
                    safe_text(
                        finding.get(
                            "current_value"
                        )
                    ),
                    safe_text(
                        finding.get(
                            "expected"
                        )
                    ),
                    safe_text(
                        finding.get(
                            "recommendation"
                        )
                    ),
                ]
            )

    style_table_header(
        sheet
    )

    style_standard_sheet(
        sheet
    )

    for row in sheet.iter_rows(
        min_row=2
    ):
        style_status_cell(
            row[2]
        )

    set_column_widths(
        sheet,
        {
            "A": 20,
            "B": 24,
            "C": 12,
            "D": 10,
            "E": 20,
            "F": 30,
            "G": 32,
            "H": 32,
            "I": 45,
        }
    )


# ============================================================
# LOCAL USERS SHEET
# ============================================================

def build_local_users_sheet(
    workbook,
    reports
):
    sheet = workbook.create_sheet(
        "Local Users"
    )

    headers = [
        "Hostname",
        "User Name",
        "Enabled",
        "Password Required",
        "Administrator",
    ]

    sheet.append(
        headers
    )

    for item in reports:
        report = item[
            "data"
        ]

        hostname = item[
            "hostname"
        ]

        local_user_data = (
            report
            .get(
                "raw_data",
                {}
            )
            .get(
                "local_users",
                {}
            )
        )

        administrators = (
            local_user_data
            .get(
                "administrators",
                []
            )
        )

        administrator_names = {
            safe_text(
                admin.get(
                    "Name"
                )
            )
            .split("\\")[-1]
            .lower()
            for admin in administrators
            if admin.get(
                "Name"
            )
        }

        for user in local_user_data.get(
            "users",
            []
        ):
            username = safe_text(
                user.get(
                    "Name"
                )
            )

            sheet.append(
                [
                    hostname,
                    username,
                    yes_no(
                        user.get(
                            "Enabled"
                        )
                    ),
                    yes_no(
                        user.get(
                            "PasswordRequired"
                        )
                    ),
                    (
                        "Yes"
                        if username.lower()
                        in administrator_names
                        else "No"
                    ),
                ]
            )

    style_table_header(
        sheet
    )

    style_standard_sheet(
        sheet
    )

    set_column_widths(
        sheet,
        {
            "A": 22,
            "B": 28,
            "C": 14,
            "D": 20,
            "E": 16,
        }
    )


# ============================================================
# ADMINISTRATORS SHEET
# ============================================================

def build_administrators_sheet(
    workbook,
    reports
):
    sheet = workbook.create_sheet(
        "Administrators"
    )

    headers = [
        "Hostname",
        "Administrator",
        "Object Class",
    ]

    sheet.append(
        headers
    )

    for item in reports:
        report = item[
            "data"
        ]

        hostname = item[
            "hostname"
        ]

        administrators = (
            report
            .get(
                "raw_data",
                {}
            )
            .get(
                "local_users",
                {}
            )
            .get(
                "administrators",
                []
            )
        )

        for admin in administrators:
            sheet.append(
                [
                    hostname,
                    admin.get(
                        "Name",
                        ""
                    ),
                    admin.get(
                        "ObjectClass",
                        ""
                    ),
                ]
            )

    style_table_header(
        sheet
    )

    style_standard_sheet(
        sheet
    )

    set_column_widths(
        sheet,
        {
            "A": 22,
            "B": 40,
            "C": 20,
        }
    )


# ============================================================
# REMEDIATION PLAN SHEET
# ============================================================

def build_remediation_sheet(
    workbook,
    reports
):
    sheet = workbook.create_sheet(
        "Remediation Plan"
    )

    headers = [
        "Priority",
        "Status",
        "Category",
        "Finding",
        "Affected Devices",
        "Device Count",
        "Recommendation",
        "Remediation Status",
        "Owner",
        "Target Date",
        "Notes",
    ]

    sheet.append(
        headers
    )

    issues = build_issue_summary(
        reports
    )

    for issue in issues:
        priority = (
            "P1"
            if issue[
                "status"
            ] == "FAIL"
            else "P2"
        )

        sheet.append(
            [
                priority,
                issue[
                    "status"
                ],
                issue[
                    "category"
                ],
                issue[
                    "check"
                ],
                ", ".join(
                    issue[
                        "devices"
                    ]
                ),
                issue[
                    "device_count"
                ],
                issue[
                    "recommendation"
                ],
                "Open",
                "",
                "",
                "",
            ]
        )

    style_table_header(
        sheet
    )

    style_standard_sheet(
        sheet
    )

    for row in sheet.iter_rows(
        min_row=2
    ):
        style_status_cell(
            row[1]
        )

    set_column_widths(
        sheet,
        {
            "A": 10,
            "B": 12,
            "C": 20,
            "D": 30,
            "E": 38,
            "F": 14,
            "G": 45,
            "H": 20,
            "I": 20,
            "J": 16,
            "K": 35,
        }
    )


# ============================================================
# CHART
# ============================================================

def add_summary_chart(
    workbook,
    metrics
):
    sheet = workbook[
        "Executive Summary"
    ]

    sheet["J2"] = "Status"
    sheet["K2"] = "Count"

    sheet["J3"] = "PASS"

    sheet["K3"] = metrics[
        "total_pass"
    ]

    sheet["J4"] = "REVIEW"

    sheet["K4"] = metrics[
        "total_review"
    ]

    sheet["J5"] = "FAIL"

    sheet["K5"] = metrics[
        "total_fail"
    ]

    chart = BarChart()

    chart.type = "col"

    chart.style = 10

    chart.title = (
        "Environment Findings"
    )

    chart.y_axis.title = (
        "Number of Checks"
    )

    chart.x_axis.title = (
        "Status"
    )

    chart.height = 7

    chart.width = 12

    data = Reference(
        sheet,
        min_col=11,
        min_row=2,
        max_row=5
    )

    categories = Reference(
        sheet,
        min_col=10,
        min_row=3,
        max_row=5
    )

    chart.add_data(
        data,
        titles_from_data=True
    )

    chart.set_categories(
        categories
    )

    sheet.add_chart(
        chart,
        "J7"
    )

    sheet.column_dimensions[
        "J"
    ].hidden = True

    sheet.column_dimensions[
        "K"
    ].hidden = True


# ============================================================
# WORKBOOK GENERATION
# ============================================================

def build_workbook(
    reports,
    customer_name,
    output_path
):
    workbook = Workbook()

    generated_at = datetime.now().strftime(
        "%d-%b-%Y %I:%M %p"
    )

    metrics = build_executive_summary(
        workbook,
        reports,
        customer_name,
        generated_at
    )

    build_device_inventory(
        workbook,
        reports
    )

    build_findings_sheet(
        workbook,
        reports
    )

    build_local_users_sheet(
        workbook,
        reports
    )

    build_administrators_sheet(
        workbook,
        reports
    )

    build_remediation_sheet(
        workbook,
        reports
    )

    add_summary_chart(
        workbook,
        metrics
    )

    workbook.save(
        output_path
    )


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Consolidate multiple Nanobricks "
            "Endpoint Assessment V3 JSON files "
            "into one business Excel report."
        )
    )

    parser.add_argument(
        "input_folder",
        help=(
            "Folder containing "
            "*-assessment.json files."
        )
    )

    parser.add_argument(
        "--customer",
        required=True,
        help=(
            "Customer or company name "
            "for the consolidated report."
        )
    )

    parser.add_argument(
        "--output-folder",
        help=(
            "Optional output folder. "
            "Defaults to the input folder's parent."
        )
    )

    args = parser.parse_args()

    input_dir = Path(
        args.input_folder
    ).expanduser().resolve()

    if not input_dir.exists():
        raise SystemExit(
            f"Input folder not found: {input_dir}"
        )

    if not input_dir.is_dir():
        raise SystemExit(
            f"Input path is not a folder: {input_dir}"
        )

    reports, errors = load_reports(
        input_dir
    )

    if not reports:
        raise SystemExit(
            "No valid *-assessment.json files "
            f"found in: {input_dir}"
        )

    print_collector_version_warning(
        reports
    )

    if args.output_folder:
        output_dir = Path(
            args.output_folder
        ).expanduser().resolve()

    else:
        output_dir = (
            input_dir.parent
            / "Consolidated-Report"
        )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    safe_customer = safe_customer_name(
        args.customer
    )

    output_file = (
        output_dir
        / (
            "Nanobricks-Business-Endpoint-Assessment-"
            f"{safe_customer}.xlsx"
        )
    )

    build_workbook(
        reports,
        args.customer,
        output_file
    )

    environment = aggregate_environment(
        reports
    )

    versions = get_collector_versions(
        reports
    )

    print()
    print("=" * 72)

    print(
        "NANOBRICKS BUSINESS ENDPOINT ASSESSMENT"
    )

    print("=" * 72)

    print(
        f"Consolidator version: {APP_VERSION}"
    )

    print(
        f"Customer: {args.customer}"
    )

    print(
        f"Endpoints processed: "
        f"{environment['endpoint_count']}"
    )

    print(
        "Collector version(s): "
        + ", ".join(
            versions
        )
    )

    print(
        f"PASS findings: "
        f"{environment['total_pass']}"
    )

    print(
        f"REVIEW findings: "
        f"{environment['total_review']}"
    )

    print(
        f"FAIL findings: "
        f"{environment['total_fail']}"
    )

    print()

    print(
        "Excel report created:"
    )

    print(
        output_file
    )

    if errors:
        print()
        print(
            "Files skipped because of errors:"
        )

        for filename, error in errors:
            print(
                f"- {filename}: {error}"
            )

    print("=" * 72)
    print()


if __name__ == "__main__":
    main()