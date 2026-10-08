import pandas as pd


def calculate_global_kpis(session_analysis):
    """
    Calcule les KPI globaux.
    """

    df = session_analysis

    kpis = {
        "patients": df["patient_id"].nunique(),
        "sessions": df["id_session"].nunique(),
        "exercises": df["exercise_id"].nunique(),
        "games": df["game_id"].nunique(),

        "mean_score": df["score"].mean(),

        "mean_success_rate": (
            df["success_rate"].mean()
        ),

        "mean_duration": (
            df["duration"].mean()
        ),

        "mean_repetitions": (
            df["repetitions"].mean()
        ),

        "mean_progression": (
            df["progression"].mean()
        ),

        "sessions_improved": (
            (df["progression"] > 0).sum()
        ),

        "sessions_declined": (
            (df["progression"] < 0).sum()
        )
    }

    return kpis


def calculate_patient_kpis(session_analysis):
    """
    Calcule les KPI par patient.
    """

    patient_kpis = (
        session_analysis
        .groupby(
            [
                "patient_id",
                "first_name",
                "last_name"
            ]
        )
        .agg(
            sessions=(
                "id_session",
                "nunique"
            ),
            mean_score=(
                "score",
                "mean"
            ),
            mean_success_rate=(
                "success_rate",
                "mean"
            ),
            mean_duration=(
                "duration",
                "mean"
            ),
            mean_repetitions=(
                "repetitions",
                "mean"
            ),
            mean_progression=(
                "progression",
                "mean"
            )
        )
        .reset_index()
    )

    return patient_kpis


def calculate_exercise_kpis(session_analysis):
    """
    Calcule les KPI par exercice.
    """

    return (
        session_analysis
        .groupby(
            [
                "exercise_id",
                "name"
            ]
        )
        .agg(
            sessions=(
                "id_session",
                "nunique"
            ),
            mean_score=(
                "score",
                "mean"
            ),
            mean_success_rate=(
                "success_rate",
                "mean"
            ),
            mean_progression=(
                "progression",
                "mean"
            )
        )
        .reset_index()
    )


def calculate_game_kpis(session_analysis):
    """
    Calcule les KPI par jeu.
    """

    return (
        session_analysis
        .groupby(
            [
                "game_id",
                "name_game"
            ]
        )
        .agg(
            sessions=(
                "id_session",
                "nunique"
            ),
            mean_score=(
                "score",
                "mean"
            ),
            mean_success_rate=(
                "success_rate",
                "mean"
            ),
            mean_progression=(
                "progression",
                "mean"
            )
        )
        .reset_index()
    )


def calculate_level_kpis(session_analysis):
    """
    Calcule les KPI par niveau.
    """

    return (
        session_analysis
        .groupby(
            "level_number"
        )
        .agg(
            sessions=(
                "id_session",
                "nunique"
            ),
            mean_score=(
                "score",
                "mean"
            ),
            mean_success_rate=(
                "success_rate",
                "mean"
            ),
            mean_progression=(
                "progression",
                "mean"
            )
        )
        .reset_index()
    )