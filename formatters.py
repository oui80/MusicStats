#!/usr/bin/env python3
"""Formatage des données pour l'affichage."""

import html
from datetime import datetime


def format_number(value: int | float) -> str:
    """Formate un nombre avec les espaces comme séparateurs."""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return f"{value:,}".replace(",", " ")


def format_hours(seconds: int | float) -> str:
    """Formate des secondes en heures et minutes lisibles."""
    total_minutes = int(round(seconds / 60))
    if total_minutes < 60:
        return f"{total_minutes} min"

    hours, minutes = divmod(total_minutes, 60)
    if minutes == 0:
        return f"{hours} h"
    return f"{hours} h {minutes:02d} min"


def format_datetime(value: datetime | None) -> str:
    """Formate une date/heure au format français."""
    if value is None:
        return "—"
    return value.strftime("%d/%m/%Y %H:%M")


def safe_text(value: object) -> str:
    """Échappe les caractères HTML pour éviter les injections."""
    return html.escape(str(value))
