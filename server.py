#!/usr/bin/env python3
"""Serveur HTTP et rendu des pages."""

import json
from http.server import BaseHTTPRequestHandler
from string import Template

from config import MIN_LISTEN_SECONDS
from formatters import format_number, format_hours, safe_text
from visualizations import bars_html, mini_stats_html, vertical_chart_svg, heatmap_svg, render_recent_table


# Template HTML principal
DASHBOARD_TEMPLATE = Template("""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>MusicStats — Deezer dashboard</title>
  <style>
    :root {
      --bg: #0a0810;
      --bg-2: #120f1f;
      --panel: rgba(255, 255, 255, 0.06);
      --panel-2: rgba(255, 255, 255, 0.08);
      --stroke: rgba(255, 255, 255, 0.08);
      --text: #f5f1ff;
      --muted: rgba(245, 241, 255, 0.72);
      --accent: #ff4d6d;
      --accent-2: #b5179e;
      --accent-3: #7b2cff;
      --shadow: 0 25px 80px rgba(0, 0, 0, 0.35);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(181, 23, 158, 0.24), transparent 28%),
        radial-gradient(circle at 80% 10%, rgba(255, 77, 109, 0.18), transparent 20%),
        linear-gradient(180deg, #0a0810 0%, #120f1f 100%);
      min-height: 100vh;
    }

    .shell {
      width: min(1400px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0 40px;
    }

    .hero {
      display: grid;
      grid-template-columns: 1.4fr 0.9fr;
      gap: 20px;
      align-items: stretch;
      margin-bottom: 20px;
    }

    .panel {
      background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.05));
      border: 1px solid var(--stroke);
      border-radius: 28px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(18px);
    }

    .hero__main {
      padding: 28px;
      position: relative;
      overflow: hidden;
    }

    .hero__main::after {
      content: "";
      position: absolute;
      inset: auto -80px -120px auto;
      width: 320px;
      height: 320px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(255,77,109,0.28), transparent 68%);
      filter: blur(8px);
      pointer-events: none;
    }

    .eyebrow {
      display: inline-flex;
      gap: 10px;
      align-items: center;
      padding: 8px 14px;
      border-radius: 999px;
      background: rgba(255, 77, 109, 0.14);
      border: 1px solid rgba(255, 77, 109, 0.25);
      color: #ffc7d1;
      font-size: 13px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    h1 {
      font-size: clamp(38px, 5vw, 72px);
      line-height: 0.95;
      margin: 18px 0 14px;
      letter-spacing: -0.05em;
    }

    .hero p {
      margin: 0;
      max-width: 64ch;
      color: var(--muted);
      font-size: 16px;
      line-height: 1.6;
    }

    .hero__metrics {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
      margin-top: 26px;
    }

    .metric-card {
      padding: 16px 18px;
      border-radius: 22px;
      background: rgba(0, 0, 0, 0.2);
      border: 1px solid rgba(255,255,255,0.06);
    }

    .metric-card span {
      display: block;
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 10px;
    }

    .metric-card strong {
      font-size: 28px;
      display: block;
      letter-spacing: -0.04em;
    }

    .hero__side {
      padding: 22px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .profile {
      display: flex;
      gap: 16px;
      align-items: center;
      padding-bottom: 14px;
      border-bottom: 1px solid rgba(255,255,255,0.08);
    }

    .avatar {
      width: 72px;
      height: 72px;
      border-radius: 24px;
      background: linear-gradient(135deg, var(--accent), var(--accent-2) 55%, var(--accent-3));
      display: grid;
      place-items: center;
      font-size: 30px;
      box-shadow: 0 16px 35px rgba(255, 77, 109, 0.28);
    }

    .profile h2 {
      margin: 0 0 6px;
      font-size: 20px;
    }

    .profile p {
      margin: 0;
      color: var(--muted);
      font-size: 14px;
    }

    .side-stat {
      padding: 15px 16px;
      border-radius: 20px;
      background: rgba(0,0,0,0.18);
      border: 1px solid rgba(255,255,255,0.06);
    }

    .side-stat label {
      display: block;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 7px;
    }

    .side-stat strong {
      font-size: 18px;
    }

    .grid-2 {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 20px;
      margin-top: 20px;
    }

    .card {
      padding: 22px;
      border-radius: 26px;
      background: var(--panel);
      border: 1px solid var(--stroke);
      box-shadow: var(--shadow);
    }

    .card h3 {
      margin: 0 0 16px;
      font-size: 20px;
      letter-spacing: -0.03em;
    }

    .card__sub {
      margin-top: -8px;
      margin-bottom: 16px;
      color: var(--muted);
      font-size: 14px;
    }

    .card__actions {
      margin-top: 16px;
      padding-top: 14px;
      border-top: 1px solid rgba(255,255,255,0.08);
    }

    .load-more-btn {
      width: 100%;
      padding: 10px 14px;
      border-radius: 18px;
      border: 1px solid rgba(255,77,109,0.3);
      background: rgba(255,77,109,0.08);
      color: #ffc7d1;
      font-size: 13px;
      cursor: pointer;
      transition: all 0.2s;
      font-weight: 600;
    }

    .load-more-btn:hover {
      background: rgba(255,77,109,0.15);
      border-color: rgba(255,77,109,0.5);
    }

    .card--full { margin-top: 20px; }

    .bar-list, .mini-list { display: grid; gap: 14px; }

    .bar-row {
      display: grid;
      gap: 8px;
    }

    .bar-row__head, .mini-item__top, .recent-table__head, .recent-table__row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 16px;
      align-items: center;
    }

    .bar-row__label {
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
      color: var(--text);
      font-weight: 600;
    }

    .bar-row__value { color: var(--muted); }

    .bar-track, .mini-item__meter {
      height: 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.08);
      overflow: hidden;
      border: 1px solid rgba(255,255,255,0.06);
    }

    .bar-fill, .mini-item__meter span {
      display: block;
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(90deg, var(--accent), #ff7aa1);
      box-shadow: 0 0 24px rgba(255,77,109,0.4);
    }

    .mini-item {
      display: grid;
      gap: 10px;
      padding: 14px 16px;
      border-radius: 20px;
      background: rgba(0, 0, 0, 0.18);
      border: 1px solid rgba(255,255,255,0.06);
    }

    .mini-item__top span { color: var(--text); font-weight: 600; }
    .mini-item__top strong { color: #ffcfda; font-weight: 700; }

    .chart-card__title {
      margin-bottom: 10px;
      font-size: 15px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .chart-svg {
      width: 100%;
      height: auto;
      overflow: visible;
      display: block;
    }

    .chart-grid { stroke: rgba(255,255,255,0.08); stroke-width: 1; }
    .chart-axis { stroke: rgba(255,255,255,0.18); stroke-width: 1.2; }
    .chart-axis-label, .chart-x-label, .chart-value-label, .heat-label {
      fill: rgba(245,241,255,0.72);
      font-size: 11px;
    }
    .chart-x-label { font-size: 10px; }
    .chart-value-label { fill: #ffd1d9; font-weight: 700; }
    .heat-label { font-size: 11px; }

    .recent-table { display: grid; gap: 10px; }
    .recent-table__head, .recent-table__row {
      grid-template-columns: 190px minmax(0, 1.2fr) minmax(0, 1fr) 100px;
      padding: 12px 14px;
      border-radius: 16px;
      background: rgba(0,0,0,0.18);
    }
    .recent-table__head {
      background: transparent;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-size: 11px;
      padding-top: 0;
    }
    .recent-table__row span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .recent-table__row strong { display: block; }
    .recent-table__row small { display: block; color: var(--muted); margin-top: 4px; }

    .empty-state {
      padding: 20px;
      border-radius: 20px;
      color: var(--muted);
      background: rgba(0,0,0,0.18);
      border: 1px dashed rgba(255,255,255,0.14);
    }

    .footer-note {
      margin-top: 18px;
      color: var(--muted);
      font-size: 13px;
      text-align: center;
    }

    @media (max-width: 1100px) {
      .hero, .grid-2 { grid-template-columns: 1fr; }
      .recent-table__head, .recent-table__row { grid-template-columns: 1fr 1.2fr 1fr 80px; }
    }

    @media (max-width: 720px) {
      .shell { width: min(100% - 20px, 100%); padding-top: 10px; }
      .hero__main, .hero__side, .card { padding: 18px; border-radius: 22px; }
      .hero__metrics { grid-template-columns: 1fr; }
      .grid-2 { gap: 14px; }
      .recent-table__head { display: none; }
      .recent-table__row {
        grid-template-columns: 1fr;
        gap: 6px;
      }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="panel hero__main">
        <div class="eyebrow">MusicStats • Scrobbles Deezer</div>
        <h1>Votre historique d'écoute, mais en version premium.</h1>
        <div class="hero__metrics">
          <div class="metric-card"><span>Écoutes totales</span><strong>${total_scrobbles}</strong></div>
          <div class="metric-card"><span>Temps d'écoute total</span><strong>${listening_hours}</strong></div>
          <div class="metric-card"><span>Artistes différents</span><strong>${unique_artists}</strong></div>
          <div class="metric-card"><span>Titres différents</span><strong>${unique_tracks}</strong></div>
        </div>
      </div>

      <aside class="panel hero__side">
        <div class="profile">
          <div class="avatar">♫</div>
          <div>
            <h2>Deezer Listening Profile</h2>
            <p>${first_seen} → ${last_seen}</p>
          </div>
        </div>
        <div class="side-stat"><label>Jours avec écoute</label><strong>${active_days} jours</strong></div>
        <div class="side-stat"><label>Moyenne par jour actif</label><strong>${avg_per_day} écoutes</strong></div>
        <div class="side-stat"><label>Moment le plus fréquent</label><strong>${favorite_weekday} · ${favorite_hour}h</strong></div>
        <div class="side-stat"><label>Année la plus active</label><strong>${favorite_year}</strong></div>
      </aside>
    </section>

    <section class="grid-2">
      <article class="card">
        <h3>Top artistes</h3>
        <p class="card__sub">Vos artistes les plus écoutés sur l'ensemble du CSV.</p>
        <div id="artists-list">${top_artists}</div>
        <div class="card__actions" id="artists-actions">${artists_load_btn}</div>
      </article>

      <article class="card">
        <h3>Top morceaux</h3>
        <p class="card__sub">Classement des titres écoutés le plus souvent.</p>
        <div id="tracks-list">${top_tracks}</div>
        <div class="card__actions" id="tracks-actions">${tracks_load_btn}</div>
      </article>
    </section>

    <section class="grid-2">
      <article class="card">
        <h3>Écoutes par année</h3>
        <p class="card__sub">Visualisez vos pics d'activité dans le temps.</p>
        ${year_chart}
      </article>

      <article class="card">
        <h3>Écoutes par mois</h3>
        <p class="card__sub">Répartition sur l'année pour repérer les périodes fortes.</p>
        ${month_chart}
      </article>
    </section>

    <section class="grid-2">
      <article class="card">
        <h3>Heatmap d'écoute</h3>
        <p class="card__sub">Quand vous écoutez le plus, sur la semaine et dans la journée.</p>
        ${heatmap}
      </article>

      <article class="card">
        <h3>Plateformes & appareils</h3>
        <p class="card__sub">Vos devices et plateformes les plus présents dans l'export.</p>
        <div style="display:grid; gap:18px;">
          <div>
            <h4 style="margin:0 0 12px; color: var(--muted); font-size:13px; text-transform:uppercase; letter-spacing:0.08em;">Plateformes</h4>
            ${top_platforms}
          </div>
          <div>
            <h4 style="margin:0 0 12px; color: var(--muted); font-size:13px; text-transform:uppercase; letter-spacing:0.08em;">Appareils</h4>
            ${top_devices}
          </div>
        </div>
      </article>
    </section>

    <section class="card card--full">
      <h3>Top albums</h3>
      <p class="card__sub">Les albums qui reviennent le plus souvent dans vos écoutes.</p>
      <div id="albums-list">${top_albums}</div>
      <div class="card__actions" id="albums-actions">${albums_load_btn}</div>
    </section>

    <section class="card card--full">
      <h3>Écoutes récentes</h3>
      <p class="card__sub">Les 20 dernières lignes de votre export avec horodatage complet.</p>
      ${recent_table}
    </section>

    <p class="footer-note">
      Données filtrées avec un seuil minimum de ${min_listen_seconds} secondes pour enlever les écoutes trop courtes.
    </p>
  </main>
  <script>
    function loadMore(type) {
      const containerMap = {
        'artists': { container: 'artists-list', actions: 'artists-actions' },
        'tracks': { container: 'tracks-list', actions: 'tracks-actions' },
        'albums': { container: 'albums-list', actions: 'albums-actions' }
      };
      
      if (!containerMap[type]) return;
      
      const config = containerMap[type];
      const container = document.getElementById(config.container);
      const actionsDiv = document.getElementById(config.actions);
      
      if (!container || !actionsDiv) return;
      
      const currentCount = container.querySelectorAll('.bar-row').length;
      
      fetch(`/api/${type}/more?offset=${currentCount}`)
        .then(res => res.json())
        .then(data => {
          if (!data.items || data.items.length === 0) {
            actionsDiv.innerHTML = '<p style="color: var(--muted); font-size: 13px;">Aucun autre élément à afficher</p>';
            return;
          }
          
          const barListDiv = container.querySelector('.bar-list');
          if (!barListDiv) return;
          
          const maxValue = data.max_value || 1;
          data.items.forEach(item => {
            const [label, value] = item;
            const width = Math.max(4, Math.round((value / maxValue) * 100));
            const html = `<div class="bar-row"><div class="bar-row__head"><span class="bar-row__label">${label}</span><span class="bar-row__value">${value.toLocaleString('fr-FR')}</span></div><div class="bar-track"><span class="bar-fill" style="width:${width}%; background:${data.gradient};"></span></div></div>`;
            barListDiv.insertAdjacentHTML('beforeend', html);
          });
          
          if (data.has_more) {
            actionsDiv.innerHTML = `<button class="load-more-btn" onclick="loadMore('${type}')">Charger plus</button>`;
          } else {
            actionsDiv.innerHTML = '<p style="color: var(--muted); font-size: 13px;">Fin du classement</p>';
          }
        })
        .catch(err => {
          console.error('Erreur:', err);
          actionsDiv.innerHTML = '<p style="color: #ff6b6b;">Erreur lors du chargement</p>';
        });
    }
  </script>
</body>
</html>""")


