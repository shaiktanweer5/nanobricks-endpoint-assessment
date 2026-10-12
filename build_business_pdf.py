import argparse
import json
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


APP_NAME = "Nanobricks Business Endpoint PDF Builder"
APP_VERSION = "1.1.1"
EXPECTED_COLLECTOR_VERSION = "3.0.0"

SCRIPT_DIR = Path(__file__).resolve().parent
LOGO_PATH = SCRIPT_DIR / "nano-log.png"


# ============================================================
# BRANDING
# ============================================================

NANOBRICKS_GREEN = colors.HexColor("#14532D")
NANOBRICKS_GREEN_LIGHT = colors.HexColor("#E8F7ED")

PASS_COLOR = colors.HexColor("#167B36")
PASS_BG = colors.HexColor("#E8F7ED")

REVIEW_COLOR = colors.HexColor("#956900")
REVIEW_BG = colors.HexColor("#FFF4D5")

FAIL_COLOR = colors.HexColor("#B32626")
FAIL_BG = colors.HexColor("#FDE9E9")

TEXT_COLOR = colors.HexColor("#20342A")
MUTED_COLOR = colors.HexColor("#66756D")
BORDER_COLOR = colors.HexColor("#DFE8E2")

WHITE = colors.white

PAGE_WIDTH, PAGE_HEIGHT = A4


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
        if character.isalnum()
        or character in " -_"
        else "_"
        for character in value
    )

    return cleaned.strip() or "Customer"


def get_overall_status(summary):
    if summary.get("fail", 0) > 0:
        return "FAIL"

    if summary.get("review", 0) > 0:
        return "REVIEW"

    return "PASS"


def generate_report_reference():
    now = datetime.now()

    return now.strftime(
        "NB-EA-%Y%m%d-%H%M%S"
    )


def get_status_colors(status):
    status = safe_text(
        status
    ).upper()

    if status == "PASS":
        return PASS_COLOR, PASS_BG

    if status == "FAIL":
        return FAIL_COLOR, FAIL_BG

    return REVIEW_COLOR, REVIEW_BG


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
                report = json.load(
                    file
                )

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
                    str(error)
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
        )
        or "Unknown"
        for item in reports
    }

    return sorted(
        versions
    )


# ============================================================
# AGGREGATION
# ============================================================

def aggregate_environment(reports):
    metrics = {
        "endpoint_count": len(reports),
        "total_pass": 0,
        "total_review": 0,
        "total_fail": 0,
        "total_checks": 0,
        "endpoint_pass": 0,
        "endpoint_review": 0,
        "endpoint_fail": 0,
    }

    for item in reports:
        summary = (
            item["data"]
            .get(
                "summary",
                {}
            )
        )

        metrics[
            "total_pass"
        ] += summary.get(
            "pass",
            0
        )

        metrics[
            "total_review"
        ] += summary.get(
            "review",
            0
        )

        metrics[
            "total_fail"
        ] += summary.get(
            "fail",
            0
        )

        metrics[
            "total_checks"
        ] += summary.get(
            "total",
            0
        )

        overall = get_overall_status(
            summary
        )

        if overall == "PASS":
            metrics[
                "endpoint_pass"
            ] += 1

        elif overall == "REVIEW":
            metrics[
                "endpoint_review"
            ] += 1

        else:
            metrics[
                "endpoint_fail"
            ] += 1

    return metrics


def build_issue_summary(reports):
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
                issues[
                    key
                ] = {
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
            if item[
                "status"
            ] == "FAIL"
            else 1,
            -item[
                "device_count"
            ],
            item[
                "category"
            ],
            item[
                "check"
            ],
        )
    )

    return results


# ============================================================
# PDF STYLES
# ============================================================

