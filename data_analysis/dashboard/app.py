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


# ==========================================================
# SIDEBAR
# ==========================================================

with st.sidebar:

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


if page == "Vue globale":

    from dashboard.pages.global_view import (
        show_global_view,
    )

    show_global_view()


elif page == "Patients":

    from dashboard.pages.patients import (
        show_patients,
    )

    show_patients()


elif page == "Fiche patient":

    from dashboard.pages.patient_detail import (
        show_patient_detail,
    )

    show_patient_detail()


elif page == "Ajouter un patient":

    from dashboard.pages.add_patient import (
        show_add_patient,
    )

    show_add_patient()