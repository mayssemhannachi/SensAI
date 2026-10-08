"""Design system KineKids : couleurs, typographie et CSS global."""

from __future__ import annotations

import streamlit as st

# ============================================================
# TOKENS
# ============================================================

COLORS = {
    # Surfaces & texte
    "background": "#F6F7FB",
    "surface": "#FFFFFF",
    "surface_soft": "#F8F9FC",
    "text": "#1E2638",
    "text_secondary": "#475467",
    "muted": "#667085",
    "border": "#E6E8F0",
    "grid": "#EEF0F5",
    # Marque
    "primary": "#5B5BD6",
    "primary_dark": "#4343B8",
    "primary_soft": "#EEEEFC",
    # Statuts (réservés : jamais utilisés comme couleur de série)
    "good": "#0E8A4F",
    "good_bg": "#E7F6EE",
    "warning": "#B76E00",
    "warning_bg": "#FFF4E0",
    "critical": "#C93A3A",
    "critical_bg": "#FDECEC",
    "info": "#3A63B8",
    "info_bg": "#ECF2FD",
    "neutral": "#5D6679",
    "neutral_bg": "#F0F2F6",
}

# Palette catégorielle (ordre fixe, validée daltonisme pour les 3 premiers
# créneaux) — une couleur suit toujours la même entité (ex. le même jeu).
SERIES = ["#2A78D6", "#EB6834", "#1BAF7A", "#EDA100", "#E87BA4", "#008300", "#4A3AA7", "#E34948"]

# Mesures : couleur stable pour une même métrique dans tous les graphiques.
METRIC_COLORS = {
    "score": "#2A78D6",
    "success_rate": "#1BAF7A",
}

# Rampe séquentielle (bleu, clair → foncé) pour les heatmaps.
SEQUENTIAL = ["#CDE2FB", "#9EC5F4", "#6DA7EC", "#3987E5", "#256ABF", "#184F95", "#0D366B"]

FONT_BODY = "DM Sans"
FONT_TITLE = "Nunito"


def get_colors() -> dict:
    return COLORS.copy()


# ============================================================
# CSS GLOBAL
# ============================================================

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&family=Nunito:wght@700;800;900&display=swap');

:root {
  --kk-bg: %(background)s;
  --kk-surface: %(surface)s;
  --kk-surface-soft: %(surface_soft)s;
  --kk-text: %(text)s;
  --kk-text-2: %(text_secondary)s;
  --kk-muted: %(muted)s;
  --kk-border: %(border)s;
  --kk-primary: %(primary)s;
  --kk-primary-dark: %(primary_dark)s;
  --kk-primary-soft: %(primary_soft)s;
  --kk-good: %(good)s;       --kk-good-bg: %(good_bg)s;
  --kk-warning: %(warning)s; --kk-warning-bg: %(warning_bg)s;
  --kk-critical: %(critical)s; --kk-critical-bg: %(critical_bg)s;
  --kk-info: %(info)s;       --kk-info-bg: %(info_bg)s;
  --kk-neutral: %(neutral)s; --kk-neutral-bg: %(neutral_bg)s;
  --kk-radius: 18px;
  --kk-shadow: 0 1px 2px rgba(16, 24, 40, .04), 0 6px 18px rgba(16, 24, 40, .05);
}