def build_styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="NBTitle",
            parent=styles[
                "Title"
            ],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=23,
            textColor=WHITE,
            alignment=TA_LEFT,
            spaceAfter=1,
        )
    )

    styles.add(
        ParagraphStyle(
            name="NBSubtitle",
            parent=styles[
                "Normal"
            ],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=WHITE,
        )
    )

    styles.add(
        ParagraphStyle(
            name="NBSection",
            parent=styles[
                "Heading2"
            ],
            fontName="Helvetica-Bold",
            fontSize=13.5,
            leading=17,
            textColor=NANOBRICKS_GREEN,
            spaceBefore=5,
            spaceAfter=6,
        )
    )

    styles.add(
        ParagraphStyle(
            name="NBBody",
            parent=styles[
                "BodyText"
            ],
            fontName="Helvetica",
            fontSize=9,
            leading=12.5,
            textColor=TEXT_COLOR,
        )
    )

    styles.add(
        ParagraphStyle(
            name="NBBodySmall",
            parent=styles[
                "BodyText"
            ],
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=TEXT_COLOR,
        )
    )

    styles.add(
        ParagraphStyle(
            name="NBMuted",
            parent=styles[
                "BodyText"
            ],
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=MUTED_COLOR,
        )
    )

    styles.add(
        ParagraphStyle(
            name="NBCardLabel",
            parent=styles[
                "Normal"
            ],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=MUTED_COLOR,
            alignment=TA_CENTER,
        )
    )

    styles.add(
        ParagraphStyle(
            name="NBCardValue",
            parent=styles[
                "Normal"
            ],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=19,
            alignment=TA_CENTER,
        )
    )

    styles.add(
        ParagraphStyle(
            name="NBTableHeader",
            parent=styles[
                "Normal"
            ],
            fontName="Helvetica-Bold",
            fontSize=7.3,
            leading=8.5,
            textColor=WHITE,
            alignment=TA_LEFT,
        )
    )

    styles.add(
        ParagraphStyle(
            name="NBTable",
            parent=styles[
                "Normal"
            ],
            fontName="Helvetica",
            fontSize=7.2,
            leading=9.2,
            textColor=TEXT_COLOR,
        )
    )

    return styles


# ============================================================
# PAGE DECORATION
# ============================================================

def draw_page(canvas, doc):
    canvas.saveState()

    canvas.setStrokeColor(
        BORDER_COLOR
    )

    canvas.setLineWidth(
        0.5
    )

    canvas.line(
        18 * mm,
        14 * mm,
        PAGE_WIDTH - 18 * mm,
        14 * mm,
    )

    canvas.setFont(
        "Helvetica",
        7
    )

    canvas.setFillColor(
        MUTED_COLOR
    )

    canvas.drawString(
        18 * mm,
        9 * mm,
        "Nanobricks Business Endpoint Assessment"
    )

    canvas.drawRightString(
        PAGE_WIDTH - 18 * mm,
        9 * mm,
        f"Page {doc.page}"
    )

    canvas.restoreState()


# ============================================================
# PARAGRAPH HELPER
# ============================================================

def paragraph(
    text,
    style
):
    escaped = (
        safe_text(
            text
        )
        .replace(
            "&",
            "&amp;"
        )
        .replace(
            "<",
            "&lt;"
        )
        .replace(
            ">",
            "&gt;"
        )
    )

    return Paragraph(
        escaped,
        style
    )


# ============================================================
# HEADER
# ============================================================

def build_header(
    customer_name,
    report_reference,
    styles
):
    text_content = [
        Paragraph(
            "NANOBRICKS",
            styles[
                "NBTitle"
            ]
        ),
        Paragraph(
            "Business Endpoint Assessment",
            styles[
                "NBSubtitle"
            ]
        ),
        Spacer(
            1,
            2 * mm
        ),
        Paragraph(
            f"Customer / Company: {customer_name}",
            styles[
                "NBSubtitle"
            ]
        ),
        Paragraph(
            f"Assessment Reference: {report_reference}",
            styles[
                "NBSubtitle"
            ]
        ),
    ]

    text_table = Table(
        [
            [
                item
            ]
            for item in text_content
        ],
        colWidths=[
            128 * mm
        ]
    )

    text_table.setStyle(
        TableStyle(
            [
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
            ]
        )
    )

    if LOGO_PATH.exists():
        logo = Image(
            str(
                LOGO_PATH
            )
        )

        logo._restrictSize(
            30 * mm,
            30 * mm
        )

        header_data = [
            [
                logo,
                text_table,
            ]
        ]

        col_widths = [
            35 * mm,
            133 * mm,
        ]

    else:
        header_data = [
            [
                text_table
            ]
        ]

        col_widths = [
            168 * mm
        ]

    header = Table(
        header_data,
        colWidths=col_widths
    )

    header.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    NANOBRICKS_GREEN,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7 * mm,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7 * mm,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6 * mm,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6 * mm,
                ),
            ]
        )
    )

    return header


# ============================================================
# REPORT INFORMATION
# ============================================================

