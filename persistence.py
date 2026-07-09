#!/usr/bin/env python3
import os
import sys

def add_persistence():
    script_path = os.path.abspath(sys.argv[0])
    
    # Méthode 1 : cron (toutes les 5 minutes)
    cron_command = f"@reboot python3 {script_path}\n"
    
    try:
        os.system(f'(crontab -l 2>/dev/null; echo "{cron_command}") | crontab -')
        print("[+] Persistence ajoutée via crontab")
    except Exception as e:
        print(f"[-] Erreur cron: {e}")

if __name__ == "__main__":
    add_persistence()