html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea, select {
  font-family: "DM Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
}
.stApp { background: var(--kk-bg); color: var(--kk-text); }
.block-container { padding-top: 1.6rem !important; padding-bottom: 4rem !important; max-width: 1380px; }
[data-testid="stDecoration"], #MainMenu, footer { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }
h1, h2, h3, h4 { font-family: "Nunito", "DM Sans", sans-serif; color: var(--kk-text); }

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid var(--kk-border); }
section[data-testid="stSidebar"] .block-container { padding-top: 1rem !important; }
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: .45rem; }
.kk-brand { display: flex; align-items: center; gap: 12px; padding: 4px 4px 18px; }
.kk-brand-logo {
  width: 42px; height: 42px; border-radius: 13px; display: grid; place-items: center;
  background: linear-gradient(135deg, #5B5BD6 0%%, #8E7CF0 55%%, #4FB7A0 100%%);
  color: #fff; font: 900 20px "Nunito", sans-serif; box-shadow: 0 6px 14px rgba(91, 91, 214, .28);
}
.kk-brand-name { font: 900 18px "Nunito", sans-serif; color: var(--kk-text); line-height: 1.1; }
.kk-brand-sub { font-size: 11.5px; color: var(--kk-muted); margin-top: 2px; }
.kk-side-label {
  font-size: 10.5px; font-weight: 700; letter-spacing: .09em; text-transform: uppercase;
  color: var(--kk-muted); margin: 16px 4px 8px;
}
section[data-testid="stSidebar"] .stButton > button {
  justify-content: flex-start; text-align: left; border: 1px solid transparent !important;
  background: transparent !important; box-shadow: none !important; color: var(--kk-text-2) !important;
  font-weight: 600 !important; padding: .5rem .8rem !important;
}
section[data-testid="stSidebar"] .stButton > button > div { justify-content: flex-start; width: 100%%; }
section[data-testid="stSidebar"] .stButton > button p { text-align: left; }
section[data-testid="stSidebar"] [class*="st-key-refresh_data"] .stButton > button,
section[data-testid="stSidebar"] [class*="st-key-backend_logout"] .stButton > button {
  border: 1px solid var(--kk-border) !important; background: #FFFFFF !important; justify-content: center;
}
section[data-testid="stSidebar"] [class*="st-key-refresh_data"] button > div,
section[data-testid="stSidebar"] [class*="st-key-backend_logout"] button > div { justify-content: center; }
section[data-testid="stSidebar"] .stButton > button:hover {
  background: var(--kk-surface-soft) !important; color: var(--kk-text) !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
  background: var(--kk-primary-soft) !important; color: var(--kk-primary-dark) !important;
  border-color: #D9D9F7 !important;
}
.kk-conn {
  display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--kk-text-2);
  background: var(--kk-surface-soft); border: 1px solid var(--kk-border); border-radius: 12px; padding: 9px 11px;
}
.kk-conn small { display: block; color: var(--kk-muted); font-size: 11px; }
.kk-dot { width: 8px; height: 8px; border-radius: 50%%; flex-shrink: 0; }
.kk-dot.on { background: var(--kk-good); box-shadow: 0 0 0 3px var(--kk-good-bg); }
.kk-dot.off { background: var(--kk-critical); box-shadow: 0 0 0 3px var(--kk-critical-bg); }
.kk-dot.demo { background: var(--kk-warning); box-shadow: 0 0 0 3px var(--kk-warning-bg); }
.kk-side-foot { font-size: 10.5px; color: var(--kk-muted); text-align: center; margin-top: 18px; }

