import sys
from pathlib import Path

# ==========================================================
# PROJECT ROOT
# ==========================================================

DATA_ANALYSIS_ROOT = Path(
    __file__
).resolve().parents[1]

if str(DATA_ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(DATA_ANALYSIS_ROOT),
    )


# ==========================================================
# STREAMLIT
# ==========================================================

import streamlit as st

from dashboard.utils.api_client import ApiError, api_mode_enabled, login as api_login
from dashboard.utils.theme import apply_theme, render_html


# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="KineKids AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================================================
# THEME
# ==========================================================

apply_theme()


# ==========================================================
# SESSION STATE
# ==========================================================

if "page" not in st.session_state:

    st.session_state[
        "page"
    ] = "Vue globale"


if "selected_patient_id" not in st.session_state:

    st.session_state[
        "selected_patient_id"
    ] = None


if api_mode_enabled() and not st.session_state.get("api_access_token"):
    st.title("Connexion thérapeute")
    st.caption("Connectez-vous avec votre compte backend KineKids AI.")
    auth_notice = st.session_state.pop("api_auth_notice", None)
    if auth_notice:
        st.info(auth_notice)
    with st.form("backend_login_form"):
        email = st.text_input("Adresse e-mail")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter", type="primary")

    if submitted:
        try:
            st.session_state["api_access_token"] = api_login(email.strip(), password)
            st.rerun()
        except ApiError as error:
            st.error(str(error))
    st.stop()


# ==========================================================
# SIDEBAR
# ==========================================================

with st.sidebar:

    if api_mode_enabled():
        st.caption("Connecté au backend KineKids AI")
        if st.button("Se déconnecter", key="backend_logout"):
            st.session_state.pop("api_access_token", None)
            st.rerun()

    render_html(
        """
        <div class="sidebar-brand">

            <div class="brand-logo">
                ✦
            </div>

            <div class="brand-title">
                KineKids AI
            </div>

            <div class="brand-subtitle">
                Rééducation pédiatrique intelligente
            </div>

        </div>
        """,
    )

    render_html(
        """
        <div style="
            font-size:11px;
            font-weight:800;
            color:#777B8C;
            margin:0 0 8px 6px;
            text-transform:uppercase;
            letter-spacing:1px;
        ">
            Navigation
        </div>
        """,
    )

    pages = [
        (
            "Vue globale",
            "◈",
        ),
        (
            "Patients",
            "○",
        ),
        (
            "Fiche patient",
            "◇",
        ),
        (
            "Ajouter un patient",
            "+",
        ),
    ]

    for page_name, icon in pages:

        is_active = (
            st.session_state["page"]
            == page_name
        )

        if st.button(
            f"{icon}  {page_name}",
            key=f"nav_{page_name}",
            width="stretch",
            type=(
                "primary"
                if is_active
                else "secondary"
            ),
        ):

            st.session_state[
                "page"
            ] = page_name

            st.rerun()

    render_html("<br>")

    render_html(
        """
        <div class="soft-card">

            <div style="
                font-family:Nunito;
                font-weight:900;
                font-size:14px;
            ">
                ✨ KineKids Intelligence
            </div>

            <div style="
                color:#777B8C;
                font-size:11px;
                margin-top:5px;
            ">
                Analyse des performances,
                progression et suivi personnalisé.
            </div>

        </div>
        """,
    )

    render_html(
        """
        <div style="
            margin-top:20px;
            text-align:center;
            color:#777B8C;
            font-size:10px;
        ">
            KineKids AI · Prototype
        </div>
        """,
    )


# ==========================================================
# ROUTER
# ==========================================================

page = st.session_state["page"]

try:
    if page == "Vue globale":
        from dashboard.pages.global_view import show_global_view

        show_global_view()

    elif page == "Patients":
        from dashboard.pages.patients import show_patients

        show_patients()

    elif page == "Fiche patient":
        from dashboard.pages.patient_detail import show_patient_detail

        show_patient_detail()

    elif page == "Ajouter un patient":
        from dashboard.pages.add_patient import show_add_patient

        show_add_patient()
except ApiError as error:
    if error.status_code == 401:
        st.session_state.pop("api_access_token", None)
        st.session_state["api_auth_notice"] = str(error)
        st.rerun()
    st.error(str(error))