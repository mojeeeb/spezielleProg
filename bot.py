import os
import json
import time
import requests
import logging

logging.basicConfig(level=logging.INFO)

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook-test/22e3bd48-0301-4ecd-9493-d8eff6678856")
SCAN_FILE = "trivy-results.json"
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "300"))

def load_scan_result(path):
    try:
        with open(path, 'r') as file:
            data = json.load(file)
        return data
    except Exception as e:
        logging.error(f"Fehler beim Laden der Datei: {e}")
        return None

def send_to_n8n(payload):
    try:
        res = requests.post(N8N_WEBHOOK_URL, json=payload)
        logging.info(f"n8n Antwort: {res.status_code} - {res.text}")
    except Exception as e:
        logging.error(f"Fehler beim Senden an n8n: {e}")

def main():
    while True:
        logging.info("🔍 Scandaten werden geladen...")
        result = load_scan_result(SCAN_FILE)
        if result:
            send_to_n8n(result)
        else:
            logging.warning("Kein gültiges Ergebnis gefunden.")
        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()