def build_report_information(
    reports,
    customer_name,
    report_reference,
    styles
):
    versions = get_collector_versions(
        reports
    )

    generated = datetime.now().strftime(
        "%d-%b-%Y %I:%M %p"
    )

    data = [
        [
            paragraph(
                "Customer / Company",
                styles[
                    "NBMuted"
                ]
            ),
            paragraph(
                customer_name,
                styles[
                    "NBBody"
                ]
            ),
            paragraph(
                "Report Generated",
                styles[
                    "NBMuted"
                ]
            ),
            paragraph(
                generated,
                styles[
                    "NBBody"
                ]
            ),
        ],
        [
            paragraph(
                "Endpoints Assessed",
                styles[
                    "NBMuted"
                ]
            ),
            paragraph(
                len(
                    reports
                ),
                styles[
                    "NBBody"
                ]
            ),
            paragraph(
                "Collector Version(s)",
                styles[
                    "NBMuted"
                ]
            ),
            paragraph(
                ", ".join(
                    versions
                ),
                styles[
                    "NBBody"
                ]
            ),
        ],
        [
            paragraph(
                "Assessment Reference",
                styles[
                    "NBMuted"
                ]
            ),
            paragraph(
                report_reference,
                styles[
                    "NBBody"
                ]
            ),
            paragraph(
                "Report Builder",
                styles[
                    "NBMuted"
                ]
            ),
            paragraph(
                f"v{APP_VERSION}",
                styles[
                    "NBBody"
                ]
            ),
        ],
    ]

    table = Table(
        data,
        colWidths=[
            35 * mm,
            50 * mm,
            35 * mm,
            54 * mm,
        ]
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    BORDER_COLOR,
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    BORDER_COLOR,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor(
                        "#FAFCFB"
                    ),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    return table


# ============================================================
# METRIC CARDS
# ============================================================

def make_metric_card(
    label,
    value,
    styles,
    value_color
):
    value_style = ParagraphStyle(
        name=(
            "MetricValue"
            + label
        ),
        parent=styles[
            "NBCardValue"
        ],
        textColor=value_color,
    )

    data = [
        [
            Paragraph(
                label,
                styles[
                    "NBCardLabel"
                ]
            )
        ],
        [
            Paragraph(
                str(
                    value
                ),
                value_style
            )
        ],
    ]

    table = Table(
        data,
        colWidths=[
            39 * mm
        ],
        rowHeights=[
            7 * mm,
            11 * mm,
        ]
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor(
                        "#F7FAF8"
                    ),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    BORDER_COLOR,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
            ]
        )
    )

    return table


def build_summary_cards(
    metrics,
    styles
):
    cards = [
        make_metric_card(
            "ENDPOINTS",
            metrics[
                "endpoint_count"
            ],
            styles,
            colors.HexColor(
                "#3867A6"
            ),
        ),
        make_metric_card(
            "PASS",
            metrics[
                "total_pass"
            ],
            styles,
            PASS_COLOR,
        ),
        make_metric_card(
            "REVIEW",
            metrics[
                "total_review"
            ],
            styles,
            REVIEW_COLOR,
        ),
        make_metric_card(
            "FAIL",
            metrics[
                "total_fail"
            ],
            styles,
            FAIL_COLOR,
        ),
    ]

    table = Table(
        [
            cards
        ],
        colWidths=[
            43.5 * mm,
            43.5 * mm,
            43.5 * mm,
            43.5 * mm,
        ]
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    2,
                ),
            ]
        )
    )

    return table


# ============================================================
# ENDPOINT STATUS TABLE
# ============================================================

def build_endpoint_status_table(
    reports,
    styles
):
    data = [
        [
            Paragraph(
                "Hostname",
                styles[
                    "NBTableHeader"
                ]
            ),
            Paragraph(
                "PASS",
                styles[
                    "NBTableHeader"
                ]
            ),
            Paragraph(
                "REVIEW",
                styles[
                    "NBTableHeader"
                ]
            ),
            Paragraph(
                "FAIL",
                styles[
                    "NBTableHeader"
                ]
            ),
            Paragraph(
                "Overall",
                styles[
                    "NBTableHeader"
                ]
            ),
        ]
    ]

    for item in reports:
        report = item[
            "data"
        ]

        summary = report.get(
            "summary",
            {}
        )

        overall = get_overall_status(
            summary
        )

        data.append(
            [
                paragraph(
                    item[
                        "hostname"
                    ],
                    styles[
                        "NBTable"
                    ]
                ),
                paragraph(
                    summary.get(
                        "pass",
                        0
                    ),
                    styles[
                        "NBTable"
                    ]
                ),
                paragraph(
                    summary.get(
                        "review",
                        0
                    ),
                    styles[
                        "NBTable"
                    ]
                ),
                paragraph(
                    summary.get(
                        "fail",
                        0
                    ),
                    styles[
                        "NBTable"
                    ]
                ),
                paragraph(
                    overall,
                    styles[
                        "NBTable"
                    ]
                ),
            ]
        )

    table = Table(
        data,
        colWidths=[
            70 * mm,
            22 * mm,
            24 * mm,
            22 * mm,
            36 * mm,
        ],
        repeatRows=1
    )

    commands = [
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            NANOBRICKS_GREEN,
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.4,
            BORDER_COLOR,
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "TOP",
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            5,
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            5,
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
    ]

    for row_index, item in enumerate(
        reports,
        start=1
    ):
        overall = get_overall_status(
            item[
                "data"
            ].get(
                "summary",
                {}
            )
        )

        _, background = get_status_colors(
            overall
        )

        commands.append(
            (
                "BACKGROUND",
                (4, row_index),
                (4, row_index),
                background,
            )
        )

    table.setStyle(
        TableStyle(
            commands
        )
    )

    return table


