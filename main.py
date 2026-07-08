#!/usr/bin/env python3

from datetime import datetime, timezone

from scanner import run_network_scan
from c2_client.client import send_to_c2


def banner():
    print("=" * 60)
    print("        RED TEAM TOOL - Raspberry Pi Zero 2 W")
    print("        Environnement pédagogique contrôlé")
    print("=" * 60)


def build_payload():

    return {
        "agent": {
            "hostname": "raspberrypi",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": "passive"
        },
        "modules": {}
    }


def run_scanner():

    payload = build_payload()

    print("[+] Lancement du module Scanner")

    payload["modules"]["scanner"] = run_network_scan()

    print("[+] Envoi au serveur C2...")

    send_to_c2(payload)

    print("[+] Fin du scan.")

    return True


if __name__ == "__main__":

    banner()
    run_scanner()
