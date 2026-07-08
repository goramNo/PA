#!/usr/bin/env python3
"""
hid_keyboard.py corrigé - Gestion correcte de l'erreur 11 (EAGAIN)
"""

import time
import struct
import os
from pathlib import Path

HID_DEVICE  = "/dev/hidg0"
DELAY_KEY   = 0.035
DELAY_WIN_R = 1.0
DELAY_ENTER = 2.0

MOD_NONE  = 0x00
MOD_SHIFT = 0x02
MOD_GUI   = 0x08
MOD_CTRL  = 0x01

KEY_ENTER = 0x28
KEY_R     = 0x15

AZERTY = {
    'a':(MOD_NONE,0x14),'b':(MOD_NONE,0x05),'c':(MOD_NONE,0x06),
    'd':(MOD_NONE,0x07),'e':(MOD_NONE,0x08),'f':(MOD_NONE,0x09),
    'g':(MOD_NONE,0x0A),'h':(MOD_NONE,0x0B),'i':(MOD_NONE,0x0C),
    'j':(MOD_NONE,0x0D),'k':(MOD_NONE,0x0E),'l':(MOD_NONE,0x0F),
    'm':(MOD_NONE,0x33),'n':(MOD_NONE,0x11),'o':(MOD_NONE,0x12),
    'p':(MOD_NONE,0x13),'q':(MOD_NONE,0x04),'r':(MOD_NONE,0x15),
    's':(MOD_NONE,0x16),'t':(MOD_NONE,0x17),'u':(MOD_NONE,0x18),
    'v':(MOD_NONE,0x19),'w':(MOD_NONE,0x1D),'x':(MOD_NONE,0x1B),
    'y':(MOD_NONE,0x1C),'z':(MOD_NONE,0x1C),
    'A':(MOD_SHIFT,0x14),'B':(MOD_SHIFT,0x05),'C':(MOD_SHIFT,0x06),
    'D':(MOD_SHIFT,0x07),'E':(MOD_SHIFT,0x08),'F':(MOD_SHIFT,0x09),
    'G':(MOD_SHIFT,0x0A),'H':(MOD_SHIFT,0x0B),'I':(MOD_SHIFT,0x0C),
    'J':(MOD_SHIFT,0x0D),'K':(MOD_SHIFT,0x0E),'L':(MOD_SHIFT,0x0F),
    'M':(MOD_SHIFT,0x33),'N':(MOD_SHIFT,0x11),'O':(MOD_SHIFT,0x12),
    'P':(MOD_SHIFT,0x13),'Q':(MOD_SHIFT,0x04),'R':(MOD_SHIFT,0x15),
    'S':(MOD_SHIFT,0x16),'T':(MOD_SHIFT,0x17),'U':(MOD_SHIFT,0x18),
    'V':(MOD_SHIFT,0x19),'W':(MOD_SHIFT,0x1A),'X':(MOD_SHIFT,0x1B),
    'Y':(MOD_SHIFT,0x1C),'Z':(MOD_SHIFT,0x1D),
    '0':(MOD_SHIFT,0x27),'1':(MOD_SHIFT,0x1E),'2':(MOD_SHIFT,0x1F),
    '3':(MOD_SHIFT,0x20),'4':(MOD_SHIFT,0x21),'5':(MOD_SHIFT,0x22),
    '6':(MOD_SHIFT,0x23),'7':(MOD_SHIFT,0x24),'8':(MOD_SHIFT,0x25),
    '9':(MOD_SHIFT,0x26),
    ' ':(MOD_NONE,0x2C), '\n':(MOD_NONE,0x28),
    '-':(MOD_NONE,0x38), '_':(MOD_SHIFT,0x38),
    '.':(MOD_SHIFT,0x36), ',':(MOD_NONE,0x36),
    ':':(MOD_NONE,0x37), ';':(MOD_SHIFT,0x37),
    "'":(MOD_NONE,0x34), '"':(MOD_SHIFT,0x34),
    '(': (MOD_NONE,0x22), ')':(MOD_NONE,0x2D),
    '=':(MOD_NONE,0x2e), '+':(MOD_SHIFT,0x2e),
    '!':(MOD_SHIFT,0x1E), '?':(MOD_SHIFT,0x2C),
    # ... (garde le reste de ton dictionnaire)
}

def _safe_write(hid, data: bytes):
    """Écriture robuste qui gère l'erreur 11 (EAGAIN)"""
    try:
        hid.write(data)
        hid.flush()
    except BlockingIOError:
        time.sleep(0.02)
        try:
            hid.write(data)
            hid.flush()
        except BlockingIOError:
            time.sleep(0.05)

def _send_key(hid, modifier: int, keycode: int) -> None:
    _safe_write(hid, struct.pack("8B", modifier, 0, keycode, 0, 0, 0, 0, 0))
    time.sleep(DELAY_KEY)
    _safe_write(hid, struct.pack("8B", 0, 0, 0, 0, 0, 0, 0, 0))
    time.sleep(DELAY_KEY)

