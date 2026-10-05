import pandas as pd
import streamlit as st

from dashboard.components.charts import (
    progression_chart,
    score_evolution_chart,
    success_rate_chart,
)
from dashboard.components.kpi_cards import display_kpi_row
from dashboard.utils.data import (
    load_consultations,
    load_patients,
    load_session_analysis,
    save_patient_diagnosis,
)


def show_patient_detail():

    if st.button("← Retour à tous les patients", width="content"):
        st.session_state["page"] = "Patients"
        st.rerun()

    st.title("Fiche patient")

    df = load_session_analysis()

    patients = load_patients()

    consultations = load_consultations()

    # ========================================================
    # PATIENT SELECTION
    # ========================================================

    if patients.empty or "id" not in patients.columns:
        st.info("Aucun patient enregistré.")
        return

    patient_ids = patients["id"].dropna().tolist()

    if not patient_ids:
        st.info("Aucun patient enregistré.")
        return

    patient_lookup = patients.set_index("id")
    selected_patient_id = st.session_state.get("selected_patient_id")
    selected_index = (
        patient_ids.index(selected_patient_id)
        if selected_patient_id in patient_ids
        else 0
    )

    selected_id = st.selectbox(
        "Patient",
        patient_ids,
        index=selected_index,
        format_func=lambda patient_id: (
            f"{patient_lookup.loc[patient_id, 'first_name']} "
            f"{patient_lookup.loc[patient_id, 'last_name']} · #{patient_id}"
        ),
        key="detail_patient_selectbox",
    )

    st.session_state["selected_patient_id"] = selected_id

    if st.session_state.get("diagnosis_saved_patient_id") == selected_id:
        st.success("Diagnostic enregistré.")
        st.session_state.pop("diagnosis_saved_patient_id", None)

    patient_record = patient_lookup.loc[selected_id]

    patient_data = df[
        df["patient_id"] == selected_id
    ].copy()

    full_name = (
        f"{patient_record['first_name']} "
        f"{patient_record['last_name']}"
    )

    # ========================================================
    # HEADER
    # ========================================================

    st.subheader(full_name)

    st.caption(
        f"Patient ID : {selected_id}"
    )

    st.divider()

    # ========================================================
    # INFORMATIONS PATIENT
    # ========================================================

    st.subheader("Informations patient")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.caption("Nom et prénom")

        st.write(full_name)

    with col2:

        st.caption("Date de naissance")

        birth_date = patient_record.get("date_of_birth")

        if pd.notna(birth_date):
            st.write(str(birth_date)[:10])
        else:
            st.write("Non disponible")

    with col3:

        st.caption("Diagnostic")

        diagnosis = ""

        if (
            not consultations.empty
            and "patient_id" in consultations.columns
            and "diagnosis" in consultations.columns
        ):

            patient_consultations = consultations[
                pd.to_numeric(
                    consultations["patient_id"],
                    errors="coerce",
                )
                == selected_id
            ]

            if not patient_consultations.empty:
                if "consultation_date" in patient_consultations.columns:
                    patient_consultations = patient_consultations.sort_values(
                        "consultation_date"
                    )
                diagnosis_value = patient_consultations.iloc[-1]["diagnosis"]
                if pd.notna(diagnosis_value):
                    diagnosis = str(diagnosis_value).strip()

        st.write(diagnosis or "Aucun diagnostic renseigné")

    with col4:

        st.caption("Thérapeute")

        therapist_id = patient_record.get("therapist_id")
        st.write(
            f"ID {therapist_id}"
            if pd.notna(therapist_id)
            else "Non disponible"
        )

    with st.expander("Ajouter ou modifier le diagnostic"):
        with st.form(f"diagnosis_form_{selected_id}"):
            diagnosis_input = st.text_area(
                "Diagnostic",
                value=diagnosis,
                placeholder="Saisissez le diagnostic du patient…",
            )
            diagnosis_submitted = st.form_submit_button(
                "Enregistrer le diagnostic",
                type="primary",
            )

        if diagnosis_submitted:
            try:
                therapist_id = patient_record.get("therapist_id")
                if pd.isna(therapist_id):
                    therapist_id = None
                save_patient_diagnosis(
                    patient_id=selected_id,
                    diagnosis=diagnosis_input,
                    therapist_id=therapist_id,
                )
                st.session_state["diagnosis_saved_patient_id"] = selected_id
                st.rerun()
            except (OSError, ValueError) as error:
                st.error(f"Impossible d’enregistrer le diagnostic : {error}")

    if patient_data.empty:
        st.info("Aucune séance enregistrée pour ce patient.")
        return

    st.divider()

    # ========================================================
    # SITUATION ACTUELLE
    # ========================================================

    st.subheader("Situation actuelle")

    latest = (
        patient_data
        .sort_values("session_date")
        .iloc[-1]
    )

    display_kpi_row([
        {
            "title": "Niveau actuel",
            "value": f"Niveau {int(latest['level_number'])}"
        },
        {
            "title": "Score récent",
            "value": f"{latest['score']:.1f}"
        },
        {
            "title": "Taux de réussite",
            "value": f"{latest['success_rate']:.1f}%"
        },
        {
            "title": "Progression",
            "value": (
                f"{latest['progression']:.1f}%"
                if pd.notna(latest["progression"])
                else "—"
            )
        }
    ])

    st.divider()

    # ========================================================
    # EVOLUTION
    # ========================================================

    st.subheader("Évolution")

    tab1, tab2, tab3 = st.tabs(
        [
            "Score",
            "Réussite",
            "Progression"
        ]
    )

    with tab1:

        fig = score_evolution_chart(
            patient_data
        )

        st.plotly_chart(
            fig,
            width="stretch"
        )

    with tab2:

        fig = success_rate_chart(
            patient_data
        )

        st.plotly_chart(
            fig,
            width="stretch"
        )

    with tab3:

        fig = progression_chart(
            patient_data
        )

        st.plotly_chart(
            fig,
            width="stretch"
        )

    st.divider()

    # ========================================================
    # SESSION HISTORY
    # ========================================================

    st.subheader("Historique des séances")

    history = (
        patient_data
        .sort_values(
            "session_date",
            ascending=False
        )
        .copy()
    )

    history["Date"] = (
        history["session_date"]
        .dt.strftime("%d/%m/%Y")
    )

    history_display = history[
        [
            "Date",
            "name_game",
            "level_number",
            "score",
            "success_rate",
            "repetitions",
            "duration",
            "progression"
        ]
    ].rename(
        columns={
            "name_game": "Jeu",
            "level_number": "Niveau",
            "score": "Score",
            "success_rate": "Réussite",
            "repetitions": "Répétitions",
            "duration": "Durée",
            "progression": "Progression"
        }
    )

    st.dataframe(
        history_display,
        width="stretch",
        hide_index=True
    )