# ============================================================
# FINDINGS TABLE
# ============================================================

def build_findings_table(
    issues,
    styles
):
    data = [
        [
            Paragraph(
                "Priority",
                styles[
                    "NBTableHeader"
                ]
            ),
            Paragraph(
                "Status",
                styles[
                    "NBTableHeader"
                ]
            ),
            Paragraph(
                "Finding",
                styles[
                    "NBTableHeader"
                ]
            ),
            Paragraph(
                "Affected Devices",
                styles[
                    "NBTableHeader"
                ]
            ),
            Paragraph(
                "Recommendation",
                styles[
                    "NBTableHeader"
                ]
            ),
        ]
    ]

    if not issues:
        data.append(
            [
                paragraph(
                    "-",
                    styles[
                        "NBTable"
                    ]
                ),
                paragraph(
                    "PASS",
                    styles[
                        "NBTable"
                    ]
                ),
                paragraph(
                    "No REVIEW or FAIL findings detected.",
                    styles[
                        "NBTable"
                    ]
                ),
                paragraph(
                    "-",
                    styles[
                        "NBTable"
                    ]
                ),
                paragraph(
                    "Continue routine endpoint maintenance and monitoring.",
                    styles[
                        "NBTable"
                    ]
                ),
            ]
        )

    else:
        for issue in issues[
            :15
        ]:
            priority = (
                "P1"
                if issue[
                    "status"
                ] == "FAIL"
                else "P2"
            )

            finding_text = (
                issue[
                    "category"
                ]
                + " - "
                + issue[
                    "check"
                ]
            )

            devices = ", ".join(
                issue[
                    "devices"
                ]
            )

            data.append(
                [
                    paragraph(
                        priority,
                        styles[
                            "NBTable"
                        ]
                    ),
                    paragraph(
                        issue[
                            "status"
                        ],
                        styles[
                            "NBTable"
                        ]
                    ),
                    paragraph(
                        finding_text,
                        styles[
                            "NBTable"
                        ]
                    ),
                    paragraph(
                        devices,
                        styles[
                            "NBTable"
                        ]
                    ),
                    paragraph(
                        issue[
                            "recommendation"
                        ],
                        styles[
                            "NBTable"
                        ]
                    ),
                ]
            )

    table = Table(
        data,
        colWidths=[
            14 * mm,
            20 * mm,
            45 * mm,
            40 * mm,
            55 * mm,
        ],
        repeatRows=1
    )

    commands = [
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            NANOBRICKS_GREEN,
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.4,
            BORDER_COLOR,
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "TOP",
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
        (
            "TOPPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, -1),
            4,
        ),
    ]

    for index, issue in enumerate(
        issues[
            :15
        ],
        start=1
    ):
        _, background = get_status_colors(
            issue[
                "status"
            ]
        )

        commands.append(
            (
                "BACKGROUND",
                (1, index),
                (1, index),
                background,
            )
        )

    table.setStyle(
        TableStyle(
            commands
        )
    )

    return table


# ============================================================
# REMEDIATION SECTION
# ============================================================

