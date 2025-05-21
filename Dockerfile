FROM python:3.11-slim

WORKDIR /app

# System-Pakete installieren + Chromedriver
RUN apt-get update && \
    apt-get install -y wget unzip curl gnupg ca-certificates chromium && \
    wget https://chromedriver.storage.googleapis.com/123.0.6312.105/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/ && \
    rm chromedriver_linux64.zip && \
    chmod +x /usr/local/bin/chromedriver

# Python-Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code kopieren
COPY bot.py .
COPY auto.py .

# Standard-Startkommando
CMD ["python", "bot.py"]