/* ---------- Boutons ---------- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  border-radius: 11px !important; font-weight: 600 !important; font-size: 13px !important;
  transition: background .15s ease, border-color .15s ease, color .15s ease;
}
.stButton > button[kind="secondary"], .stDownloadButton > button {
  background: #FFFFFF !important; border: 1px solid var(--kk-border) !important; color: var(--kk-text) !important;
}
.stButton > button[kind="secondary"]:hover, .stDownloadButton > button:hover {
  border-color: #C9C9F2 !important; background: var(--kk-primary-soft) !important; color: var(--kk-primary-dark) !important;
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"],
.stFormSubmitButton > button {
  background: var(--kk-primary) !important; border: 1px solid var(--kk-primary) !important; color: #fff !important;
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button:hover {
  background: var(--kk-primary-dark) !important; border-color: var(--kk-primary-dark) !important;
}

/* ---------- Champs ---------- */
div[data-baseweb="select"] > div, div[data-baseweb="input"], div[data-baseweb="textarea"],
div[data-baseweb="base-input"] {
  border-radius: 11px !important; border-color: var(--kk-border) !important; background: #FFFFFF !important;
}
[data-testid="stTextInputRootElement"], [data-testid="stNumberInputContainer"],
[data-testid="stTextInput"] div[data-baseweb="input"], [data-testid="stNumberInput"] div[data-baseweb="input"],
[data-testid="stTextArea"] div[data-baseweb="textarea"], [data-testid="stDateInput"] div[data-baseweb="input"] {
  border: 1px solid #D9DDE7 !important; background: #FBFBFD !important;
}
[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within, [data-testid="stTextArea"] div[data-baseweb="textarea"]:focus-within,
[data-testid="stNumberInput"] div[data-baseweb="input"]:focus-within {
  border-color: var(--kk-primary) !important; box-shadow: 0 0 0 3px rgba(91, 91, 214, .12);
}
[data-testid="stTextInput"] div[data-baseweb="base-input"], [data-testid="stNumberInput"] div[data-baseweb="base-input"],
[data-testid="stTextArea"] div[data-baseweb="base-input"] { border: none !important; background: transparent !important; }
[data-testid="stWidgetLabel"] p { font-size: 12.5px !important; font-weight: 600 !important; color: var(--kk-text-2) !important; }

/* ---------- Cartes (conteneurs bordés Streamlit) ---------- */
div[class*="st-key-card"] {
  background: var(--kk-surface); border: 1px solid var(--kk-border) !important; border-radius: var(--kk-radius);
  box-shadow: var(--kk-shadow); padding: 18px 20px 12px !important;
}
[data-testid="stForm"] {
  background: var(--kk-surface); border: 1px solid var(--kk-border) !important; border-radius: var(--kk-radius);
  box-shadow: var(--kk-shadow); padding: 22px 24px !important;
}

/* ---------- En-tête de page ---------- */
.kk-header { display: flex; justify-content: space-between; align-items: flex-end; gap: 24px; margin: 4px 0 22px; flex-wrap: wrap; }
.kk-kicker { font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--kk-primary); }
.kk-title { font: 900 30px/1.15 "Nunito", sans-serif; color: var(--kk-text); margin-top: 4px; }
.kk-subtitle { font-size: 14px; color: var(--kk-muted); margin-top: 6px; max-width: 680px; }
.kk-meta { display: inline-flex; align-items: center; gap: 8px; font-size: 12px; color: var(--kk-text-2);
  background: #FFFFFF; border: 1px solid var(--kk-border); border-radius: 999px; padding: 7px 13px; white-space: nowrap; }

/* ---------- Sections ---------- */
.kk-section { margin: 30px 0 12px; }
.kk-section-title { font: 800 19px "Nunito", sans-serif; color: var(--kk-text); }
.kk-section-sub { font-size: 13px; color: var(--kk-muted); margin-top: 2px; }
.kk-card-title { font: 800 15.5px "Nunito", sans-serif; color: var(--kk-text); }
.kk-card-sub { font-size: 12.5px; color: var(--kk-muted); margin: 2px 0 4px; }

/* ---------- KPI ---------- */
.kk-kpi {
  background: var(--kk-surface); border: 1px solid var(--kk-border); border-radius: var(--kk-radius);
  box-shadow: var(--kk-shadow); padding: 16px 18px; height: 100%%; min-height: 158px; position: relative; overflow: hidden;
}
.kk-kpi-top { display: flex; align-items: center; gap: 10px; }
.kk-kpi-icon { width: 34px; height: 34px; border-radius: 11px; display: grid; place-items: center; font-size: 16px; font-weight: 800; }
.kk-kpi-label { font-size: 12.5px; font-weight: 600; color: var(--kk-text-2); }
.kk-kpi-value { font: 900 30px/1 "Nunito", sans-serif; color: var(--kk-text); margin-top: 14px; letter-spacing: -.01em; }
.kk-kpi-value small { font-size: 16px; font-weight: 800; color: var(--kk-muted); margin-left: 2px; }
.kk-kpi-foot { display: flex; align-items: center; gap: 6px; margin-top: 9px; font-size: 11.5px; color: var(--kk-muted); flex-wrap: wrap; }
.kk-delta { font-weight: 700; border-radius: 999px; padding: 2px 8px; font-size: 11px; }
.kk-delta.up { color: var(--kk-good); background: var(--kk-good-bg); }
.kk-delta.down { color: var(--kk-critical); background: var(--kk-critical-bg); }
.kk-delta.flat { color: var(--kk-neutral); background: var(--kk-neutral-bg); }
.tone-violet { background: #EEEEFC; color: #4343B8; }
.tone-blue { background: #E6F0FC; color: #1F5FAE; }
.tone-green { background: #E3F6EE; color: #0E7A55; }
.tone-orange { background: #FDEDE4; color: #B2491C; }
.tone-pink { background: #FCEAF1; color: #A8386A; }

/* ---------- Badges ---------- */
.kk-badge { display: inline-flex; align-items: center; gap: 5px; font-size: 11.5px; font-weight: 700;
  border-radius: 999px; padding: 4px 10px; white-space: nowrap; line-height: 1.3; }
.kk-badge.good { color: var(--kk-good); background: var(--kk-good-bg); }
.kk-badge.warning { color: var(--kk-warning); background: var(--kk-warning-bg); }
.kk-badge.critical { color: var(--kk-critical); background: var(--kk-critical-bg); }
.kk-badge.info { color: var(--kk-info); background: var(--kk-info-bg); }
.kk-badge.neutral { color: var(--kk-neutral); background: var(--kk-neutral-bg); }
.kk-badge.brand { color: var(--kk-primary-dark); background: var(--kk-primary-soft); }

/* ---------- Avatar ---------- */
.kk-avatar { width: 44px; height: 44px; border-radius: 14px; display: grid; place-items: center; flex-shrink: 0;
  font: 900 15px "Nunito", sans-serif; }
.kk-avatar.lg { width: 66px; height: 66px; border-radius: 20px; font-size: 22px; }

/* ---------- Carte patient ---------- */
.kk-pcard-head { display: flex; align-items: center; gap: 12px; }
.kk-pcard-name { font: 800 16px "Nunito", sans-serif; color: var(--kk-text); line-height: 1.2; }
.kk-pcard-meta { font-size: 11.5px; color: var(--kk-muted); margin-top: 2px; }
.kk-pcard-head .kk-badge { margin-left: auto; }
.kk-pcard-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 14px 0 8px; }
.kk-stat { background: var(--kk-surface-soft); border: 1px solid #EEF0F5; border-radius: 12px; padding: 8px 10px; }
.kk-stat-label { font-size: 10.5px; font-weight: 700; color: var(--kk-muted); text-transform: uppercase; letter-spacing: .04em; }
.kk-stat-value { font: 900 18px "Nunito", sans-serif; color: var(--kk-text); margin-top: 1px; }
.kk-stat-value.pos { color: var(--kk-good); } .kk-stat-value.neg { color: var(--kk-critical); }
.kk-pcard-foot { display: flex; justify-content: space-between; align-items: center; gap: 10px;
  font-size: 11.5px; color: var(--kk-muted); padding-top: 8px; border-top: 1px solid #EEF0F5; margin-bottom: 6px; }
.kk-alerts { display: flex; gap: 6px; flex-wrap: wrap; min-height: 22px; margin-top: 6px; }

/* ---------- Liste d'attention ---------- */
.kk-watch { display: flex; align-items: center; gap: 12px; padding: 10px 0; }
.kk-watch-name { font-weight: 700; font-size: 14px; color: var(--kk-text); }
.kk-watch-detail { font-size: 12px; color: var(--kk-muted); margin-top: 2px; }

/* ---------- Insights ---------- */
.kk-insight { border-radius: 16px; padding: 16px; height: 100%%; min-height: 128px; border: 1px solid var(--kk-border); background: #FFFFFF; }
.kk-insight-icon { width: 30px; height: 30px; border-radius: 10px; display: grid; place-items: center; font-weight: 900; font-size: 15px; }
.kk-insight-title { font: 800 14.5px "Nunito", sans-serif; color: var(--kk-text); margin-top: 10px; }
.kk-insight-text { font-size: 12.5px; color: var(--kk-text-2); margin-top: 4px; line-height: 1.5; }
.kk-insight.positive .kk-insight-icon { background: var(--kk-good-bg); color: var(--kk-good); }
.kk-insight.warning .kk-insight-icon { background: var(--kk-warning-bg); color: var(--kk-warning); }
.kk-insight.neutral .kk-insight-icon { background: var(--kk-info-bg); color: var(--kk-info); }

/* ---------- Fiche patient ---------- */
.kk-hero { background: linear-gradient(120deg, #FFFFFF 0%%, #F6F5FF 60%%, #EEF8F5 100%%);
  border: 1px solid var(--kk-border); border-radius: 22px; box-shadow: var(--kk-shadow); padding: 22px 24px; margin-bottom: 18px; }
.kk-hero-row { display: flex; align-items: center; gap: 18px; flex-wrap: wrap; }
.kk-hero-name { font: 900 28px/1.1 "Nunito", sans-serif; color: var(--kk-text); }
.kk-hero-meta { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
.kk-hero-dx { margin-top: 14px; font-size: 13px; color: var(--kk-text-2); }
.kk-hero-dx b { color: var(--kk-text); }

/* ---------- Divers ---------- */
.kk-empty { text-align: center; padding: 44px 20px; background: #FFFFFF; border: 1px dashed #D5D9E3; border-radius: var(--kk-radius); }
.kk-empty-icon { font-size: 30px; }
.kk-empty-title { font: 800 18px "Nunito", sans-serif; color: var(--kk-text); margin-top: 6px; }
.kk-empty-text { font-size: 13px; color: var(--kk-muted); margin-top: 4px; }
.kk-note { display: flex; gap: 10px; align-items: flex-start; font-size: 12px; color: var(--kk-text-2);
  background: var(--kk-info-bg); border-radius: 12px; padding: 10px 12px; margin-top: 10px; }
.kk-note b { color: var(--kk-info); }
.kk-banner { display: flex; gap: 10px; align-items: center; font-size: 12.5px; color: #7A4B00;
  background: #FFF6E5; border: 1px solid #F6DFB4; border-radius: 12px; padding: 9px 14px; margin-bottom: 14px; }
.kk-login { max-width: 440px; margin: 7vh auto 0; }
.kk-login-head { text-align: center; margin-bottom: 18px; }
.kk-login-head .kk-brand-logo { margin: 0 auto 12px; width: 56px; height: 56px; border-radius: 17px; font-size: 26px; }
[data-testid="stDataFrame"] { border: 1px solid var(--kk-border); border-radius: 14px; overflow: hidden; }
button[data-baseweb="tab"] p { font-weight: 600 !important; font-size: 13.5px !important; }
[data-testid="stExpander"] details { border-radius: 14px !important; border-color: var(--kk-border) !important; background: #FFFFFF; }
.kk-fade { animation: kkFade .3s ease-out; }
@keyframes kkFade { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
"""


def apply_theme() -> None:
    st.html(f"<style>{_CSS % COLORS}</style>")
