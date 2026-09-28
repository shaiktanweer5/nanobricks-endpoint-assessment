import platform
import socket
import psutil
import subprocess
import json


def run_powershell(command):
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            command
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return None

    return result.stdout.strip()


def get_defender_status():
    command = """
    Get-MpComputerStatus |
    Select-Object AntivirusEnabled,
                  RealTimeProtectionEnabled,
                  AntivirusSignatureLastUpdated |
    ConvertTo-Json
    """

    output = run_powershell(command)

    if not output:
        return {
            "available": False
        }

    try:
        data = json.loads(output)

        return {
            "available": True,
            "antivirus_enabled": data.get("AntivirusEnabled"),
            "realtime_protection": data.get("RealTimeProtectionEnabled"),
            "signature_updated": data.get("AntivirusSignatureLastUpdated")
        }

    except json.JSONDecodeError:
        return {
            "available": False
        }


def get_firewall_status():
    command = """
    Get-NetFirewallProfile |
    Select-Object Name, Enabled |
    ConvertTo-Json
    """

    output = run_powershell(command)

    if not output:
        return {
            "available": False,
            "profiles": []
        }

    try:
        data = json.loads(output)

        if isinstance(data, dict):
            data = [data]

        profiles = []

        for profile in data:
            profiles.append({
                "name": profile.get("Name"),
                "enabled": bool(profile.get("Enabled"))
            })

        return {
            "available": True,
            "profiles": profiles
        }

    except json.JSONDecodeError:
        return {
            "available": False,
            "profiles": []
        }


def get_windows_update_status():
    command = """
    $session = New-Object -ComObject Microsoft.Update.Session
    $searcher = $session.CreateUpdateSearcher()
    $result = $searcher.Search("IsInstalled=0 and IsHidden=0")

    [PSCustomObject]@{
        PendingUpdates = $result.Updates.Count
    } | ConvertTo-Json
    """

    output = run_powershell(command)

    if not output:
        return {
            "available": False,
            "pending_updates": None
        }

    try:
        data = json.loads(output)

        return {
            "available": True,
            "pending_updates": data.get("PendingUpdates")
        }

    except json.JSONDecodeError:
        return {
            "available": False,
            "pending_updates": None
        }


def get_office_status():
    command = """
    $officePath = "HKLM:\\SOFTWARE\\Microsoft\\Office\\ClickToRun\\Configuration"

    if (Test-Path $officePath) {

        $office = Get-ItemProperty $officePath

        [PSCustomObject]@{
            Installed = $true
            Product = $office.ProductReleaseIds
            Version = $office.VersionToReport
            Platform = $office.Platform
        } | ConvertTo-Json

    } else {

        $officeApps = Get-ItemProperty `
            "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*" `
            -ErrorAction SilentlyContinue |
            Where-Object {
                $_.DisplayName -match "Microsoft 365|Microsoft Office"
            } |
            Select-Object -First 1

        if ($officeApps) {

            [PSCustomObject]@{
                Installed = $true
                Product = $officeApps.DisplayName
                Version = $officeApps.DisplayVersion
                Platform = "Unknown"
            } | ConvertTo-Json

        } else {

            [PSCustomObject]@{
                Installed = $false
                Product = $null
                Version = $null
                Platform = $null
            } | ConvertTo-Json
        }
    }
    """

    output = run_powershell(command)

    if not output:
        return {
            "available": False,
            "installed": None
        }

    try:
        data = json.loads(output)

        return {
            "available": True,
            "installed": data.get("Installed"),
            "product": data.get("Product"),
            "version": data.get("Version"),
            "platform": data.get("Platform")
        }

    except json.JSONDecodeError:
        return {
            "available": False,
            "installed": None
        }


