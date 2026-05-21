#!/usr/bin/env python3
"""Chargement et analyse des données Deezer."""

import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

from config import MIN_LISTEN_SECONDS, WEEKDAYS_FR, MONTHS_FR
from parsers import parse_int, parse_datetime
from formatters import format_datetime


def load_dataset(csv_path: Path) -> dict:
    """Charge et analyse le fichier CSV d'export Deezer."""
    rows: list[dict] = []
    artist_counter: Counter[str] = Counter()
    track_counter: Counter[str] = Counter()
    album_counter: Counter[str] = Counter()
    platform_counter: Counter[str] = Counter()
    device_counter: Counter[str] = Counter()
    year_counter: Counter[int] = Counter()
    month_counter: Counter[int] = Counter()
    weekday_counter: Counter[int] = Counter()
    hour_counter: Counter[int] = Counter()
    weekday_hour: dict[int, Counter[int]] = {i: Counter() for i in range(7)}

    first_seen: datetime | None = None
    last_seen: datetime | None = None
    active_dates: set[str] = set()

    if not csv_path.exists():
        return {
            "exists": False,
            "rows": [],
            "stats": {},
            "top_artists": [],
            "top_tracks": [],
            "top_albums": [],
            "top_platforms": [],
            "top_devices": [],
            "year_series": [],
            "month_series": [],
            "weekday_series": [],
            "hour_series": [],
            "heatmap": [],
            "recent": [],
            "first_seen": None,
            "last_seen": None,
        }

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel

        reader = csv.DictReader(f, dialect=dialect)
        for raw in reader:
            title = (raw.get("Song Title") or raw.get("Track") or raw.get("Title") or "").strip()
            artist = (raw.get("Artist") or "").strip()
            album = (raw.get("Album Title") or raw.get("Album") or "").strip()
            platform = (raw.get("Platform Name") or "").strip()
            device = (raw.get("Platform Model") or "").strip()
            listened_raw = raw.get("Listening Time") or raw.get("Listen Time") or raw.get("Duration listened") or ""
            dt = parse_datetime(raw.get("Date") or raw.get("Timestamp") or raw.get("Played At"))
            listened_seconds = parse_int(listened_raw)

            if not title or not artist:
                continue

            if listened_seconds is not None and listened_seconds < MIN_LISTEN_SECONDS:
                continue

            if listened_seconds is None:
                listened_seconds = 0

            rows.append(
                {
                    "title": title,
                    "artist": artist,
                    "album": album or "—",
                    "platform": platform or "—",
                    "device": device or "—",
                    "listened_seconds": listened_seconds,
                    "date": dt,
                }
            )

            artist_counter[artist] += 1
            track_counter[f"{artist} — {title}"] += 1
            if album:
                album_counter[f"{artist} — {album}"] += 1
            platform_counter[platform or "Inconnu"] += 1
            device_counter[device or "Inconnu"] += 1

            if dt is not None:
                first_seen = dt if first_seen is None or dt < first_seen else first_seen
                last_seen = dt if last_seen is None or dt > last_seen else last_seen
                active_dates.add(dt.strftime("%Y-%m-%d"))
                year_counter[dt.year] += 1
                month_counter[dt.month] += 1
                weekday_counter[dt.weekday()] += 1
                hour_counter[dt.hour] += 1
                weekday_hour[dt.weekday()][dt.hour] += 1

    total_listened_seconds = sum(row["listened_seconds"] for row in rows)
    total_scrobbles = len(rows)
    unique_artists = len(artist_counter)
    unique_tracks = len(track_counter)
    active_days = len(active_dates)

    top_artists = artist_counter.most_common(100)  # Changé de 10 à 100 pour pouvoir charger plus
    top_tracks = track_counter.most_common(100)
    top_albums = album_counter.most_common(100)
    top_platforms = platform_counter.most_common(6)
    top_devices = device_counter.most_common(6)

    year_series = sorted(year_counter.items())
    month_series = [(MONTHS_FR[i - 1], month_counter[i]) for i in range(1, 13)]
    weekday_series = [(WEEKDAYS_FR[i], weekday_counter[i]) for i in range(7)]
    hour_series = [(f"{i:02d}h", hour_counter[i]) for i in range(24)]

    heatmap = [[weekday_hour[d][h] for h in range(24)] for d in range(7)]

    recent = sorted([row for row in rows if row["date"] is not None], key=lambda r: r["date"], reverse=True)[:20]

    favorite_year = max(year_counter.items(), key=lambda item: item[1]) if year_counter else None
    favorite_hour = max(hour_counter.items(), key=lambda item: item[1]) if hour_counter else None
    favorite_weekday = max(weekday_counter.items(), key=lambda item: item[1]) if weekday_counter else None

    stats = {
        "total_scrobbles": total_scrobbles,
        "listening_hours": total_listened_seconds / 3600,
        "unique_artists": unique_artists,
        "unique_tracks": unique_tracks,
        "active_days": active_days,
        "avg_per_day": (total_scrobbles / active_days) if active_days else 0,
        "first_seen": format_datetime(first_seen),
        "last_seen": format_datetime(last_seen),
        "favorite_year": favorite_year[0] if favorite_year else None,
        "favorite_year_count": favorite_year[1] if favorite_year else 0,
        "favorite_hour": favorite_hour[0] if favorite_hour else None,
        "favorite_hour_count": favorite_hour[1] if favorite_hour else 0,
        "favorite_weekday": WEEKDAYS_FR[favorite_weekday[0]] if favorite_weekday else None,
        "favorite_weekday_count": favorite_weekday[1] if favorite_weekday else 0,
    }

    return {
        "exists": True,
        "rows": rows,
        "stats": stats,
        "top_artists": top_artists,
        "top_tracks": top_tracks,
        "top_albums": top_albums,
        "top_platforms": top_platforms,
        "top_devices": top_devices,
        "year_series": year_series,
        "month_series": month_series,
        "weekday_series": weekday_series,
        "hour_series": hour_series,
        "heatmap": heatmap,
        "recent": recent,
        "first_seen": first_seen,
        "last_seen": last_seen,
    }
