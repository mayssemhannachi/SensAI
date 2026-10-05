import streamlit as st

from dashboard.utils.api_client import ApiError, ApiPartialSuccessError, api_mode_enabled
from dashboard.utils.data import save_patient
from dashboard.utils.theme import render_html


def show_add_patient():
    backend_mode = api_mode_enabled()

    render_html(
        """
        <div class="page-header animate">

            <div class="page-kicker">
                NOUVEAU PARCOURS
            </div>

            <div class="page-title">
                Ajouter un patient 🌱
            </div>

            <div class="page-description">
                Créez le profil initial d'un enfant pour commencer
                son parcours de rééducation.
            </div>

        </div>
        """,
    )

    # ======================================================
    # FORM
    # ======================================================

    with st.form(
        "add_patient_form",
        clear_on_submit=True,
    ):

        render_html(
            """
            <div class="section-title">
                Informations personnelles
            </div>
            """,
        )

        col1, col2 = st.columns(
            2,
            gap="large",
        )

        with col1:

            first_name = st.text_input(
                "Prénom *",
                placeholder="Ex : Adam",
            )

        with col2:

            last_name = st.text_input(
                "Nom *",
                placeholder="Ex : Ben Ali",
            )

        if backend_mode:
            age = st.number_input(
                "Âge *",
                min_value=0,
                max_value=18,
                value=8,
                step=1,
            )
            date_of_birth = None
            patient_code = None
            st.caption("Le backend génère automatiquement le code patient.")
        else:
            col1, col2 = st.columns(
                2,
                gap="large",
            )

            with col1:
                date_of_birth = st.date_input(
                    "Date de naissance *"
                )

            with col2:
                patient_code = st.text_input(
                    "Code patient *",
                    placeholder="Ex : KID-2026-001",
                )
            age = None

        render_html(
            """
            <div class="section-title">
                Informations thérapeutiques
            </div>
            """,
        )

        diagnosis = st.text_input(
            "Diagnostic",
            placeholder="Ex : Déficit de coordination motrice",
        )

        st.caption(
            "Le diagnostic pourra être complété ou modifié lors des consultations."
        )

        submitted = st.form_submit_button(
            "Créer le profil",
            type="primary",
            width="stretch",
        )

    # ======================================================
    # VALIDATION
    # ======================================================

    if submitted:

        errors = []

        if not first_name.strip():
            errors.append(
                "Le prénom est obligatoire."
            )

        if not last_name.strip():
            errors.append(
                "Le nom est obligatoire."
            )

        if not backend_mode and not patient_code.strip():
            errors.append(
                "Le code patient est obligatoire."
            )

        if errors:

            for error in errors:
                st.error(error)

            return

        try:

            patient_id = save_patient(
                first_name=first_name,
                last_name=last_name,
                date_of_birth=date_of_birth,
                patient_code=patient_code,
                diagnosis=diagnosis,
                age=age,
            )

            if backend_mode:
                st.success(
                    "Patient enregistré dans le backend. "
                    f"ID : {patient_id['id']} · Code : {patient_id['patient_code']}"
                )
            else:
                st.success(
                    f"Patient créé avec succès. ID : {patient_id}"
                )

            st.balloons()

        except ApiPartialSuccessError as error:
            if error.status_code == 401:
                st.session_state.pop("api_access_token", None)
                st.session_state["api_auth_notice"] = (
                    f"{error} Patient déjà créé : ID {error.patient.get('id')} · "
                    f"code {error.patient.get('patient_code')}"
                )
                st.rerun()
            st.warning(
                f"{error} Le patient reste bien enregistré : "
                f"ID {error.patient.get('id')} · code {error.patient.get('patient_code')}"
            )

        except ApiError as error:
            if error.status_code == 401:
                st.session_state.pop("api_access_token", None)
                st.session_state["api_auth_notice"] = str(error)
                st.rerun()
            st.error(f"Erreur backend : {error}")

        except ValueError as error:

            st.error(
                str(error)
            )

        except Exception as error:

            st.error(
                f"Erreur lors de l'enregistrement : {error}"
            )