import json
from datetime import datetime, timezone

from collector import get_system_info
from assessor import assess_system


REPORT_FILE = "endpoint-report.json"


def build_report():
    system_info = get_system_info()
    findings = assess_system(system_info)

    summary = {
        "pass": 0,
        "review": 0,
        "fail": 0,
        "total": len(findings)
    }

    for finding in findings:
        status = finding["status"].lower()

        if status in summary:
            summary[status] += 1

    report = {
        "scanner": {
            "name": "Nanobricks Endpoint Assessment",
            "version": "1.0.0",
            "generated_at_utc": datetime.now(
                timezone.utc
            ).isoformat()
        },

        "endpoint": {
            "hostname": system_info["hostname"],
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

        "summary": summary,

        "findings": findings
    }

    return report


def save_report(report):
    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4
        )


def print_summary(report):
    summary = report["summary"]

    print("\n" + "=" * 60)
    print("NANOBRICKS ENDPOINT ASSESSMENT SUMMARY")
    print("=" * 60)

    print(
        f"PASS:   {summary['pass']}"
    )

    print(
        f"REVIEW: {summary['review']}"
    )

    print(
        f"FAIL:   {summary['fail']}"
    )

    print(
        f"TOTAL:  {summary['total']}"
    )

    print("=" * 60)

    print(
        f"Report saved to: {REPORT_FILE}"
    )


if __name__ == "__main__":
    report = build_report()
    save_report(report)
    print_summary(report)