import requests
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os




URL = 'https://www.wbm.de/wohnungen-berlin/angebote/'
CHECK_INTERVAL = 60  # Sekunden

# Email configuration
SMTP_SERVER = "smtp.gmail.com"  # Change this if using a different email provider
SMTP_PORT = 587
SENDER_EMAIL = "moj.khaled0@gmail.com"  # Replace with your email
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")  # Replace with your app password
RECEIVER_EMAIL = "al.hazmi.mojeeb@gmail.com"  # Replace with your email


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode (no GUI)
    return webdriver.Chrome(options=chrome_options)

def fill_application_form(driver, offer_url):
    try:
        # Navigate to the offer
        driver.get(offer_url)
        
        # Click "Ansehen" button
        ansehen_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Ansehen')]"))
        )
        ansehen_button.click()

        # Fill the form
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "vorname"))
        )

        # Fill personal information
        driver.find_element(By.NAME, "anrede").send_keys(BEWERBER_DATA["anrede"])
        driver.find_element(By.NAME, "vorname").send_keys(BEWERBER_DATA["vorname"])
        driver.find_element(By.NAME, "name").send_keys(BEWERBER_DATA["name"])
        driver.find_element(By.NAME, "strasse").send_keys(BEWERBER_DATA["strasse"])
        driver.find_element(By.NAME, "plz").send_keys(BEWERBER_DATA["plz"])
        driver.find_element(By.NAME, "ort").send_keys(BEWERBER_DATA["ort"])
        driver.find_element(By.NAME, "email").send_keys(BEWERBER_DATA["email"])
        driver.find_element(By.NAME, "telefon").send_keys(BEWERBER_DATA["telefon"])

        # Accept privacy policy
        privacy_checkbox = driver.find_element(By.XPATH, "//input[@type='checkbox']")
        privacy_checkbox.click()

        # Submit form
        submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'ANFRAGE ABSENDEN')]")
        submit_button.click()

        print(f"[{datetime.now()}] Bewerbung erfolgreich gesendet")
        return True

    except Exception as e:
        print(f"[{datetime.now()}] Fehler beim Ausfüllen des Formulars: {str(e)}")
        return False

def get_offers():
    response = requests.get(URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    offers = []

    # Überprüfen, ob die "keine Angebote" Nachricht vorhanden ist
    no_offers_text = soup.find(string="LEIDER HABEN WIR DERZEIT KEINE VERFÜGBAREN ANGEBOTE")
    if no_offers_text:
        print(f"[{datetime.now()}] Keine Angebote verfügbar.")
        send_no_offers_email()
        return []  # Return empty list to continue normal operation

    # Angebote extrahieren
    offer_elements = soup.find_all('div', class_='c-teaser__content')  # Beispielhafte Klasse
    for elem in offer_elements:
        title_elem = elem.find('h3')
        link_elem = elem.find('a', href=True)
        if title_elem and link_elem:
            title = title_elem.get_text(strip=True)
            link = link_elem['href']
            offers.append({'title': title, 'link': link})
    return offers

def load_applied_offers():
    try:
        with open('applied_offers.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_applied_offer(offer):
    applied_offers = load_applied_offers()
    applied_offers.append(offer)
    with open('applied_offers.json', 'w') as f:
        json.dump(applied_offers, f)

def send_email_notification(new_offers):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = f"Neue WBM Wohnungsangebote gefunden ({len(new_offers)})"
    
    body = "Neue Wohnungsangebote gefunden:\n\n"
    for offer in new_offers:
        body += f"Titel: {offer['title']}\n"
        body += f"Link: {offer['link']}\n\n"
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"[{datetime.now()}] Email-Benachrichtigung gesendet")
    except Exception as e:
        print(f"[{datetime.now()}] Fehler beim Senden der Email: {str(e)}")

def notify_new_offers(new_offers):
    for offer in new_offers:
        print(f"[{datetime.now()}] Neues Angebot gefunden: {offer['title']} - {offer['link']}")
    send_email_notification(new_offers)

def send_no_offers_email():
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = "Keine WBM Wohnungsangebote verfügbar"
    
    body = "Es sind derzeit keine Wohnungsangebote auf der WBM Website verfügbar."
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"[{datetime.now()}] Email-Benachrichtigung (keine Angebote) gesendet")
    except Exception as e:
        print(f"[{datetime.now()}] Fehler beim Senden der Email: {str(e)}")

def main():
    driver = setup_driver()
    while True:
        try:
            current_offers = get_offers()
            applied_offers = load_applied_offers()
            
            for offer in current_offers:
                if offer not in applied_offers:
                    print(f"[{datetime.now()}] Neues Angebot gefunden: {offer['title']}")
                    if fill_application_form(driver, offer['link']):
                        save_applied_offer(offer)
                        notify_new_offers([offer])
            
            time.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            print(f"[{datetime.now()}] Fehler im Hauptprogramm: {str(e)}")
            time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()