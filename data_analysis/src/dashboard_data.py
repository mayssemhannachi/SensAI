import pandas as pd


def get_patient_history(
    session_analysis,
    patient_id
):
    """
    Retourne l'historique complet d'un patient.
    """

    history = session_analysis[
        session_analysis["patient_id"] == patient_id
    ].copy()

    history = history.sort_values(
        "session_date"
    )

    return history


def get_patient_kpis(
    session_analysis,
    patient_id
):
    """
    Retourne les KPI d'un patient.
    """

    patient_data = session_analysis[
        session_analysis["patient_id"] == patient_id
    ]

    if patient_data.empty:
        return None

    return {
        "sessions": patient_data[
            "id_session"
        ].nunique(),

        "mean_score": patient_data[
            "score"
        ].mean(),

        "mean_success_rate": patient_data[
            "success_rate"
        ].mean(),

        "mean_duration": patient_data[
            "duration"
        ].mean(),

        "mean_repetitions": patient_data[
            "repetitions"
        ].mean(),

        "mean_progression": patient_data[
            "progression"
        ].mean()
    }


def get_last_session(
    session_analysis,
    patient_id
):
    """
    Retourne la dernière séance d'un patient.
    """

    patient_data = get_patient_history(
        session_analysis,
        patient_id
    )

    if patient_data.empty:
        return None

    return patient_data.iloc[-1]


def get_score_evolution(
    session_analysis,
    patient_id
):
    """
    Retourne l'évolution du score d'un patient.
    """

    history = get_patient_history(
        session_analysis,
        patient_id
    )

    return history[
        [
            "session_date",
            "score"
        ]
    ].copy()


def get_success_rate_evolution(
    session_analysis,
    patient_id
):
    """
    Retourne l'évolution du taux de réussite.
    """

    history = get_patient_history(
        session_analysis,
        patient_id
    )

    return history[
        [
            "session_date",
            "success_rate"
        ]
    ].copy()


def get_progression_evolution(
    session_analysis,
    patient_id
):
    """
    Retourne l'évolution de la progression.
    """

    history = get_patient_history(
        session_analysis,
        patient_id
    )

    return history[
        [
            "session_date",
            "progression"
        ]
    ].copy()