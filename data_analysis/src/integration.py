import pandas as pd


def create_exercise_analysis(
    exercises,
    games
):
    """
    Crée le dataset analytique des exercices.

    Relation :
    exercises -> games
    """

    exercise_analysis = exercises.merge(
        games[
            [
                "id",
                "name",
                "body_part",
                "description"
            ]
        ],
        left_on="game_id",
        right_on="id",
        how="left",
        suffixes=(
            "_exercise",
            "_game"
        )
    )

    return exercise_analysis


def create_patient_exercise_analysis(
    patients,
    patient_exercises,
    exercises,
    games,
    exercise_levels
):
    """
    Crée le dataset analytique des exercices
    attribués aux patients.
    """

    result = patient_exercises.merge(
        patients,
        left_on="patient_id",
        right_on="id",
        how="left",
        suffixes=(
            "_assignment",
            "_patient"
        )
    )

    result = result.merge(
        exercises,
        left_on="exercise_id",
        right_on="id",
        how="left",
        suffixes=(
            "",
            "_exercise"
        )
    )

    result = result.merge(
        games[
            [
                "id",
                "name",
                "body_part",
                "description"
            ]
        ],
        left_on="game_id",
        right_on="id",
        how="left",
        suffixes=(
            "",
            "_game"
        )
    )

    result = result.merge(
        exercise_levels,
        left_on="current_level_id",
        right_on="id",
        how="left",
        suffixes=(
            "",
            "_level"
        )
    )

    return result


def create_session_analysis(
    patient_exercise_analysis,
    sessions,
    results
):
    """
    Crée le dataset analytique final des sessions.
    """

    result = patient_exercise_analysis.merge(
        sessions,
        left_on="id",
        right_on="patient_exercise_id",
        how="inner",
        suffixes=(
            "_assignment",
            "_session"
        )
    )

    result = result.merge(
        results[
            [
                "session_id",
                "repetitions",
                "success_rate",
                "progression"
            ]
        ],
        left_on="id_session",
        right_on="session_id",
        how="left"
    )

    return result