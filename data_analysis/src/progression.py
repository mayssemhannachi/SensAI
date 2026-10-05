import pandas as pd


def calculate_progression(
    session_analysis
):
    """
    Calcule la progression à partir
    du score de la séance précédente.
    """

    df = session_analysis.copy()

    df = df.sort_values(
        [
            "patient_id",
            "exercise_id",
            "session_date"
        ]
    )

    df["previous_score"] = (
        df
        .groupby(
            [
                "patient_id",
                "exercise_id"
            ]
        )["score"]
        .shift(1)
    )

    df["calculated_progression"] = (
        (
            df["score"]
            - df["previous_score"]
        )
        / df["previous_score"]
    ) * 100

    return df


def classify_progression(value):
    """
    Classe la progression d'une séance.
    """

    if pd.isna(value):
        return "Première séance"

    if value > 0:
        return "Amélioration"

    if value < 0:
        return "Diminution"

    return "Stable"


def add_progression_status(
    session_analysis
):
    """
    Ajoute le statut de progression.
    """

    df = session_analysis.copy()

    df["progression_status"] = (
        df["progression"]
        .apply(classify_progression)
    )

    return df


def calculate_patient_progression(
    session_analysis
):
    """
    Calcule la progression moyenne par patient.
    """

    return (
        session_analysis
        .groupby(
            [
                "patient_id",
                "first_name",
                "last_name"
            ]
        )
        .agg(
            mean_progression=(
                "progression",
                "mean"
            ),
            sessions=(
                "id_session",
                "nunique"
            )
        )
        .reset_index()
    )


def calculate_exercise_progression(
    session_analysis
):
    """
    Calcule la progression moyenne par exercice.
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
            mean_progression=(
                "progression",
                "mean"
            ),
            sessions=(
                "id_session",
                "nunique"
            )
        )
        .reset_index()
    )


def calculate_game_progression(
    session_analysis
):
    """
    Calcule la progression moyenne par jeu.
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
            mean_progression=(
                "progression",
                "mean"
            ),
            sessions=(
                "id_session",
                "nunique"
            )
        )
        .reset_index()
    )


def calculate_level_progression(
    session_analysis
):
    """
    Calcule la progression moyenne par niveau.
    """

    return (
        session_analysis
        .groupby(
            "level_number"
        )
        .agg(
            mean_progression=(
                "progression",
                "mean"
            ),
            sessions=(
                "id_session",
                "nunique"
            )
        )
        .reset_index()
    )