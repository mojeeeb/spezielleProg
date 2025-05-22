FROM python:3.11-slim

WORKDIR /app

# Python-Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code kopieren
COPY bot.py .
COPY auto.py .
