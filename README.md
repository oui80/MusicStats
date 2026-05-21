# MusicStats - Deezer Dashboard

Un dashboard moderne en style last.fm pour visualiser vos statistiques d'écoute Deezer.

## Structure du projet

```
MusicStats/
├── app.py                 # Point d'entrée principal du serveur
├── config.py             # Constantes et configuration
├── parsers.py            # Parsing des données brutes (CSV, dates, nombres)
├── formatters.py         # Formatage pour l'affichage (nombres, heures, dates)
├── data_loader.py        # Chargement et analyse du CSV Deezer
├── visualizations.py     # Génération des graphiques SVG et HTML
├── server.py             # Handler HTTP et templates HTML
├── convertCSV.py         # Ancien script de conversion (optionnel)
└── deezer-data_879719721.csv  # Données d'export Deezer
```

## Modules

- **app.py** : Démarre le serveur HTTP sur le port 8000
- **config.py** : Constantes globales (port, fichier CSV, limites, labels français)
- **parsers.py** : Parsing des nombres et dates depuis le CSV
- **formatters.py** : Formatage pour l'affichage lisible
- **data_loader.py** : Chargement du CSV et statistiques (100 top artistes/morceaux/albums)
- **visualizations.py** : HTML/SVG pour les graphiques, classements et heatmap
- **server.py** : Handler HTTP et template HTML principal

## Installation et lancement

```bash
python3 app.py
```

Le serveur démarre sur `http://127.0.0.1:8000`

## Variables d'environnement

- `PORT` : Port du serveur (défaut: 8000)
- `MIN_LISTEN_SECONDS` : Durée minimale pour compter une écoute (défaut: 30)

Exemple :
```bash
PORT=9000 MIN_LISTEN_SECONDS=5 python3 app.py
```

## Fonctionnalités

- 📊 Stats globales (écoutes, heures, artistes, titres)
- 🎤 Top 10 artistes avec bouton "Charger plus"
- 🎵 Top 10 morceaux avec bouton "Charger plus"  
- 💿 Top 10 albums avec bouton "Charger plus"
- 📈 Graphiques par année et par mois
- 🔥 Heatmap d'activité (jour de la semaine × heure)
- 📱 Plateformes et appareils utilisés
- ⏰ Écoutes récentes avec horodatage

## API

- `GET /` : Dashboard HTML
- `GET /api/stats` : JSON avec toutes les statistiques
- `GET /health` : Health check

## Notes

- Le filtrage à 30 secondes minimum est appliqué pour enlever les écoutes trop courtes
- Les données sont chargées une fois au démarrage du serveur
- Le rendu HTML utilise la classe `Template` avec substitution simple

## Développement

Pour modifier les statistiques affichées ou ajouter des données au CSV, éditez les modules concernés :
- `data_loader.py` pour le chargement et les calculs
- `visualizations.py` pour les graphiques et rendu HTML
- `server.py` pour les routes et réponses