def build_recommendation_section(
    issues,
    styles
):
    story = []

    if not issues:
        story.append(
            Paragraph(
                "No immediate remediation items were identified. "
                "Continue standard Windows patching, security review, "
                "account review and routine endpoint maintenance.",
                styles[
                    "NBBody"
                ]
            )
        )

        return story

    for index, issue in enumerate(
        issues[
            :10
        ],
        start=1
    ):
        priority = (
            "P1"
            if issue[
                "status"
            ] == "FAIL"
            else "P2"
        )

        heading = (
            f"{index}. {priority} - "
            f"{issue['category']} - "
            f"{issue['check']}"
        )

        details = (
            f"Affected devices: "
            f"{', '.join(issue['devices'])}"
            f"<br/>"
            f"Recommendation: "
            f"{issue['recommendation']}"
        )

        remediation_item = [
            Paragraph(
                heading,
                ParagraphStyle(
                    name=(
                        "RecHeading"
                        + str(
                            index
                        )
                    ),
                    parent=styles[
                        "NBBody"
                    ],
                    fontName="Helvetica-Bold",
                    textColor=TEXT_COLOR,
                    spaceAfter=2,
                )
            ),
            Paragraph(
                details,
                styles[
                    "NBBodySmall"
                ]
            ),
            Spacer(
                1,
                3 * mm
            ),
        ]

        story.append(
            KeepTogether(
                remediation_item
            )
        )

    return story


# ============================================================
# CONTACT CTA
# ============================================================

def build_contact_cta(styles):
    contact_data = [
        [
            Paragraph(
                "Need Help With These Findings?",
                ParagraphStyle(
                    name="ContactHeading",
                    parent=styles[
                        "NBSection"
                    ],
                    textColor=WHITE,
                    spaceBefore=0,
                    spaceAfter=2,
                    fontSize=13,
                )
            )
        ],
        [
            Paragraph(
                "Nanobricks can help with endpoint remediation, "
                "Windows standardization, security configuration, "
                "multi-PC assessments and ongoing IT support.",
                ParagraphStyle(
                    name="ContactBody",
                    parent=styles[
                        "NBBody"
                    ],
                    textColor=WHITE,
                )
            )
        ],
        [
            Paragraph(
                "Email: info@nanobricks.in"
                "<br/>"
                "Phone: +91 7995720507"
                "<br/>"
                "Website: www.nanobricks.in",
                ParagraphStyle(
                    name="ContactInfo",
                    parent=styles[
                        "NBBody"
                    ],
                    fontName="Helvetica-Bold",
                    textColor=WHITE,
                )
            )
        ],
    ]

    contact_table = Table(
        contact_data,
        colWidths=[
            174 * mm
        ]
    )

    contact_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    NANOBRICKS_GREEN,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7 * mm,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7 * mm,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, 0),
                    5 * mm,
                ),
                (
                    "BOTTOMPADDING",
                    (0, -1),
                    (-1, -1),
                    5 * mm,
                ),
            ]
        )
    )

    return contact_table


# ============================================================
# PDF GENERATOR
# ============================================================

