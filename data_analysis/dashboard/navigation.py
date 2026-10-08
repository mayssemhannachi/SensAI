"""Navigation entre les pages (st.navigation masquée + menu personnalisé)."""

from __future__ import annotations

import streamlit as st

from dashboard.utils import state

# clé → (titre, icône du menu, chemin d'URL)
PAGES = {
    "overview": ("Vue globale", "◈", "vue-globale"),
    "patients": ("Patients", "◉", "patients"),
    "patient": ("Fiche patient", "◇", "fiche-patient"),
    "games": ("Jeux", "▲", "jeux"),
    "add_patient": ("Ajouter un patient", "＋", "ajouter-patient"),
}

_REGISTRY: dict[str, st.Page] = {}


def register(pages: dict[str, st.Page]) -> None:
    _REGISTRY.clear()
    _REGISTRY.update(pages)


def go(page_key: str, patient_id=None) -> None:
    if patient_id is not None:
        state.select_patient(patient_id)
    st.switch_page(_REGISTRY[page_key])


def open_patient(patient_id) -> None:
    go("patient", patient_id=patient_id)
