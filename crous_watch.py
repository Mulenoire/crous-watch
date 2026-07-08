#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Surveillance de la plateforme CROUS (trouverunlogement.lescrous.fr)
--------------------------------------------------------------------
Ce script verifie regulierement une page de recherche de logement CROUS
et envoie une notification Telegram des qu'un changement est detecte
(typiquement : apparition d'un ou plusieurs logements).

CONFIGURATION : le token et le chat_id sont lus depuis les variables
d'environnement TELEGRAM_TOKEN et TELEGRAM_CHAT_ID (definies comme secrets
GitHub Actions), pour ne jamais les ecrire en clair ici.
"""

import requests
from bs4 import BeautifulSoup
import hashlib
import json
import os
import re
import sys
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

SEARCH_URL = (
    "https://trouverunlogement.lescrous.fr/tools/47/search"
    "?occupationModes=alone"
    "&bounds=5.2286902_43.3910329_5.5324758_43.1696205"
    "&locationName=Marseille+%2813000%29"
)

# Fichier ou le script garde en memoire le dernier etat vu
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_state.json")

# ============================================================
# FONCTIONS
# ============================================================

def send_telegram_message(text: str) -> None:
    """Envoie un message via le bot Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "disable_web_page_preview": False}
    try:
        r = requests.post(url, data=payload, timeout=15)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"[{datetime.now()}] Erreur lors de l'envoi Telegram : {e}", file=sys.stderr)


def fetch_page(url: str) -> str:
    """Recupere le HTML de la page de recherche."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }
    r = re
