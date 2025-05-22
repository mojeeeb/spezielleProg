import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import smtplib
from email.mime.text import MIMEText

# Konfiguration
URL = 'https://www.wbm.de/wohnungen-berlin/angebote/'
CHECK_INTERVAL = 60

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "moj.khaled0@gmail.com"
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = "al.hazmi.mojeeb@gmail.com"

def get_offers():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    if soup.find(string="LEIDER HABEN WIR DERZEIT KEINE VERFÜGBAREN ANGEBOTE"):
        return None  # keine Angebote

    offers = []
    for elem in soup.find_all('div', class_='c-teaser__content'):
        title_elem = elem.find('h3')
        link_elem = elem.find('a', href=True)
        if title_elem and link_elem:
            title = title_elem.get_text(strip=True)
            link = link_elem['href']
            offers.append((title, link))
    return offers

def send_email(subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"[{datetime.now()}] E-Mail gesendet: {subject}")
    except Exception as e:
        print(f"[{datetime.now()}] Fehler beim Senden der E-Mail: {e}")

def main():
    while True:
        try:
            offers = get_offers()
            if not offers:
                send_email("WBM: Keine Angebote", "Derzeit sind keine Wohnungsangebote auf der WBM-Seite verfügbar.")
            else:
                text = "Folgende Wohnungsangebote wurden gefunden:\n\n"
                for title, link in offers:
                    text += f"{title}\n{link}\n\n"
                send_email(f"WBM: {len(offers)} Angebote gefunden", text)

        except Exception as e:
            print(f"[{datetime.now()}] Fehler beim Abrufen: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()