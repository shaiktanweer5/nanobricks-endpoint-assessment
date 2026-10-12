import json
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

from collector import get_system_info
from assessor import assess_system
from build_html_report import generate_report


if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
else:
    APP_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = APP_DIR / "endpoint-data"


def build_endpoint_package():
    system_info = get_system_info()
    findings = assess_system(system_info)

    summary = {
        "pass": 0,
        "review": 0,
        "fail": 0,
        "total": len(findings)
    }

    for finding in findings:
        status = finding.get(
            "status",
            ""
        ).lower()

        if status in summary:
            summary[status] += 1

    hostname = socket.gethostname()

    package = {
        "agent": {
            "name": "Nanobricks Endpoint Collector",
            "version": "3.0.0",
            "collected_at_utc": datetime.now(
                timezone.utc
            ).isoformat()
        },

        "endpoint": {
            "hostname": hostname,
            "operating_system": (
                f"{system_info['os']} "
                f"{system_info['os_release']}"
            ),
            "os_version": system_info["os_version"],
            "architecture": system_info["architecture"],
            "processor": system_info["processor"],
            "ram_gb": system_info["ram_gb"],
            "disk_total_gb": system_info["disk_total_gb"],
            "disk_free_gb": system_info["disk_free_gb"],
            "disk_used_percent": system_info[
                "disk_used_percent"
            ]
        },

        "raw_data": {
            "defender": system_info.get(
                "defender",
                {}
            ),

            "firewall": system_info.get(
                "firewall",
                {}
            ),

            "windows_update": system_info.get(
                "windows_update",
                {}
            ),

            "office": system_info.get(
                "office",
                {}
            ),

            "local_users": system_info.get(
                "local_users",
                {}
            )
        },

        "summary": summary,

        "findings": findings
    }

    return package


def get_safe_hostname(package):
    hostname = package[
        "endpoint"
    ][
        "hostname"
    ]

    safe_hostname = "".join(
        character
        if character.isalnum()
        or character in "-_"
        else "_"
        for character in hostname
    )

    return safe_hostname


def save_endpoint_package(package):
    OUTPUT_DIR.mkdir(
        exist_ok=True
    )

    safe_hostname = get_safe_hostname(
        package
    )

    filename = (
        OUTPUT_DIR
        / f"{safe_hostname}-assessment.json"
    )

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            package,
            file,
            indent=4
        )

    return filename


def save_html_report(package):
    OUTPUT_DIR.mkdir(
        exist_ok=True
    )

    safe_hostname = get_safe_hostname(
        package
    )

    filename = (
        OUTPUT_DIR
        / f"{safe_hostname}-assessment.html"
    )

    report_html = generate_report(
        package
    )

    filename.write_text(
        report_html,
        encoding="utf-8"
    )

    return filename


def print_summary(
    package,
    json_filename,
    html_filename
):
    summary = package["summary"]

    print()
    print("=" * 65)
    print("NANOBRICKS ENDPOINT ASSESSMENT V2")
    print("=" * 65)

    print(
        f"Hostname: "
        f"{package['endpoint']['hostname']}"
    )

    print(
        f"Operating System: "
        f"{package['endpoint']['operating_system']}"
    )

    print("-" * 65)

    print(
        f"PASS:   "
        f"{summary['pass']}"
    )

    print(
        f"REVIEW: "
        f"{summary['review']}"
    )

    print(
        f"FAIL:   "
        f"{summary['fail']}"
    )

    print(
        f"TOTAL:  "
        f"{summary['total']}"
    )

    print("-" * 65)

    print("JSON assessment created:")
    print(
        json_filename.resolve()
    )

    print()

    print("HTML report created:")
    print(
        html_filename.resolve()
    )

    print("=" * 65)


if __name__ == "__main__":
    endpoint_package = build_endpoint_package()

    json_output_file = save_endpoint_package(
        endpoint_package
    )

    html_output_file = save_html_report(
        endpoint_package
    )

    print_summary(
        endpoint_package,
        json_output_file,
        html_output_file
    )