def _win_r(hid) -> None:
    _safe_write(hid, struct.pack("8B", MOD_GUI, 0, KEY_R, 0, 0, 0, 0, 0))
    time.sleep(DELAY_KEY)
    _safe_write(hid, struct.pack("8B", 0, 0, 0, 0, 0, 0, 0, 0))
    time.sleep(DELAY_KEY)

def _type(hid, text: str) -> None:
    for ch in text:
        if ch not in AZERTY:
            continue
        mod, kc = AZERTY[ch]
        _send_key(hid, mod, kc)

def type_payload(command: str) -> bool:
    if not Path(HID_DEVICE).exists():
        print(f"[hid] ERREUR : {HID_DEVICE} introuvable")
        return False

    try:
        with open(HID_DEVICE, "wb", buffering=0) as hid:
            print("[hid] → Win+R")
            _win_r(hid)
            time.sleep(DELAY_WIN_R)

            print(f"[hid] → Frappe ({len(command)} caractères)...")
            _type(hid, command)

            print("[hid] → Enter")
            _send_key(hid, MOD_NONE, KEY_ENTER)
            time.sleep(DELAY_ENTER)

        print("[hid] Séquence terminée.")
        return True

    except PermissionError:
        print(f"[hid] ERREUR : permission refusée — lancer avec sudo")
        return False
    except Exception as e:
        print(f"[hid] ERREUR : {e}")
        return False

def run_cmd(command):
    """Ouvre CMD et exécute une commande (version courte et fiable)."""
    import time
    import struct

    with open(HID_DEVICE, 'wb', buffering=0) as hid:
        # Win + R
        hid.write(struct.pack('8B', MOD_GUI, 0, KEY_R, 0, 0, 0, 0, 0))
        hid.flush()
        time.sleep(0.035)
        hid.write(struct.pack('8B', 0, 0, 0, 0, 0, 0, 0, 0))
        hid.flush()
        time.sleep(1.2)

        # Tape "cmd"
        for ch in 'cmd':
            if ch not in AZERTY: continue
            mod, kc = AZERTY[ch]
            hid.write(struct.pack('8B', mod, 0, kc, 0, 0, 0, 0, 0))
            hid.flush()
            time.sleep(0.025)
            hid.write(struct.pack('8B', 0, 0, 0, 0, 0, 0, 0, 0))
            hid.flush()
            time.sleep(0.025)

        # Enter
        hid.write(struct.pack('8B', MOD_NONE, 0, KEY_ENTER, 0, 0, 0, 0, 0))
        hid.flush()
        time.sleep(1.8)

        # Tape la commande
        for ch in command:
            if ch not in AZERTY: continue
            mod, kc = AZERTY[ch]
            hid.write(struct.pack('8B', mod, 0, kc, 0, 0, 0, 0, 0))
            hid.flush()
            time.sleep(0.025)
            hid.write(struct.pack('8B', 0, 0, 0, 0, 0, 0, 0, 0))
            hid.flush()
            time.sleep(0.025)

        # Enter
        hid.write(struct.pack('8B', MOD_NONE, 0, KEY_ENTER, 0, 0, 0, 0, 0))
        hid.flush()

