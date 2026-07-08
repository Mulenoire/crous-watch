#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Surveillance de la plateforme CROUS (trouverunlogement.lescrous.fr)
--------------------------------------------------------------------
Ce script verifie regulierement une page de recherche de logement CROUS
et envoie une notification Telegram des qu'un changement est detecte
(typiquement : apparition d'un ou plusieurs logements).

CONFIGURATION : le token et le(s) chat_id sont lus depuis les variables
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

# Plusieurs destinataires possibles : liste de chat_id separes par des virgules
# dans le secret TELEGRAM_CHAT_ID, par exemple "111111111,8884272660"
TELEGRAM_CHAT_IDS = [
    chat_id.strip()
    for chat_id in os.environ.get("TELEGRAM_CHAT_ID", "").split(",")
    if chat_id.strip()
]

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
    """Envoie un message via le bot Telegram a tous les destinataires configures."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for chat_id in TELEGRAM_CHAT_IDS:
        payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": False}
        try:
            r = requests.post(url, data=payload, timeout=15)
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"[{datetime.now()}] Erreur lors de l'envoi Telegram a {chat_id} : {e}", file=sys.stderr)


def fetch_page(url: str) -> str:
    """Recupere le HTML de la page de recherche."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return r.text


def extract_relevant_content(html: str):
    """
    Extrait la partie utile de la page (resultats de recherche),
    en ignorant les elements qui changent sans rapport avec les logements
    (menus, scripts, etc.).

    Retourne (texte_normalise, message_resume) pour comparaison + affichage.
    """
    soup = BeautifulSoup(html, "html.parser")

    main = soup.find("main") or soup.find("body") or soup

    for tag in main.find_all(["script", "style", "noscript"]):
        tag.decompose()

    text = main.get_text(separator=" | ", strip=True)

    match = re.search(r"(Aucun logement trouve|(\d+)\s+logements?\s+trouves?)", text, re.IGNORECASE)
    summary = match.group(0) if match else "Statut indisponible"

    return text, summary


def load_previous_hash():
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("hash")
    except (json.JSONDecodeError, OSError):
        return None


def save_current_hash(current_hash: str, summary: str) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"hash": current_hash, "summary": summary, "checked_at": datetime.now().isoformat()},
            f,
            ensure_ascii=False,
            indent=2,
        )


def main() -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_IDS:
        print(
            f"[{datetime.now()}] Erreur : TELEGRAM_TOKEN ou TELEGRAM_CHAT_ID "
            "non defini (variables d'environnement / secrets manquants).",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"[{datetime.now()}] Verification en cours...")

    try:
        html = fetch_page(SEARCH_URL)
    except requests.RequestException as e:
        print(f"[{datetime.now()}] Erreur de connexion : {e}", file=sys.stderr)
        return

    text, summary = extract_relevant_content(html)
    current_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

    previous_hash = load_previous_hash()

    if previous_hash is None:
        save_current_hash(current_hash, summary)
        print(f"[{datetime.now()}] Premier lancement, etat de reference enregistre : {summary}")
        return

    if current_hash != previous_hash:
        message = (
            "ALERTE : changement detecte sur ta recherche CROUS !\n\n"
            f"Statut actuel : {summary}\n\n"
            f"Verifie ici :\n{SEARCH_URL}"
        )
        send_telegram_message(message)
        print(f"[{datetime.now()}] Changement detecte, notification envoyee : {summary}")
        save_current_hash(current_hash, summary)
    else:
        print(f"[{datetime.now()}] Aucun changement ({summary})")


if __name__ == "__main__":
    main()
