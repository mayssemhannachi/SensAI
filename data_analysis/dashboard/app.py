"""SensAI — Espace thérapeute (dashboard d'analyse, Streamlit).

Le thérapeute arrive ici depuis le site SensAI : après connexion ou inscription,
le site redirige vers ce dashboard avec son jeton (``?token=...``).

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
from dashboard.utils.theme import apply_theme, logo_html  # noqa: E402

st.set_page_config(
    page_title="SensAI · Espace thérapeute",
    page_icon=str(Path(__file__).resolve().parent / "assets" / "sensai-mascot.png"),
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
# CONNEXION UNIQUE DEPUIS LE SITE (?token=...)
# ==========================================================

def consume_site_token() -> None:
    token = st.query_params.get("token")
    if not token:
        return
    st.query_params.clear()  # le jeton ne reste pas dans l'adresse
    try:
        user = api_client.me(token)
    except ApiError:
        user = None
    if user and user.get("role", "therapist") == "therapist":
        state.set_data_source("api")
        state.sign_in(token, user)
    elif user:
        st.session_state[state.NOTICE_KEY] = (
            "Ce compte est un compte patient : son espace se trouve sur le site SensAI."
        )
    else:
        st.session_state[state.NOTICE_KEY] = "Le lien de connexion a expiré. Reconnectez-vous."
    st.rerun()


consume_site_token()


# ==========================================================
# SIDEBAR
# ==========================================================

def render_sidebar(current_key: str | None, authenticated: bool) -> None:
    with st.sidebar:
        render_html(logo_html("Espace thérapeute"))

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

            render_html('<div class="kk-side-label">Mon compte</div>')
            if state.api_mode_enabled():
                user = state.current_user()
                name = esc(user.get("full_name") or "Thérapeute")
                email = esc(user.get("sub") or "")
                render_html(
                    f"""
                    <div class="kk-conn"><span class="kk-dot on"></span>
                      <div><b>{name}</b><small>{email}</small></div></div>
                    """
                )
            else:
                render_html(
                    """
                    <div class="kk-conn"><span class="kk-dot demo"></span>
                      <div>Mode hors-ligne<small>Données de démonstration</small></div></div>
                    """
                )
            col_refresh, col_logout = st.columns(2)
            with col_refresh:
                if st.button("↻ Actualiser", key="refresh_data", width="stretch",
                             help="Recharger les données"):
                    refresh_data()
                    st.rerun()
            with col_logout:
                if state.api_mode_enabled() and st.button(
                    "Déconnexion", key="backend_logout", width="stretch"
                ):
                    state.sign_out()
                    st.rerun()
            st.link_button("↗ Plateforme SensAI", api_client.site_url(), width="stretch")

        render_html('<div class="kk-side-foot">SensAI · Rééducation pédiatrique</div>')


# ==========================================================
# GESTION DES ERREURS
# ==========================================================

def render_api_error(error: ApiError) -> None:
    from dashboard.components.ui import empty_state

    empty_state("⚠️", "Les données n’ont pas pu être chargées", str(error))
    st.write("")
    _, col_retry, col_login, _ = st.columns([1, 1, 1, 1])
    with col_retry:
        if st.button("Réessayer", type="primary", width="stretch", key="err_retry"):
            refresh_data()
            st.rerun()
    with col_login:
        st.link_button("Se reconnecter", f"{api_client.site_url()}/login", width="stretch")


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

try:
    current.run()
except ApiError as error:
    if error.status_code == 401:
        state.sign_out(notice="Votre session a expiré. Reconnectez-vous.")
        st.rerun()
    render_api_error(error)