def run_cmd(command):
    """Ouvre CMD et exécute une commande."""
    import time, struct
    with open(HID_DEVICE, 'wb', buffering=0) as hid:
        hid.write(struct.pack('8B', MOD_GUI, 0, KEY_R, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(0.035)
        hid.write(struct.pack('8B', 0, 0, 0, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(1.0)

        for ch in 'cmd':
            if ch not in AZERTY: continue
            mod, kc = AZERTY[ch]
            hid.write(struct.pack('8B', mod, 0, kc, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(0.025)
            hid.write(struct.pack('8B', 0, 0, 0, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(0.025)

        hid.write(struct.pack('8B', MOD_NONE, 0, KEY_ENTER, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(1.6)

        for ch in command:
            if ch not in AZERTY: continue
            mod, kc = AZERTY[ch]
            hid.write(struct.pack('8B', mod, 0, kc, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(0.025)
            hid.write(struct.pack('8B', 0, 0, 0, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(0.025)

        hid.write(struct.pack('8B', MOD_NONE, 0, KEY_ENTER, 0, 0, 0, 0, 0)); hid.flush()


def run_ps(command):
    """Ouvre PowerShell et exécute une commande (version rapide)."""
    import time, struct
    with open(HID_DEVICE, 'wb', buffering=0) as hid:
        hid.write(struct.pack('8B', MOD_GUI, 0, KEY_R, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(0.035)
        hid.write(struct.pack('8B', 0, 0, 0, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(1.0)

        for ch in 'powershell':
            if ch not in AZERTY: continue
            mod, kc = AZERTY[ch]
            hid.write(struct.pack('8B', mod, 0, kc, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(0.025)
            hid.write(struct.pack('8B', 0, 0, 0, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(0.025)

        hid.write(struct.pack('8B', MOD_NONE, 0, KEY_ENTER, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(2.0)

        for ch in command:
            if ch not in AZERTY: continue
            mod, kc = AZERTY[ch]
            hid.write(struct.pack('8B', mod, 0, kc, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(0.025)
            hid.write(struct.pack('8B', 0, 0, 0, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(0.025)

        hid.write(struct.pack('8B', MOD_NONE, 0, KEY_ENTER, 0, 0, 0, 0, 0)); hid.flush()

def run_cmd(command):
    """Ouvre CMD et exécute une commande."""
    import time, struct
    with open(HID_DEVICE, 'wb', buffering=0) as hid:
        hid.write(struct.pack('8B', MOD_GUI, 0, KEY_R, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(0.035)
        hid.write(struct.pack('8B', 0, 0, 0, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(1.0)

        for ch in 'cmd':
            if ch not in AZERTY: continue
            mod, kc = AZERTY[ch]
            hid.write(struct.pack('8B', mod, 0, kc, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(0.025)
            hid.write(struct.pack('8B', 0, 0, 0, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(0.025)

        hid.write(struct.pack('8B', MOD_NONE, 0, KEY_ENTER, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(1.6)

        for ch in command:
            if ch not in AZERTY: continue
            mod, kc = AZERTY[ch]
            hid.write(struct.pack('8B', mod, 0, kc, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(0.025)
            hid.write(struct.pack('8B', 0, 0, 0, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(0.025)

        hid.write(struct.pack('8B', MOD_NONE, 0, KEY_ENTER, 0, 0, 0, 0, 0)); hid.flush()


def run_ps(command):
    """Ouvre PowerShell et exécute une commande (version rapide)."""
    import time, struct
    with open(HID_DEVICE, 'wb', buffering=0) as hid:
        hid.write(struct.pack('8B', MOD_GUI, 0, KEY_R, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(0.035)
        hid.write(struct.pack('8B', 0, 0, 0, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(1.0)

        for ch in 'powershell':
            if ch not in AZERTY: continue
            mod, kc = AZERTY[ch]
            hid.write(struct.pack('8B', mod, 0, kc, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(0.025)
            hid.write(struct.pack('8B', 0, 0, 0, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(0.025)

        hid.write(struct.pack('8B', MOD_NONE, 0, KEY_ENTER, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(2.0)

        for ch in command:
            if ch not in AZERTY: continue
            mod, kc = AZERTY[ch]
            hid.write(struct.pack('8B', mod, 0, kc, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(0.025)
            hid.write(struct.pack('8B', 0, 0, 0, 0, 0, 0, 0, 0)); hid.flush(); time.sleep(0.025)

        hid.write(struct.pack('8B', MOD_NONE, 0, KEY_ENTER, 0, 0, 0, 0, 0)); hid.flush()

def run_cmd(command):
    """Ouvre cmd et exécute une commande (version stable)."""
    import time
    import struct

    with open(HID_DEVICE, 'wb', buffering=0) as hid:
        # Win+R
        hid.write(struct.pack('8B', MOD_GUI, 0, KEY_R, 0, 0, 0, 0, 0))
        hid.flush()
        time.sleep(0.035)
        hid.write(struct.pack('8B', 0, 0, 0, 0, 0, 0, 0, 0))
        hid.flush()
        time.sleep(1.0)

        # Tape "cmd"
        for ch in 'cmd':
            if ch not in AZERTY: continue
            mod, kc = AZERTY[ch]
            hid.write(struct.pack('8B', mod, 0, kc, 0, 0, 0, 0, 0))
            hid.flush()
            time.sleep(0.025)
            hid.write(struct.pack('8B', 0, 0, 0, 0, 0, 0, 0, 0))
            hid.flush()
            time.sleep(0.025)

        # Enter
        hid.write(struct.pack('8B', MOD_NONE, 0, KEY_ENTER, 0, 0, 0, 0, 0))
        hid.flush()
        time.sleep(1.6)

        # Tape la commande
        for ch in command:
            if ch not in AZERTY: continue
            mod, kc = AZERTY[ch]
            hid.write(struct.pack('8B', mod, 0, kc, 0, 0, 0, 0, 0))
            hid.flush()
            time.sleep(0.025)
            hid.write(struct.pack('8B', 0, 0, 0, 0, 0, 0, 0, 0))
            hid.flush()
            time.sleep(0.025)

        # Enter final
        hid.write(struct.pack('8B', MOD_NONE, 0, KEY_ENTER, 0, 0, 0, 0, 0))
        hid.flush()
