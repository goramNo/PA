#!/usr/bin/env python3

import subprocess
import json
import socket
import ipaddress
import re
from datetime import datetime


def get_local_ip():
    """
    Retourne l'adresse IP principale du Raspberry.
    """

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()

    return ip


def get_network():

    ip = get_local_ip()

    output = subprocess.check_output(
        ["ip", "-o", "-f", "inet", "addr", "show"],
        text=True
    )

    for line in output.splitlines():

        if ip in line:

            match = re.search(r"inet ([0-9./]+)", line)

            if match:

                network = ipaddress.ip_interface(
                    match.group(1)
                ).network

                return str(network)

    return str(ipaddress.ip_network(ip + "/24", strict=False))


def empty_result():

    return {

        "module": "network_scanner",

        "status": "failed",

        "timestamp": datetime.utcnow().isoformat(),

        "network_range": "",

        "hosts": [],

        "errors": []

    }


def parse_nmap(text):

    hosts = []

    current = None

    for line in text.splitlines():

        if line.startswith("Nmap scan report for"):

            if current:

                hosts.append(current)

            current = {
                "hostname": "",
                "ip": "",
                "ports": []
            }

            info = line.replace(
                "Nmap scan report for ",
                ""
            )

            m = re.search(r"\((.*?)\)", info)

            if m:

                current["ip"] = m.group(1)
                current["hostname"] = info.replace(
                    f"({m.group(1)})",
                    ""
                ).strip()

            else:

                current["ip"] = info.strip()

        elif "/tcp" in line:

            cols = line.split()

            if len(cols) >= 3:

                current["ports"].append({

                    "port": cols[0],

                    "state": cols[1],

                    "service": cols[2]

                })

    if current:

        hosts.append(current)

    return hosts
def run_network_scan():

    result = empty_result()

    network = get_network()

    result["network_range"] = network

    print(f"[scanner] Target network range : {network}")

    try:

        print("[scanner] Phase 1 : découverte des hôtes...")

        discovery = subprocess.run(

            [
                "nmap",
                "-sn",
                network
            ],

            capture_output=True,
            text=True,
            timeout=60

        )

        if discovery.returncode != 0:

            result["errors"].append(discovery.stderr)

            return result

        hosts = []

        for line in discovery.stdout.splitlines():

            if "Nmap scan report for" in line:

                ip = line.split()[-1]

                hosts.append(ip)

        if len(hosts) == 0:

            print("[scanner] Aucun hôte trouvé.")

            result["status"] = "completed"

            return result

        print(f"[scanner] {len(hosts)} hôte(s) trouvé(s).")

        result["hosts"] = []

        for host in hosts:

            print(f"[scanner] Scan de {host}...")

            scan = subprocess.run(

                [
                    "nmap",
                    "-Pn",
                    "-sV",
                    "--top-ports",
                    "20",
                    host
                ],

                capture_output=True,
                text=True,
                timeout=90

            )

            if scan.returncode != 0:

                print(f"[scanner] Impossible de scanner {host}")

                continue

            parsed = parse_nmap(scan.stdout)

            if len(parsed):

                result["hosts"].append(parsed[0])

        result["status"] = "completed"

        print(
            f"[scanner] Scan terminé ({len(result['hosts'])} hôte(s))."
        )

        return result

    except subprocess.TimeoutExpired:

        result["errors"].append("Le scan Nmap a dépassé le temps limite.")

        return result

    except FileNotFoundError:

        result["errors"].append("Nmap n'est pas installé.")

        return result

    except Exception as e:

        result["errors"].append(str(e))

        return result

if __name__ == "__main__":

    result = run_network_scan()

    print("\n==============================")
    print("SCAN SUMMARY")
    print("==============================")

    print(json.dumps(
        result,
        indent=4,
        ensure_ascii=False
    ))
