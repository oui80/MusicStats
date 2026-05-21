#!/usr/bin/env python3
"""Point d'entrée du serveur MusicStats."""

from http.server import ThreadingHTTPServer
from config import PORT, CSV_FILE
from data_loader import load_dataset
from server import DashboardHandler


def main() -> None:
    """Démarre le serveur HTTP."""
    if not CSV_FILE.exists():
        print(f"CSV introuvable: {CSV_FILE}")
    else:
        print(f"CSV chargé: {CSV_FILE}")

    # Charger les données une fois au démarrage du serveur
    DashboardHandler.dataset = load_dataset(CSV_FILE)

    server = ThreadingHTTPServer(("0.0.0.0", PORT), DashboardHandler)
    print(f"Serveur lancé sur http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