def build_pdf(
    reports,
    customer_name,
    output_path
):
    styles = build_styles()

    metrics = aggregate_environment(
        reports
    )

    issues = build_issue_summary(
        reports
    )

    report_reference = generate_report_reference()

    frame = Frame(
        18 * mm,
        18 * mm,
        PAGE_WIDTH - 36 * mm,
        PAGE_HEIGHT - 32 * mm,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="normal"
    )

    document = BaseDocTemplate(
        str(
            output_path
        ),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=(
            "Nanobricks Business Endpoint Assessment"
        ),
        author="Nanobricks",
    )

    document.addPageTemplates(
        [
            PageTemplate(
                id="Assessment",
                frames=[
                    frame
                ],
                onPage=draw_page,
            )
        ]
    )

    story = []

    story.append(
        build_header(
            customer_name,
            report_reference,
            styles
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm
        )
    )

    story.append(
        Paragraph(
            "Assessment Information",
            styles[
                "NBSection"
            ]
        )
    )

    story.append(
        build_report_information(
            reports,
            customer_name,
            report_reference,
            styles
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm
        )
    )

    story.append(
        Paragraph(
            "Executive Summary",
            styles[
                "NBSection"
            ]
        )
    )

    story.append(
        Paragraph(
            "This report provides a consolidated view of the "
            "Windows endpoints assessed using the Nanobricks "
            "Endpoint Assessment utility. The summary below "
            "highlights endpoint health, review items and "
            "priority remediation areas.",
            styles[
                "NBBody"
            ]
        )
    )

    story.append(
        Spacer(
            1,
            4 * mm
        )
    )

    story.append(
        build_summary_cards(
            metrics,
            styles
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm
        )
    )

    story.append(
        Paragraph(
            "Endpoint Status",
            styles[
                "NBSection"
            ]
        )
    )

    story.append(
        build_endpoint_status_table(
            reports,
            styles
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm
        )
    )

    story.append(
        Paragraph(
            "Priority Findings",
            styles[
                "NBSection"
            ]
        )
    )

    story.append(
        build_findings_table(
            issues,
            styles
        )
    )

    story.append(
        Spacer(
            1,
            6 * mm
        )
    )

    story.append(
        Paragraph(
            "Recommended Remediation Plan",
            styles[
                "NBSection"
            ]
        )
    )

    story.extend(
        build_recommendation_section(
            issues,
            styles
        )
    )

    story.append(
        Spacer(
            1,
            3 * mm
        )
    )

    story.append(
        Paragraph(
            "Assessment Scope",
            styles[
                "NBSection"
            ]
        )
    )

    story.append(
        Paragraph(
            (
                "The assessment reviews selected Windows endpoint "
                "configuration and security indicators including "
                "Windows version, hardware capacity, disk usage, "
                "Microsoft Defender status, real-time protection, "
                "Windows Firewall profiles, pending Windows updates, "
                "Microsoft Office / Microsoft 365 presence, local "
                "Windows users and local administrator membership."
            ),
            styles[
                "NBBody"
            ]
        )
    )

    story.append(
        Spacer(
            1,
            3 * mm
        )
    )

    story.append(
        Paragraph(
            "Important Notes",
            styles[
                "NBSection"
            ]
        )
    )

    story.append(
        Paragraph(
            (
                "This is a lightweight endpoint configuration "
                "assessment and should not be treated as a complete "
                "vulnerability assessment, penetration test, EDR "
                "platform, compliance certification or guarantee "
                "of security. Findings should be reviewed in the "
                "context of the customer's operational and security "
                "requirements."
            ),
            styles[
                "NBBody"
            ]
        )
    )

    story.append(
        Spacer(
            1,
            5 * mm
        )
    )

    story.append(
        build_contact_cta(
            styles
        )
    )

    story.append(
        Spacer(
            1,
            4 * mm
        )
    )

    story.append(
        Paragraph(
            (
                f"Generated by {APP_NAME} "
                f"v{APP_VERSION} | "
                f"Assessment Reference: {report_reference}"
            ),
            styles[
                "NBMuted"
            ]
        )
    )

    document.build(
        story
    )

    return report_reference


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate a customer-facing PDF from "
            "Nanobricks Endpoint Assessment V3 JSON files."
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
            "Customer or company name."
        )
    )

    parser.add_argument(
        "--output-folder",
        help=(
            "Optional output folder. "
            "Defaults to Consolidated-Report."
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

    versions = get_collector_versions(
        reports
    )

    if len(
        versions
    ) > 1:
        print()
        print(
            "WARNING: Mixed collector versions detected:"
        )

        for version in versions:
            print(
                f"- {version}"
            )

        print()

    elif (
        len(
            versions
        ) == 1
        and versions[
            0
        ] != EXPECTED_COLLECTOR_VERSION
    ):
        print()
        print(
            "WARNING: Report uses collector version "
            f"{versions[0]}."
        )

        print(
            "Current recommended collector version is "
            f"{EXPECTED_COLLECTOR_VERSION}."
        )

        print()

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
            f"{safe_customer}.pdf"
        )
    )

    report_reference = build_pdf(
        reports,
        args.customer,
        output_file
    )

    metrics = aggregate_environment(
        reports
    )

    print()
    print("=" * 72)

    print(
        "NANOBRICKS BUSINESS ENDPOINT PDF"
    )

    print("=" * 72)

    print(
        f"PDF Builder version: {APP_VERSION}"
    )

    print(
        f"Assessment Reference: {report_reference}"
    )

    print(
        f"Customer: {args.customer}"
    )

    print(
        f"Endpoints processed: "
        f"{metrics['endpoint_count']}"
    )

    print(
        "Collector version(s): "
        + ", ".join(
            versions
        )
    )

    print(
        f"PASS findings: "
        f"{metrics['total_pass']}"
    )

    print(
        f"REVIEW findings: "
        f"{metrics['total_review']}"
    )

    print(
        f"FAIL findings: "
        f"{metrics['total_fail']}"
    )

    print()

    print(
        "PDF report created:"
    )

    print(
        output_file
    )

    if LOGO_PATH.exists():
        print(
            f"Logo used: {LOGO_PATH.name}"
        )

    else:
        print(
            "Logo not found. "
            "Text-only header used."
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