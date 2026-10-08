"""Briques d'interface réutilisables (HTML stylé par ``theme.py``)."""

from __future__ import annotations

import html
import re

import pandas as pd
import streamlit as st

from dashboard.utils.theme import COLORS

AVATAR_TONES = ["tone-violet", "tone-blue", "tone-green", "tone-orange", "tone-pink"]

STATUS_TONES = {
    "À surveiller": ("warning", "!"),
    "En progression": ("good", "↗"),
    "Stable": ("info", "→"),
    "Nouveau": ("neutral", "✦"),
}

ALERT_TONES = {"critical": "critical", "warning": "warning", "info": "neutral"}


# ============================================================
# BAS NIVEAU
# ============================================================

def esc(value) -> str:
    """Échappe une valeur (nom, diagnostic…) avant insertion dans du HTML."""
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return ""
    return html.escape(str(value))


def render_html(markup: str) -> None:
    """Affiche du HTML de façon fiable.

    ``st.markdown`` interprète les lignes indentées de 4 espaces comme du code et
    les lignes vides comme des fins de bloc : on compacte donc le HTML.
    """
    compact = "\n".join(line.strip() for line in markup.splitlines() if line.strip())
    compact = re.sub(r">\n\s*<", "><", compact)
    st.markdown(compact, unsafe_allow_html=True)


def fmt_number(value, decimals: int = 0, suffix: str = "", signed: bool = False) -> str:
    if value is None or pd.isna(value):
        return "—"
    sign = "+" if signed else ""
    text = f"{float(value):{sign},.{decimals}f}".replace(",", " ").replace(".", ",")
    return f"{text}{suffix}"


def fmt_date(value, pattern: str = "%d/%m/%Y") -> str:
    if value is None or pd.isna(value):
        return "—"
    return pd.Timestamp(value).strftime(pattern)


def days_ago(value, reference: pd.Timestamp) -> str:
    if value is None or pd.isna(value):
        return "Aucune séance"
    days = (reference.normalize() - pd.Timestamp(value).normalize()).days
    if days <= 0:
        return "Aujourd’hui"
    if days == 1:
        return "Hier"
    return f"Il y a {days} j"


def initials(first_name, last_name) -> str:
    letters = "".join(str(part).strip()[:1] for part in (first_name, last_name) if str(part).strip())
    return letters.upper() or "KK"


def avatar(first_name, last_name, seed: int = 0, large: bool = False) -> str:
    tone = AVATAR_TONES[int(seed) % len(AVATAR_TONES)]
    size = " lg" if large else ""
    return f'<div class="kk-avatar{size} {tone}">{esc(initials(first_name, last_name))}</div>'


def badge(text: str, tone: str = "neutral", icon: str = "") -> str:
    icon_html = f"<span>{icon}</span>" if icon else ""
    return f'<span class="kk-badge {tone}">{icon_html}{esc(text)}</span>'


def status_badge(status: str) -> str:
    tone, icon = STATUS_TONES.get(status, ("neutral", ""))
    return badge(status, tone, icon)


def alert_badges(alerts) -> str:
    return "".join(badge(a.label, ALERT_TONES.get(a.level, "neutral")) for a in alerts)


def delta_chip(value, unit: str = "", decimals: int = 1, good_when_up: bool = True) -> str:
    if value is None or pd.isna(value):
        return ""
    if abs(value) < 10 ** (-decimals) / 2:
        return f'<span class="kk-delta flat">= stable</span>'
    up = value > 0
    tone = "up" if up == good_when_up else "down"
    arrow = "▲" if up else "▼"
    return f'<span class="kk-delta {tone}">{arrow} {fmt_number(abs(value), decimals)}{unit}</span>'


# ============================================================
# STRUCTURE DE PAGE
# ============================================================

def page_header(kicker: str, title: str, subtitle: str = "", meta: str = "") -> None:
    meta_html = f'<div class="kk-meta">{meta}</div>' if meta else ""
    render_html(
        f"""
        <div class="kk-header kk-fade">
          <div>
            <div class="kk-kicker">{esc(kicker)}</div>
            <div class="kk-title">{esc(title)}</div>
            <div class="kk-subtitle">{esc(subtitle)}</div>
          </div>
          {meta_html}
        </div>
        """
    )


def section(title: str, subtitle: str = "") -> None:
    sub = f'<div class="kk-section-sub">{esc(subtitle)}</div>' if subtitle else ""
    render_html(f'<div class="kk-section"><div class="kk-section-title">{esc(title)}</div>{sub}</div>')


def card_title(title: str, subtitle: str = "") -> None:
    sub = f'<div class="kk-card-sub">{esc(subtitle)}</div>' if subtitle else ""
    render_html(f'<div class="kk-card-title">{esc(title)}</div>{sub}')


def card(key: str):
    """Conteneur blanc arrondi (stylé via la classe CSS ``st-key-card-*``)."""
    return st.container(key=f"card-{key}")


def empty_state(icon: str, title: str, text: str = "") -> None:
    render_html(
        f"""
        <div class="kk-empty">
          <div class="kk-empty-icon">{icon}</div>
          <div class="kk-empty-title">{esc(title)}</div>
          <div class="kk-empty-text">{esc(text)}</div>
        </div>
        """
    )


def note(text: str, title: str = "À noter") -> None:
    render_html(f'<div class="kk-note"><b>ⓘ</b><div><b>{esc(title)} :</b> {esc(text)}</div></div>')


# ============================================================
# KPI
# ============================================================

def kpi_card(label: str, value: str, icon: str = "✦", tone: str = "tone-violet",
             foot: str = "", delta_html: str = "", unit: str = "") -> str:
    unit_html = f"<small>{esc(unit)}</small>" if unit else ""
    return f"""
    <div class="kk-kpi kk-fade">
      <div class="kk-kpi-top">
        <div class="kk-kpi-icon {tone}">{icon}</div>
        <div class="kk-kpi-label">{esc(label)}</div>
      </div>
      <div class="kk-kpi-value">{esc(value)}{unit_html}</div>
      <div class="kk-kpi-foot">{delta_html}<span>{esc(foot)}</span></div>
    </div>
    """


def kpi_row(cards: list[str]) -> None:
    columns = st.columns(len(cards), gap="small")
    for column, markup in zip(columns, cards):
        with column:
            render_html(markup)


# ============================================================
# MINI-GRAPHIQUE (SVG inline, léger)
# ============================================================

def sparkline(values, color: str | None = None, width: int = 120, height: int = 34) -> str:
    points = [float(v) for v in values if v is not None and not pd.isna(v)]
    if len(points) < 2:
        return f'<svg width="{width}" height="{height}" aria-hidden="true"></svg>'
    color = color or COLORS["primary"]
    low, high = min(points), max(points)
    span = (high - low) or 1
    step = (width - 6) / (len(points) - 1)
    coords = [
        (3 + i * step, height - 4 - (p - low) / span * (height - 8))
        for i, p in enumerate(points)
    ]
    path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(coords))
    last_x, last_y = coords[-1]
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Évolution du score">'
        f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="3.5" fill="#fff" stroke="{color}" stroke-width="2"/>'
        f"</svg>"
    )


# ============================================================
# INSIGHTS
# ============================================================

def insight_card(insight) -> str:
    return f"""
    <div class="kk-insight {insight.tone} kk-fade">
      <div class="kk-insight-icon">{insight.icon}</div>
      <div class="kk-insight-title">{esc(insight.title)}</div>
      <div class="kk-insight-text">{esc(insight.text)}</div>
    </div>
    """
