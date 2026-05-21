#!/usr/bin/env python3
"""Génération des visualisations HTML et SVG."""

import math
from formatters import safe_text, format_number
from config import WEEKDAYS_FR


def bars_html(items: list[tuple[str, int]], accent: str, limit: int = 10) -> tuple[str, bool]:
    """
    Génère les barres de classement.
    Retourne (html, has_more) où has_more indique s'il y a plus d'items.
    """
    if not items:
        return '<div class="empty-state">Aucune donnée disponible.</div>', False

    displayed_items = items[:limit]
    has_more = len(items) > limit
    
    max_value = max(value for _, value in displayed_items) or 1
    parts: list[str] = ['<div class="bar-list">']
    for label, value in displayed_items:
        width = max(4, int(round((value / max_value) * 100)))
        parts.append(
            f'''<div class="bar-row">
                <div class="bar-row__head">
                    <span class="bar-row__label">{safe_text(label)}</span>
                    <span class="bar-row__value">{format_number(value)}</span>
                </div>
                <div class="bar-track"><span class="bar-fill" style="width:{width}%; background:{accent};"></span></div>
            </div>'''
        )
    parts.append("</div>")
    return "\n".join(parts), has_more


def mini_stats_html(items: list[tuple[str, int]]) -> str:
    """Génère les mini-stats pour plateformes et appareils."""
    if not items:
        return '<div class="empty-state">Aucune donnée disponible.</div>'
    max_value = max(value for _, value in items) or 1
    rows: list[str] = ['<div class="mini-list">']
    for label, value in items:
        percent = value / max_value
        rows.append(
            f'''<div class="mini-item">
                <div class="mini-item__top">
                    <span>{safe_text(label)}</span>
                    <strong>{format_number(value)}</strong>
                </div>
                <div class="mini-item__meter"><span style="width:{max(4, int(percent * 100))}%;"></span></div>
            </div>'''
        )
    rows.append("</div>")
    return "\n".join(rows)


def vertical_chart_svg(title: str, series: list[tuple[str, int]], color: str) -> str:
    """Génère un graphique en barres verticales SVG."""
    if not series:
        return '<div class="empty-state">Aucune donnée disponible.</div>'

    width = 1000
    height = 320
    left = 48
    right = 16
    top = 20
    bottom = 58
    plot_width = width - left - right
    plot_height = height - top - bottom
    max_value = max(value for _, value in series) or 1
    bar_width = plot_width / len(series)

    svg_parts = [
        f'<div class="chart-card__title">{safe_text(title)}</div>',
        f'<svg viewBox="0 0 {width} {height}" class="chart-svg" role="img" aria-label="{safe_text(title)}">',
        '<defs>',
        f'<linearGradient id="grad-{abs(hash(title))}" x1="0" x2="0" y1="0" y2="1">',
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0.95"/>',
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0.35"/>',
        '</linearGradient>',
        '</defs>',
    ]

    for frac in (0.25, 0.5, 0.75, 1.0):
        y = top + plot_height * frac
        svg_parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" class="chart-grid" />'
        )
        svg_parts.append(
            f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end" class="chart-axis-label">{format_number(int(max_value * (1 - frac)) if frac < 1 else 0)}</text>'
        )

    for index, (label, value) in enumerate(series):
        height_px = 0 if max_value == 0 else plot_height * (value / max_value)
        x = left + index * bar_width + bar_width * 0.18
        bar_w = bar_width * 0.64
        y = top + plot_height - height_px
        svg_parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{height_px:.1f}" rx="12" fill="url(#grad-{abs(hash(title))})" opacity="0.95">'
            f'<title>{safe_text(label)}: {format_number(value)}</title></rect>'
        )
        svg_parts.append(
            f'<text x="{x + bar_w / 2:.1f}" y="{height - 20}" text-anchor="middle" class="chart-x-label">{safe_text(label)}</text>'
        )
        if value:
            svg_parts.append(
                f'<text x="{x + bar_w / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle" class="chart-value-label">{format_number(value)}</text>'
            )

    svg_parts.append(
        f'<line x1="{left}" y1="{top + plot_height}" x2="{width-right}" y2="{top + plot_height}" class="chart-axis" />'
    )
    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def heatmap_svg(matrix: list[list[int]]) -> str:
    """Génère une heatmap d'activité."""
    width = 1000
    cell_w = 34
    cell_h = 28
    left = 74
    top = 36
    height = top + cell_h * 7 + 36
    max_value = max((value for row in matrix for value in row), default=1) or 1

    def heat_color(value: int) -> str:
        if value <= 0:
            return "rgba(255,255,255,0.05)"
        ratio = math.sqrt(value / max_value)
        alpha = 0.12 + ratio * 0.88
        return f"rgba(255, 77, 109, {alpha:.3f})"

    parts = [
        '<div class="chart-card__title">Heatmap d\'activité</div>',
        f'<svg viewBox="0 0 {width} {height}" class="chart-svg chart-svg--heatmap" role="img" aria-label="Heatmap d\'activité">',
    ]

    for hour in range(24):
        x = left + hour * cell_w + cell_w / 2
        parts.append(
            f'<text x="{x:.1f}" y="22" text-anchor="middle" class="heat-label">{hour:02d}</text>'
        )

    for day_idx, day_name in enumerate(WEEKDAYS_FR):
        y = top + day_idx * cell_h + cell_h * 0.72
        parts.append(
            f'<text x="20" y="{y:.1f}" text-anchor="start" class="heat-label">{day_name}</text>'
        )

    for day_idx, row in enumerate(matrix):
        for hour_idx, value in enumerate(row):
            x = left + hour_idx * cell_w
            y = top + day_idx * cell_h
            parts.append(
                f'<rect x="{x}" y="{y}" width="{cell_w - 4}" height="{cell_h - 4}" rx="8" fill="{heat_color(value)}">'
                f'<title>{WEEKDAYS_FR[day_idx]} {hour_idx:02d}h: {format_number(value)}</title></rect>'
            )

    parts.append('</svg>')
    return "\n".join(parts)


def render_recent_table(rows: list[dict]) -> str:
    """Génère le tableau des écoutes récentes."""
    if not rows:
        return '<div class="empty-state">Aucune écoute récente à afficher.</div>'
    lines = ['<div class="recent-table">']
    lines.append('<div class="recent-table__head"><span>Moment</span><span>Titre</span><span>Album</span><span>Seconds</span></div>')
    for row in rows:
        lines.append(
            '<div class="recent-table__row">'
            f'<span>{safe_text(row["date"].strftime("%d/%m/%Y %H:%M") if row["date"] else "—")}</span>'
            f'<span><strong>{safe_text(row["title"])}</strong><small>{safe_text(row["artist"])}</small></span>'
            f'<span>{safe_text(row["album"])}</span>'
            f'<span>{format_number(row["listened_seconds"])} s</span>'
            '</div>'
        )
    lines.append('</div>')
    return "\n".join(lines)