def get_local_users():
    command = """
    $users = Get-LocalUser |
    Select-Object Name, Enabled, PasswordRequired

    $admins = Get-LocalGroupMember -Group "Administrators" |
    Select-Object Name, ObjectClass

    [PSCustomObject]@{
        Users = $users
        Administrators = $admins
    } | ConvertTo-Json -Depth 4
    """

    output = run_powershell(command)

    if not output:
        return {
            "available": False,
            "users": [],
            "administrators": []
        }

    try:
        data = json.loads(output)

        users = data.get("Users", [])
        admins = data.get("Administrators", [])

        if isinstance(users, dict):
            users = [users]

        if isinstance(admins, dict):
            admins = [admins]

        return {
            "available": True,
            "users": users,
            "administrators": admins
        }

    except json.JSONDecodeError:
        return {
            "available": False,
            "users": [],
            "administrators": []
        }


def get_system_info():
    disk = psutil.disk_usage("C:\\")

    info = {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_version": platform.version(),
        "os_release": platform.release(),
        "processor": platform.processor(),
        "architecture": platform.machine(),

        "ram_gb": round(
            psutil.virtual_memory().total / (1024 ** 3),
            2
        ),

        "disk_total_gb": round(
            disk.total / (1024 ** 3),
            2
        ),

        "disk_free_gb": round(
            disk.free / (1024 ** 3),
            2
        ),

        "disk_used_percent": disk.percent,

        "defender": get_defender_status(),
        "firewall": get_firewall_status(),
        "windows_update": get_windows_update_status(),
        "office": get_office_status(),
        "local_users": get_local_users()
    }

    return info


def print_report(info):
    print("\n" + "=" * 60)
    print("NANOBRICKS ENDPOINT ASSESSMENT")
    print("=" * 60)

    print(f"Hostname:        {info['hostname']}")
    print(f"OS:              {info['os']}")
    print(f"OS Release:      {info['os_release']}")
    print(f"OS Version:      {info['os_version']}")
    print(f"Architecture:    {info['architecture']}")
    print(f"Processor:       {info['processor']}")
    print(f"RAM:             {info['ram_gb']} GB")
    print(f"Disk Total:      {info['disk_total_gb']} GB")
    print(f"Disk Free:       {info['disk_free_gb']} GB")
    print(f"Disk Used:       {info['disk_used_percent']}%")

    print("\nMICROSOFT DEFENDER")
    print("-" * 60)

    defender = info["defender"]

    if not defender["available"]:
        print("Defender Status: Unable to read")
    else:
        print(f"Antivirus Enabled:       {defender['antivirus_enabled']}")
        print(f"Real-Time Protection:    {defender['realtime_protection']}")
        print(f"Signature Last Updated:  {defender['signature_updated']}")

    print("\nWINDOWS FIREWALL")
    print("-" * 60)

    firewall = info["firewall"]

    if not firewall["available"]:
        print("Firewall Status: Unable to read")
    else:
        for profile in firewall["profiles"]:
            print(
                f"{profile['name']} Profile: "
                f"{profile['enabled']}"
            )

    print("\nWINDOWS UPDATE")
    print("-" * 60)

    update = info["windows_update"]

    if not update["available"]:
        print("Windows Update Status: Unable to read")
    else:
        print(
            f"Pending Updates: "
            f"{update['pending_updates']}"
        )

    print("\nMICROSOFT OFFICE")
    print("-" * 60)

    office = info["office"]

    if not office["available"]:
        print("Office Status: Unable to read")

    elif not office["installed"]:
        print("Office Installed: False")

    else:
        print("Office Installed: True")
        print(f"Product:          {office['product']}")
        print(f"Version:          {office['version']}")
        print(f"Platform:         {office['platform']}")

    print("\nLOCAL WINDOWS USERS")
    print("-" * 60)

    local_users = info["local_users"]

    if not local_users["available"]:
        print("Local User Status: Unable to read")

    else:
        for user in local_users["users"]:
            print(
                f"User: {user.get('Name')} | "
                f"Enabled: {user.get('Enabled')} | "
                f"Password Required: {user.get('PasswordRequired')}"
            )

        print("\nLOCAL ADMINISTRATORS")
        print("-" * 60)

        for admin in local_users["administrators"]:
            print(
                f"Admin: {admin.get('Name')} | "
                f"Type: {admin.get('ObjectClass')}"
            )

    print("=" * 60)


if __name__ == "__main__":
    system_info = get_system_info()
    print_report(system_info)