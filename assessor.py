from collector import get_system_info


def create_finding(
    check,
    status,
    category,
    current_value,
    expected,
    recommendation
):
    return {
        "check": check,
        "status": status,
        "category": category,
        "current_value": current_value,
        "expected": expected,
        "recommendation": recommendation
    }


def assess_system(info):
    findings = []

    # ========================================================
    # WINDOWS VERSION
    # ========================================================

    if info["os"] == "Windows" and info["os_release"] == "11":

        findings.append(
            create_finding(
                "Operating System",
                "PASS",
                "System",
                "Windows 11",
                "Windows 11",
                "No action required."
            )
        )

    else:

        findings.append(
            create_finding(
                "Operating System",
                "FAIL",
                "System",
                f"{info['os']} {info['os_release']}",
                "Windows 11",
                "Upgrade the endpoint to a supported Windows 11 edition."
            )
        )


    # ========================================================
    # RAM
    # ========================================================

    ram = info["ram_gb"]

    if ram >= 8:

        status = "PASS"
        recommendation = "RAM meets the endpoint baseline."

    elif ram >= 4:

        status = "REVIEW"
        recommendation = "Consider upgrading the system to at least 8 GB RAM."

    else:

        status = "FAIL"
        recommendation = "Upgrade RAM to at least 8 GB."

    findings.append(
        create_finding(
            "System Memory",
            status,
            "Hardware",
            f"{ram} GB",
            "8 GB or greater",
            recommendation
        )
    )


    # ========================================================
    # DISK SPACE
    # ========================================================

    free_percentage = round(
        (
            info["disk_free_gb"]
            / info["disk_total_gb"]
        ) * 100,
        1
    )

    if free_percentage >= 15:

        status = "PASS"
        recommendation = "Disk has sufficient free space."

    elif free_percentage >= 10:

        status = "REVIEW"
        recommendation = (
            "Disk space is becoming low. "
            "Consider cleanup or capacity expansion."
        )

    else:

        status = "FAIL"
        recommendation = (
            "Free disk space is critically low. "
            "Remove unnecessary files or increase storage capacity."
        )

    findings.append(
        create_finding(
            "Disk Free Space",
            status,
            "Hardware",
            (
                f"{info['disk_free_gb']} GB free "
                f"({free_percentage}%)"
            ),
            "At least 15% free disk space",
            recommendation
        )
    )


    # ========================================================
    # MICROSOFT DEFENDER
    # ========================================================

    defender = info["defender"]

    if not defender["available"]:

        findings.append(
            create_finding(
                "Microsoft Defender",
                "REVIEW",
                "Security",
                "Unable to determine",
                "Defender available and enabled",
                "Verify antivirus protection manually."
            )
        )

    elif (
        defender["antivirus_enabled"]
        and defender["realtime_protection"]
    ):

        findings.append(
            create_finding(
                "Microsoft Defender",
                "PASS",
                "Security",
                "Enabled with real-time protection",
                "Enabled",
                "No action required."
            )
        )

    else:

        findings.append(
            create_finding(
                "Microsoft Defender",
                "FAIL",
                "Security",
                "Protection disabled or incomplete",
                "Antivirus and real-time protection enabled",
                "Enable Microsoft Defender and real-time protection."
            )
        )


    # ========================================================
    # WINDOWS FIREWALL
    # ========================================================

    firewall = info["firewall"]

    if not firewall["available"]:

        firewall_status = "REVIEW"
        firewall_value = "Unable to determine"

    else:

        all_enabled = all(
            profile["enabled"]
            for profile in firewall["profiles"]
        )

        if all_enabled:
            firewall_status = "PASS"
            firewall_value = "All profiles enabled"
        else:
            firewall_status = "FAIL"
            firewall_value = "One or more profiles disabled"

    findings.append(
        create_finding(
            "Windows Firewall",
            firewall_status,
            "Security",
            firewall_value,
            "Domain, Private and Public profiles enabled",
            (
                "No action required."
                if firewall_status == "PASS"
                else "Enable Windows Firewall on all profiles."
            )
        )
    )


    # ========================================================
    # WINDOWS UPDATE
    # ========================================================

    update = info["windows_update"]

    if not update["available"]:

        status = "REVIEW"
        current = "Unable to determine"
        recommendation = "Check Windows Update manually."

    else:

        pending = update["pending_updates"]

        if pending == 0:

            status = "PASS"
            recommendation = "No pending Windows updates."

        elif pending <= 5:

            status = "REVIEW"
            recommendation = "Install the pending Windows updates."

        else:

            status = "FAIL"
            recommendation = (
                "Multiple Windows updates are pending. "
                "Patch the endpoint as soon as practical."
            )

        current = f"{pending} pending update(s)"

    findings.append(
        create_finding(
            "Windows Update",
            status,
            "Patch Management",
            current,
            "No pending updates",
            recommendation
        )
    )


    # ========================================================
    # MICROSOFT OFFICE
    # ========================================================

    office = info["office"]

    if office["available"] and office["installed"]:

        findings.append(
            create_finding(
                "Microsoft Office",
                "PASS",
                "Software",
                office.get("product", "Installed"),
                "Microsoft Office / Microsoft 365 installed",
                "Keep Office updated."
            )
        )

    else:

        findings.append(
            create_finding(
                "Microsoft Office",
                "REVIEW",
                "Software",
                "Not detected",
                "Microsoft Office / Microsoft 365",
                "Verify whether Office is required for this employee."
            )
        )


    # ========================================================
    # LOCAL ACCOUNTS
    # ========================================================

    local_users = info["local_users"]

    if local_users["available"]:

        for user in local_users["users"]:

            if (
                user.get("Enabled")
                and not user.get("PasswordRequired")
            ):

                findings.append(
                    create_finding(
                        f"Account Password Review - {user.get('Name')}",
                        "REVIEW",
                        "Identity",
                        "PasswordRequired property is False",
                        "User authentication required",
                        (
                            "Verify that this account is protected "
                            "by a password, Windows Hello, PIN, "
                            "or another approved authentication method."
                        )
                    )
                )


    # ========================================================
    # BUILT-IN ADMINISTRATOR
    # ========================================================

    administrator = next(
        (
            user
            for user in local_users.get("users", [])
            if user.get("Name") == "Administrator"
        ),
        None
    )

    if administrator:

        if administrator.get("Enabled"):

            findings.append(
                create_finding(
                    "Built-in Administrator Account",
                    "REVIEW",
                    "Identity",
                    "Enabled",
                    "Disabled when not required",
                    "Disable the built-in Administrator account if not required."
                )
            )

        else:

            findings.append(
                create_finding(
                    "Built-in Administrator Account",
                    "PASS",
                    "Identity",
                    "Disabled",
                    "Disabled when not required",
                    "No action required."
                )
            )


    return findings


def print_assessment(findings):

    print("\n")
    print("=" * 75)
    print("NANOBRICKS ENDPOINT SECURITY ASSESSMENT")
    print("=" * 75)

    for finding in findings:

        print(
            f"{finding['status']:<7} "
            f"{finding['check']}"
        )

        print(
            f"        Current: "
            f"{finding['current_value']}"
        )

        print(
            f"        Expected: "
            f"{finding['expected']}"
        )

        print(
            f"        Action: "
            f"{finding['recommendation']}"
        )

        print("-" * 75)


if __name__ == "__main__":

    system_info = get_system_info()

    assessment = assess_system(
        system_info
    )

    print_assessment(
        assessment
    )