def render_page(data: dict) -> str:
    """Génère la page HTML du dashboard."""
    stats = data["stats"]
    # Convert hours back to seconds for proper formatting
    total_seconds = int(stats.get("listening_hours", 0) * 3600)
    
    # Générer les listes avec boutons "Charger plus"
    artists_html, artists_has_more = bars_html(data["top_artists"], "linear-gradient(90deg, #ff4d6d, #ff7aa1)", limit=10)
    tracks_html, tracks_has_more = bars_html(data["top_tracks"], "linear-gradient(90deg, #b5179e, #ff4d6d)", limit=10)
    albums_html, albums_has_more = bars_html(data["top_albums"], "linear-gradient(90deg, #7b2cff, #b5179e)", limit=10)
    
    artists_btn = '<button class="load-more-btn" onclick="loadMore(\'artists\')">Charger plus d\'artistes</button>' if artists_has_more else ''
    tracks_btn = '<button class="load-more-btn" onclick="loadMore(\'tracks\')">Charger plus de morceaux</button>' if tracks_has_more else ''
    albums_btn = '<button class="load-more-btn" onclick="loadMore(\'albums\')">Charger plus d\'albums</button>' if albums_has_more else ''
    
    template_values = {
        "total_scrobbles": format_number(stats.get("total_scrobbles", 0)),
        "listening_hours": format_hours(total_seconds),
        "unique_artists": format_number(stats.get("unique_artists", 0)),
        "unique_tracks": format_number(stats.get("unique_tracks", 0)),
        "active_days": format_number(stats.get("active_days", 0)),
        "avg_per_day": f'{stats.get("avg_per_day", 0):.1f}',
        "first_seen": safe_text(stats.get("first_seen") or "—"),
        "last_seen": safe_text(stats.get("last_seen") or "—"),
        "favorite_year": safe_text(stats.get("favorite_year") or "—"),
        "favorite_weekday": safe_text(stats.get("favorite_weekday") or "—"),
        "favorite_hour": safe_text(stats.get("favorite_hour") if stats.get("favorite_hour") is not None else "—"),
        "top_artists": artists_html,
        "artists_load_btn": artists_btn,
        "top_tracks": tracks_html,
        "tracks_load_btn": tracks_btn,
        "top_albums": albums_html,
        "albums_load_btn": albums_btn,
        "top_platforms": mini_stats_html(data["top_platforms"]),
        "top_devices": mini_stats_html(data["top_devices"]),
        "year_chart": vertical_chart_svg("Écoutes par année", data["year_series"], "#ff4d6d"),
        "month_chart": vertical_chart_svg("Écoutes par mois", data["month_series"], "#b5179e"),
        "heatmap": heatmap_svg(data["heatmap"]),
        "recent_table": render_recent_table(data["recent"]),
        "min_listen_seconds": MIN_LISTEN_SECONDS,
    }
    return DASHBOARD_TEMPLATE.safe_substitute(template_values)


