#!/usr/bin/env python3
import csv
import sys
import re

MIN_LISTEN_SECONDS = 30
USE_ORIGINAL_TIMESTAMP = True


def normalize_header(name):
    return re.sub(r"[^a-z0-9]", "", name.lower().strip())


def get_value(row, aliases):
    normalized = {normalize_header(k): v for k, v in row.items() if k is not None}

    for alias in aliases:
        key = normalize_header(alias)
        if key in normalized:
            return normalized[key].strip().lstrip("'")

    return ""


def to_seconds(value):
    value = value.strip().lstrip("'")

    if not value:
        return None

    if value.isdigit():
        return int(value)

    try:
        number = float(value)
        return int(round(number))
    except ValueError:
        pass

    # Format mm:ss ou hh:mm:ss
    parts = value.split(":")
    if all(part.isdigit() for part in parts):
        parts = [int(p) for p in parts]

        if len(parts) == 2:
            return parts[0] * 60 + parts[1]

        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]

    return None


def convert_csv(input_file, output_file):
    with open(input_file, "r", encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)

        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel

        reader = csv.DictReader(f, dialect=dialect)

        with open(output_file, "w", encoding="utf-8", newline="") as out:
            writer = csv.writer(out, quoting=csv.QUOTE_ALL)

            for row in reader:
                listen_duration_raw = get_value(row, [
                    "Listening Time",
                    "Listen Time",
                    "Listening Duration",
                    "Duration listened",
                    "Played Duration",
                    "Ms Played",
                    "ms_played"
                ])

                listen_seconds = to_seconds(listen_duration_raw)

                # On enlève les morceaux écoutés moins de 40 secondes
                if listen_seconds is not None and listen_seconds < MIN_LISTEN_SECONDS:
                    continue

                artist = get_value(row, ["Artist"])
                track = get_value(row, ["Song Title", "Track", "Title"])
                album = get_value(row, ["Album Title", "Album"])
                timestamp = get_value(row, ["Date", "Timestamp", "Played At"])
                album_artist = get_value(row, ["Album Artist"])

                if not artist or not track:
                    continue

                if not album_artist:
                    album_artist = artist

                writer.writerow([
                    artist,
                    track,
                    album,
                    timestamp if USE_ORIGINAL_TIMESTAMP else "",
                    album_artist,
                    ""
                ])


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Utilisation : python convert_csv.py input.csv output.csv")
        sys.exit(1)

    convert_csv(sys.argv[1], sys.argv[2])