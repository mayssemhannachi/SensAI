import pandas as pd
import streamlit as st

from dashboard.utils.data import (
    get_initials,
    load_patients,
    load_session_analysis,
)
from dashboard.utils.theme import render_html


def show_patients():

    render_html(
        """
        <div class="page-header animate">

            <div class="page-kicker">
                SUIVI DES ENFANTS
            </div>

            <div class="page-title">
                Mes patients ✨
            </div>

            <div class="page-description">
                Recherchez rapidement un enfant et accédez à son parcours
                de rééducation.
            </div>

        </div>
        """,
    )

    patients = load_patients()
    sessions = load_session_analysis()

    if patients.empty:

        st.info(
            "Aucun patient enregistré."
        )

        return

    # ======================================================
    # SEARCH
    # ======================================================

    search = st.text_input(
        "Rechercher",
        placeholder="Nom, prénom ou code patient...",
        label_visibility="collapsed",
    )

    filtered = patients.copy()

    if search.strip():

        query = search.lower().strip()

        mask = (
            filtered["first_name"]
            .astype(str)
            .str.lower()
            .str.contains(query, na=False)
            |
            filtered["last_name"]
            .astype(str)
            .str.lower()
            .str.contains(query, na=False)
            |
            filtered["patient_code"]
            .astype(str)
            .str.lower()
            .str.contains(query, na=False)
        )

        filtered = filtered[mask]

    # ======================================================
    # COUNT
    # ======================================================

    st.caption(
        f"{len(filtered)} patient(s) trouvé(s)"
    )

    # ======================================================
    # PATIENT CARDS
    # ======================================================

    for start in range(
        0,
        len(filtered),
        2,
    ):

        row = filtered.iloc[
            start:start + 2
        ]

        columns = st.columns(
            len(row),
            gap="medium",
        )

        for column, (_, patient) in zip(
            columns,
            row.iterrows(),
        ):

            with column:

                patient_id = patient["id"]

                patient_sessions = sessions[
                    sessions["patient_id"]
                    == patient_id
                ]

                if not patient_sessions.empty:

                    latest = (
                        patient_sessions
                        .sort_values("session_date")
                        .iloc[-1]
                    )

                    score = latest["score"]

                    success = latest[
                        "success_rate"
                    ]

                    progression = latest[
                        "progression"
                    ]

                else:

                    score = None
                    success = None
                    progression = None

                initials = get_initials(
                    patient["first_name"],
                    patient["last_name"],
                )

                score_text = (
                    f"{score:.1f}"
                    if pd.notna(score)
                    else "—"
                )

                success_text = (
                    f"{success:.1f}%"
                    if pd.notna(success)
                    else "—"
                )

                if pd.notna(progression):

                    progression_text = (
                        f"{progression:+.1f}%"
                    )

                    badge_class = (
                        "badge-positive"
                        if progression >= 0
                        else "badge-negative"
                    )

                else:

                    progression_text = "—"
                    badge_class = "badge-neutral"

                render_html(
                    f"""
                    <div class="patient-card animate">

                        <div style="
                            display:flex;
                            align-items:center;
                            gap:14px;
                        ">

                            <div class="patient-avatar">
                                {initials}
                            </div>

                            <div>
                                <div style="
                                    font-family:Nunito;
                                    font-weight:900;
                                    font-size:17px;
                                ">
                                    {patient["first_name"]}
                                    {patient["last_name"]}
                                </div>

                                <div style="
                                    color:#777B8C;
                                    font-size:11px;
                                ">
                                    Code :
                                    {patient.get("patient_code", "—")}
                                </div>
                            </div>

                        </div>

                        <div style="
                            display:grid;
                            grid-template-columns:
                                repeat(3,1fr);
                            gap:8px;
                            margin-top:18px;
                        ">

                            <div>
                                <div style="
                                    color:#777B8C;
                                    font-size:10px;
                                ">
                                    Score
                                </div>

                                <strong>
                                    {score_text}
                                </strong>
                            </div>

                            <div>
                                <div style="
                                    color:#777B8C;
                                    font-size:10px;
                                ">
                                    Réussite
                                </div>

                                <strong>
                                    {success_text}
                                </strong>
                            </div>

                            <div>
                                <div style="
                                    color:#777B8C;
                                    font-size:10px;
                                ">
                                    Progression
                                </div>

                                <span class="badge {badge_class}">
                                    {progression_text}
                                </span>
                            </div>

                        </div>

                    </div>
                    """,
                )

                if st.button(
                    "Ouvrir la fiche",
                    key=f"patient_{patient_id}",
                    width="stretch",
                ):

                    st.session_state[
                        "selected_patient_id"
                    ] = patient_id

                    st.session_state[
                        "page"
                    ] = "Fiche patient"

                    st.rerun()