class DashboardHandler(BaseHTTPRequestHandler):
    """Handler HTTP pour le serveur dashboard."""
    
    dataset = None  # Will be set by the server
    
    def _send_html(self, content: str, status: int = 200) -> None:
        encoded = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _get_query_param(self, name: str, default: str = "") -> str:
        """Extract a query parameter from self.path."""
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        return params.get(name, [default])[0]

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            html_page = render_page(self.dataset)
            self._send_html(html_page)
            return

        if self.path == "/api/stats":
            payload = {
                "stats": self.dataset["stats"],
                "top_artists": self.dataset["top_artists"],
                "top_tracks": self.dataset["top_tracks"],
                "top_albums": self.dataset["top_albums"],
                "top_platforms": self.dataset["top_platforms"],
                "top_devices": self.dataset["top_devices"],
                "year_series": self.dataset["year_series"],
                "month_series": self.dataset["month_series"],
                "weekday_series": self.dataset["weekday_series"],
                "hour_series": self.dataset["hour_series"],
                "first_seen": self.dataset.get("first_seen"),
                "last_seen": self.dataset.get("last_seen"),
            }
            self._send_json(payload)
            return

        if self.path == "/health":
            self._send_json({"ok": True, "rows": len(self.dataset["rows"])})
            return

        # Handle /api/{type}/more?offset=X requests
        if self.path.startswith("/api/") and "/more" in self.path:
            parts = self.path.split("/")
            if len(parts) >= 3 and parts[-1].startswith("more"):
                data_type = parts[2]
                offset = int(self._get_query_param("offset", "0"))
                
                if data_type == "artists":
                    items = self.dataset["top_artists"][offset:offset+10]
                    max_value = self.dataset["top_artists"][0][1] if self.dataset["top_artists"] else 1
                    gradient = "linear-gradient(90deg, #ff4d6d, #b5179e)"
                elif data_type == "tracks":
                    items = self.dataset["top_tracks"][offset:offset+10]
                    max_value = self.dataset["top_tracks"][0][1] if self.dataset["top_tracks"] else 1
                    gradient = "linear-gradient(90deg, #b5179e, #7b2cff)"
                elif data_type == "albums":
                    items = self.dataset["top_albums"][offset:offset+10]
                    max_value = self.dataset["top_albums"][0][1] if self.dataset["top_albums"] else 1
                    gradient = "linear-gradient(90deg, #7b2cff, #ff006e)"
                else:
                    self.send_error(400, "Invalid data type")
                    return
                
                has_more = offset + 10 < len(self.dataset[f"top_{data_type}"])
                payload = {
                    "items": items,
                    "max_value": max_value,
                    "gradient": gradient,
                    "has_more": has_more
                }
                self._send_json(payload)
                return

        self.send_error(404, "Not found")

    def do_HEAD(self) -> None:
        if self.path in ("/", "/index.html"):
            html_page = render_page(self.dataset)
            encoded = html_page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            return

        if self.path in ("/api/stats", "/health"):
            payload = json.dumps({"ok": True}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            return

        self.send_error(404, "Not found")

    def log_message(self, format: str, *args) -> None:  # noqa: A003 - standard signature
        return
