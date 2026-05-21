#!/usr/bin/env python3
"""Parsing des données brutes."""

from datetime import datetime


def parse_int(value: str | None) -> int | None:
    """Parse une valeur en entier, gère les formats variés."""
    if value is None:
        return None
    value = value.strip().lstrip("'")
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def parse_datetime(value: str | None) -> datetime | None:
    """Parse une date/heure depuis plusieurs formats."""
    if not value:
        return None
    value = value.strip().lstrip("'")
    if not value:
        return None

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
