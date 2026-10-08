"""KineKids AI — Dashboard thérapeute (Streamlit).

Lancement (depuis le dossier ``data_analysis``) :
    streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

DATA_ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
if str(DATA_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(DATA_ANALYSIS_ROOT))

import streamlit as st  # noqa: E402

from dashboard import navigation  # noqa: E402
from dashboard.components.ui import esc, render_html  # noqa: E402
from dashboard.utils import api_client, state  # noqa: E402
from dashboard.utils.api_client import ApiError  # noqa: E402
from dashboard.utils.data import refresh_data  # noqa: E402
from dashboard.utils.theme import apply_theme  # noqa: E402

st.set_page_config(
    page_title="KineKids AI · Thérapeute",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()


# ==========================================================
# PAGES (import paresseux pour garder un démarrage rapide)
# ==========================================================

def _overview():
    from dashboard.pages.global_view import show_global_view
    show_global_view()


def _patients():
    from dashboard.pages.patients import show_patients
    show_patients()


def _patient():
    from dashboard.pages.patient_detail import show_patient_detail
    show_patient_detail()


def _games():
    from dashboard.pages.games import show_games
    show_games()


def _add_patient():
    from dashboard.pages.add_patient import show_add_patient
    show_add_patient()


def _login():
    from dashboard.pages.login import show_login
    show_login()


PAGE_FUNCTIONS = {
    "overview": _overview,
    "patients": _patients,
    "patient": _patient,
    "games": _games,
    "add_patient": _add_patient,
}


# ==========================================================
# SIDEBAR
# ==========================================================

def _on_source_change():
    choice = st.session_state.get("source_selector")
    if choice:
        state.set_data_source(choice)
    else:  # désélection : on garde la source courante
        st.session_state["source_selector"] = state.get_data_source()


def render_sidebar(current_key: str | None, authenticated: bool) -> None:
    with st.sidebar:
        render_html(
            """
            <div class="kk-brand">
              <div class="kk-brand-logo">K</div>
              <div>
                <div class="kk-brand-name">KineKids AI</div>
                <div class="kk-brand-sub">Espace thérapeute</div>
              </div>
            </div>
            """
        )

        if authenticated:
            render_html('<div class="kk-side-label">Navigation</div>')
            for key, (title, icon, _) in navigation.PAGES.items():
                if st.button(
                    f"{icon}  {title}",
                    key=f"nav_{key}",
                    width="stretch",
                    type="primary" if key == current_key else "secondary",
                ):
                    navigation.go(key)

        render_html('<div class="kk-side-label">Source des données</div>')
        if st.session_state.get("source_selector") != state.get_data_source():
            st.session_state["source_selector"] = state.get_data_source()
        st.segmented_control(
            "Source des données",
            options=list(state.SOURCE_LABELS),
            format_func=lambda key: state.SOURCE_LABELS[key],
            key="source_selector",
            on_change=_on_source_change,
            label_visibility="collapsed",
            width="stretch",
        )

        if state.api_mode_enabled():
            user = state.current_user()
            if authenticated:
                email = esc(user.get("sub") or "Thérapeute connecté")
                render_html(
                    f"""
                    <div class="kk-conn"><span class="kk-dot on"></span>
                      <div>Backend connecté<small>{email}</small></div></div>
                    """
                )
            else:
                online = api_client.health()
                dot, text = ("on", "Backend disponible") if online else ("off", "Backend injoignable")
                render_html(
                    f"""
                    <div class="kk-conn"><span class="kk-dot {dot}"></span>
                      <div>{text}<small>{esc(api_client.api_base_url())}</small></div></div>
                    """
                )
        else:
            render_html(
                """
                <div class="kk-conn"><span class="kk-dot demo"></span>
                  <div>Mode démo<small>Données synthétiques, aucune donnée réelle</small></div></div>
                """
            )

        if authenticated:
            col_refresh, col_logout = st.columns(2) if state.api_mode_enabled() else (st.container(), None)
            with col_refresh:
                if st.button("↻ Actualiser", key="refresh_data", width="stretch",
                             help="Recharger les données"):
                    refresh_data()
                    st.rerun()
            if col_logout is not None:
                with col_logout:
                    if st.button("Déconnexion", key="backend_logout", width="stretch"):
                        state.sign_out()
                        st.rerun()

        render_html('<div class="kk-side-foot">KineKids AI · Data Analysis & Therapist Dashboard</div>')


# ==========================================================
# GESTION DES ERREURS
# ==========================================================

def render_api_error(error: ApiError) -> None:
    from dashboard.components.ui import empty_state

    empty_state("⚠️", "Le backend n’a pas pu fournir les données", str(error))
    st.write("")
    _, col_retry, col_demo, _ = st.columns([1, 1, 1, 1])
    with col_retry:
        if st.button("Réessayer", type="primary", width="stretch", key="err_retry"):
            refresh_data()
            st.rerun()
    with col_demo:
        if st.button("Passer en mode démo", width="stretch", key="err_demo"):
            state.set_data_source("demo")
            st.rerun()


# ==========================================================
# ROUTAGE
# ==========================================================

authenticated = not state.api_mode_enabled() or bool(state.get_token())

if authenticated:
    pages = {
        key: st.Page(PAGE_FUNCTIONS[key], title=title, url_path=url, default=(key == "overview"))
        for key, (title, _, url) in navigation.PAGES.items()
    }
else:
    pages = {"login": st.Page(_login, title="Connexion", url_path="connexion", default=True)}

navigation.register(pages)
current = st.navigation(list(pages.values()), position="hidden")
current_key = next((k for k, p in pages.items() if p.url_path == current.url_path), None)

render_sidebar(current_key, authenticated)

if not state.api_mode_enabled():
    render_html(
        '<div class="kk-banner">🧪 <span><b>Mode démo</b> — données synthétiques. '
        'Basculez sur « Backend » dans le menu pour utiliser les données réelles.</span></div>'
    )

try:
    current.run()
except ApiError as error:
    if error.status_code == 401:
        state.sign_out(notice=str(error))
        st.rerun()
    render_api_error(error)
