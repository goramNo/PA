#!/usr/bin/env python3
import platform
import os
import json
import subprocess
from datetime import datetime

def collect_windows_info():
    """Collecte les infos sur Windows"""
    data = {
        "Hostname": platform.node(),
        "Username": os.getenv('USERNAME') or os.getenv('USER') or 'unknown',
        "OS": platform.platform(),
        "Architecture": platform.machine(),
        "Python_Version": platform.python_version(),
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Users": []
    }

    try:
        # Récupération des utilisateurs locaux via PowerShell
        cmd = 'powershell -Command "Get-LocalUser | Select-Object Name, Enabled, LastLogon, Description | ConvertTo-Json"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0 and result.stdout.strip():
            users = json.loads(result.stdout)
            if isinstance(users, dict):
                users = [users]
            data["Users"] = users
        else:
            data["Users"] = ["Impossible de récupérer les utilisateurs"]
    except Exception as e:
        data["Users"] = [f"Erreur: {str(e)}"]

    return data


def collect_linux_info():
    """Collecte les infos sur Linux"""
    data = {
        "Hostname": platform.node(),
        "Username": os.getenv('USER') or 'unknown',
        "OS": platform.platform(),
        "Architecture": platform.machine(),
        "Python_Version": platform.python_version(),
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Users": []
    }

    try:
        with open("/etc/passwd", "r") as f:
            for line in f:
                parts = line.strip().split(":")
                if len(parts) >= 1:
                    data["Users"].append({"Name": parts[0]})
        data["Users"] = data["Users"][:15]
    except Exception as e:
        data["Users"] = [f"Erreur: {str(e)}"]

    return data


def collect_system_info():
    system = platform.system()
    if system == "Windows":
        return collect_windows_info()
    elif system == "Linux":
        return collect_linux_info()
    else:
        return {
            "Hostname": platform.node(),
            "OS": platform.platform(),
            "Error": f"OS non supporté: {system}",
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


if __name__ == "__main__":
    info = collect_system_info()

    output_path = "/opt/redteam_tool/results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=4, ensure_ascii=False)

    print(f"[+] Données collectées → {output_path}")
