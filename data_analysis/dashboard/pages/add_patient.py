import streamlit as st

from dashboard import navigation
from dashboard.components.ui import esc, note, page_header, render_html
from dashboard.utils import state
from dashboard.utils.api_client import ApiError, ApiPartialSuccessError
from dashboard.utils.data import save_patient

CREATED_KEY = "last_created_patient"


def _created_banner() -> None:
    created = st.session_state.get(CREATED_KEY)
    if not created:
        return
    patient, warning = created
    name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
    render_html(
        f"""
        <div class="kk-kpi kk-fade" style="min-height:0;border-color:#BFE5D0;background:#F3FBF6;margin-bottom:14px">
          <div class="kk-kpi-top">
            <div class="kk-kpi-icon tone-green">✓</div>
            <div>
              <div class="kk-card-title">Profil créé : {esc(name)}</div>
              <div class="kk-card-sub">Code patient <b>{esc(patient.get('patient_code'))}</b>
                · ID {esc(patient.get('id'))}</div>
            </div>
          </div>
        </div>
        """
    )
    if warning:
        st.warning(warning)
    col_open, col_new, _ = st.columns([1, 1, 2])
    with col_open:
        if st.button("Ouvrir la fiche →", type="primary", width="stretch"):
            st.session_state.pop(CREATED_KEY, None)
            navigation.open_patient(int(patient["id"]))
    with col_new:
        if st.button("Créer un autre patient", width="stretch"):
            st.session_state.pop(CREATED_KEY, None)
            st.rerun()


def show_add_patient():
    backend = state.api_mode_enabled()
    page_header(
        "Nouveau parcours",
        "Ajouter un patient",
        "Créez le profil d’un enfant pour démarrer son suivi de rééducation.",
    )

    if st.session_state.get(CREATED_KEY):
        _created_banner()
        return

    center, _ = st.columns([1, 0.45])
    with center:
        with st.form("add_patient_form", clear_on_submit=False):
            render_html('<div class="kk-card-title">Identité</div>')
            col1, col2, col3 = st.columns([1.2, 1.2, 0.7])
            with col1:
                first_name = st.text_input("Prénom *", placeholder="Ex. : Adam", max_chars=100)
            with col2:
                last_name = st.text_input("Nom *", placeholder="Ex. : Ben Ali", max_chars=100)
            with col3:
                age = st.number_input("Âge *", min_value=1, max_value=18, value=8, step=1)

            render_html('<div class="kk-card-title" style="margin-top:8px">Informations cliniques</div>')
            diagnosis = st.text_area(
                "Diagnostic (optionnel)",
                placeholder="Ex. : trouble développemental de la coordination",
                height=90,
            )
            submitted = st.form_submit_button("Créer le profil", type="primary", width="stretch")

        if backend:
            note("le code patient est généré par le backend et le profil est rattaché "
                 "à votre compte thérapeute. Pensez ensuite à lui assigner des jeux depuis sa fiche.",
                 title="Backend")
        else:
            note("le patient est ajouté en mémoire le temps de la session "
                 "(rien n’est écrit dans les fichiers du projet).", title="Mode démo")

    if not submitted:
        return

    errors = []
    if not first_name.strip():
        errors.append("Le prénom est obligatoire.")
    if not last_name.strip():
        errors.append("Le nom est obligatoire.")
    if errors:
        for error in errors:
            st.error(error)
        return

    try:
        with st.spinner("Création du profil…"):
            patient = save_patient(first_name, last_name, age=int(age), diagnosis=diagnosis)
        st.session_state[CREATED_KEY] = (patient, None)
        st.rerun()
    except ApiPartialSuccessError as error:
        if error.status_code == 401:
            raise
        st.session_state[CREATED_KEY] = (error.patient, str(error))
        st.rerun()
    except ApiError as error:
        if error.status_code == 401:
            raise
        st.error(f"Le backend a refusé la création : {error}")
    except ValueError as error:
        st.error(str(error))
