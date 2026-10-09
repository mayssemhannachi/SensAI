"""État de session du dashboard : source de données, authentification, navigation."""

from __future__ import annotations

import streamlit as st

from dashboard.utils.api_client import default_data_source

SOURCE_KEY = "data_source"
TOKEN_KEY = "api_access_token"
USER_KEY = "api_user"
NOTICE_KEY = "api_auth_notice"
PATIENT_KEY = "selected_patient_id"

SOURCE_LABELS = {"demo": "Démo", "api": "Backend"}


def get_data_source() -> str:
    try:
        source = st.session_state.get(SOURCE_KEY)
    except Exception:  # hors runtime Streamlit (tests, scripts)
        source = None
    return source if source in SOURCE_LABELS else default_data_source()


def set_data_source(source: str) -> None:
    if source not in SOURCE_LABELS:
        return
    if st.session_state.get(SOURCE_KEY) != source:
        st.session_state[SOURCE_KEY] = source
        # Les identifiants patients ne sont pas les mêmes entre les deux sources.
        st.session_state.pop(PATIENT_KEY, None)
        st.cache_data.clear()


def api_mode_enabled() -> bool:
    return get_data_source() == "api"


def get_token() -> str | None:
    try:
        return st.session_state.get(TOKEN_KEY)
    except Exception:
        return None


def sign_in(token: str, user: dict | None = None) -> None:
    st.session_state[TOKEN_KEY] = token
    st.session_state[USER_KEY] = user or {}
    st.cache_data.clear()


# Page du site SensAI vers laquelle renvoyer un visiteur non connecté
# (« /login » par défaut ; « /logout?reason=… » après une déconnexion).
REDIRECT_KEY = "site_redirect"


def sign_out(notice: str | None = None, site_path: str | None = None) -> None:
    if site_path:
        st.session_state[REDIRECT_KEY] = site_path
    st.session_state.pop(TOKEN_KEY, None)
    st.session_state.pop(USER_KEY, None)
    st.session_state.pop(PATIENT_KEY, None)
    if notice:
        st.session_state[NOTICE_KEY] = notice
    st.cache_data.clear()


def current_user() -> dict:
    return st.session_state.get(USER_KEY) or {}


def selected_patient_id():
    return st.session_state.get(PATIENT_KEY)


def select_patient(patient_id) -> None:
    st.session_state[PATIENT_KEY] = patient_id
