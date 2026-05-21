#!/usr/bin/env python3
"""Configuration et constantes globales."""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "deezer-data_879719721.csv"
PORT = int(os.environ.get("PORT", "8000"))
MIN_LISTEN_SECONDS = int(os.environ.get("MIN_LISTEN_SECONDS", "30"))

MONTHS_FR = [
    "Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
    "Juil", "Août", "Sep", "Oct", "Nov", "Déc",
]
WEEKDAYS_FR = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
