import json
import socket
from datetime import datetime, timezone
from pathlib import Path

import requests

from collector import get_system_info
from assessor import assess_system


OUTPUT_DIR = Path("endpoint-data")

API_URL = "http://127.0.0.1:8000/api/endpoints"


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
            "version": "1.1.0",
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

        "summary": summary,

        "findings": findings
    }

    return package


def save_endpoint_package(package):
    OUTPUT_DIR.mkdir(
        exist_ok=True
    )

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


def send_to_api(package):
    try:
        response = requests.post(
            API_URL,
            json=package,
            timeout=10
        )

        if response.status_code == 200:
            return {
                "success": True,
                "response": response.json()
            }

        return {
            "success": False,
            "error": (
                f"API returned status "
                f"{response.status_code}"
            )
        }

    except requests.RequestException as error:
        return {
            "success": False,
            "error": str(error)
        }


def print_summary(
    package,
    filename,
    api_result
):
    summary = package["summary"]

    print("\n" + "=" * 65)
    print("NANOBRICKS ENDPOINT COLLECTOR")
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

    print(
        "Local endpoint package:"
    )

    print(
        filename
    )

    print("-" * 65)

    if api_result["success"]:

        print(
            "API Submission: SUCCESS"
        )

        response = api_result[
            "response"
        ]

        print(
            f"Stored Endpoint: "
            f"{response.get('hostname')}"
        )

        print(
            f"API File: "
            f"{response.get('stored_as')}"
        )

    else:

        print(
            "API Submission: FAILED"
        )

        print(
            api_result.get(
                "error",
                "Unknown error"
            )
        )

    print("=" * 65)


if __name__ == "__main__":
    endpoint_package = build_endpoint_package()

    output_file = save_endpoint_package(
        endpoint_package
    )

    api_result = send_to_api(
        endpoint_package
    )

    print_summary(
        endpoint_package,
        output_file,
        api_result
    )