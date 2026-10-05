from pathlib import Path

import pandas as pd
import streamlit as st

from dashboard.utils.api_client import (
    ApiError,
    ApiPartialSuccessError,
    api_mode_enabled,
    get as api_get,
    post as api_post,
)


# ==========================================================
# PATHS
# ==========================================================

DATA_ANALYSIS_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = DATA_ANALYSIS_ROOT / "data"

RAW_DIR = DATA_DIR / "raw"

PROCESSED_DIR = DATA_DIR / "processed"


def _api_token():
    token = st.session_state.get("api_access_token")
    if not token:
        raise ApiError("Connectez-vous pour accéder aux données du backend.")
    return token


# ==========================================================
# GENERIC CSV LOADER
# ==========================================================

def load_csv(path):
    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


# ==========================================================
# SESSION ANALYSIS
# ==========================================================

def load_session_analysis():

    if api_mode_enabled():
        return _load_api_session_analysis()

    path = PROCESSED_DIR / "session_analysis.csv"

    if not path.exists():
        raise FileNotFoundError(
            f"""
            Le fichier session_analysis.csv est introuvable.

            Chemin attendu :
            {path}

            Exécute d'abord les notebooks 01 → 03.
            """
        )

    df = pd.read_csv(path)

    if "session_date" in df.columns:
        df["session_date"] = pd.to_datetime(
            df["session_date"],
            errors="coerce",
        )

    numeric_columns = [
        "score",
        "success_rate",
        "progression",
        "duration",
        "repetitions",
        "level_number",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    return df


def _load_api_session_analysis():
    """Adapt authorized backend sessions to the dashboard's analysis columns."""
    token = _api_token()
    patients = load_patients()
    games = load_games()
    games_by_id = {
        int(game["id"]): game
        for game in games.to_dict("records")
        if pd.notna(game.get("id"))
    }
    rows = []

    # The current backend exposes sessions per patient-game association.
    for patient in patients.to_dict("records"):
        patient_id = patient.get("id")
        if pd.isna(patient_id):
            continue

        patient_games = api_get(
            f"/patient-games/patient/{int(patient_id)}",
            token,
        )
        for patient_game in patient_games:
            patient_game_id = int(patient_game["id"])
            game_id = int(patient_game["game_id"])
            game = games_by_id.get(game_id, {})
            sessions = api_get(
                f"/sessions/patient-game/{patient_game_id}",
                token,
            )

            for session in sessions:
                metrics = session.get("metrics") or {}
                if not isinstance(metrics, dict):
                    metrics = {}

                rows.append(
                    {
                        "id_session": session.get("id"),
                        "patient_game_id": patient_game_id,
                        "patient_id": int(patient_id),
                        "id_patient": int(patient_id),
                        "first_name": patient.get("first_name", ""),
                        "last_name": patient.get("last_name", ""),
                        "date_of_birth": patient.get("date_of_birth", pd.NaT),
                        "age": patient.get("age"),
                        "game_id": game_id,
                        "id_game": game_id,
                        "name_game": game.get("name", f"Jeu {game_id}"),
                        "exercise_id": _metric(metrics, "exercise_id"),
                        "name": _metric(metrics, "exercise_name", "name_exercise"),
                        "level_number": _metric(metrics, "level_number", "level"),
                        "session_date": session.get("created_at"),
                        "duration": _seconds_to_minutes(session.get("duration_sec")),
                        "score": _metric(metrics, "score"),
                        "repetitions": _metric(metrics, "repetitions", "reps"),
                        "success_rate": _metric(metrics, "success_rate", "successRate", "accuracy"),
                        "progression": _metric(metrics, "progression"),
                    }
                )

    columns = [
        "id_session", "patient_game_id", "patient_id", "id_patient",
        "first_name", "last_name", "date_of_birth", "age", "game_id",
        "id_game", "name_game", "exercise_id", "name", "level_number",
        "session_date", "duration", "score", "repetitions", "success_rate",
        "progression",
    ]
    df = pd.DataFrame(rows, columns=columns)
    if "session_date" in df:
        df["session_date"] = pd.to_datetime(df["session_date"], errors="coerce")
    for column in [
        "score", "success_rate", "progression", "duration", "repetitions",
        "level_number", "exercise_id", "id_session", "patient_id", "game_id",
    ]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def _metric(metrics, *names):
    for name in names:
        value = metrics.get(name)
        if value is not None:
            return value
    return None


def _seconds_to_minutes(value):
    number = pd.to_numeric(value, errors="coerce")
    return number / 60 if pd.notna(number) else None


# ==========================================================
# PATIENTS
# ==========================================================

def load_patients():

    if api_mode_enabled():
        patients = api_get("/patients/", _api_token())
        df = pd.DataFrame(patients)
        if "date_of_birth" not in df:
            df["date_of_birth"] = pd.NaT
        if "user_id" not in df:
            df["user_id"] = None
        return df

    path = RAW_DIR / "patients.csv"

    df = load_csv(path)

    if "date_of_birth" in df.columns:
        df["date_of_birth"] = pd.to_datetime(
            df["date_of_birth"],
            errors="coerce",
        )

    return df


# ==========================================================
# CONSULTATIONS
# ==========================================================

def load_consultations():

    if api_mode_enabled():
        # The backend currently supports creating consultations but not listing
        # them. Do not silently read the demo CSV in API mode.
        return pd.DataFrame(
            columns=["id", "patient_id", "therapist_id", "consultation_date", "diagnosis"]
        )

    path = RAW_DIR / "consultations.csv"

    df = load_csv(path)

    if "consultation_date" in df.columns:
        df["consultation_date"] = pd.to_datetime(
            df["consultation_date"],
            errors="coerce",
        )

    return df


def save_patient_diagnosis(patient_id, diagnosis, therapist_id=None):
    diagnosis = diagnosis.strip()
    if not diagnosis:
        raise ValueError("Le diagnostic ne peut pas être vide.")

    if api_mode_enabled():
        result = api_post(
            "/consultations/",
            _api_token(),
            {
                "patient_id": int(patient_id),
                "consultation_date": pd.Timestamp.today().date().isoformat(),
                "diagnosis": diagnosis,
            },
        )
        return result.get("id")

    consultations_path = RAW_DIR / "consultations.csv"
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if consultations_path.exists():
        consultations = pd.read_csv(consultations_path)
    else:
        consultations = pd.DataFrame(
            columns=[
                "id",
                "patient_id",
                "therapist_id",
                "consultation_date",
                "diagnosis",
            ]
        )

    for column in [
        "id",
        "patient_id",
        "therapist_id",
        "consultation_date",
        "diagnosis",
    ]:
        if column not in consultations.columns:
            consultations[column] = None

    numeric_ids = pd.to_numeric(consultations["id"], errors="coerce")
    next_id = int(numeric_ids.max()) + 1 if numeric_ids.notna().any() else 1

    consultations = pd.concat(
        [
            consultations,
            pd.DataFrame(
                [
                    {
                        "id": next_id,
                        "patient_id": patient_id,
                        "therapist_id": therapist_id,
                        "consultation_date": pd.Timestamp.today().normalize(),
                        "diagnosis": diagnosis,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )
    consultations.to_csv(consultations_path, index=False)

    return next_id


# ==========================================================
# GAMES
# ==========================================================

def load_games():
    if api_mode_enabled():
        return pd.DataFrame(api_get("/games/", _api_token()))
    return load_csv(RAW_DIR / "games.csv")


# ==========================================================
# SAVE PATIENT
# ==========================================================

def save_patient(
    first_name,
    last_name,
    date_of_birth=None,
    patient_code=None,
    diagnosis="",
    therapist_id=None,
    age=None,
):
    if api_mode_enabled():
        if age is None:
            raise ValueError(
                "Le backend attend l’âge du patient. Demandez un âge au lieu d’une date de naissance."
            )
        patient = api_post(
            "/patients/",
            _api_token(),
            {
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "age": int(age),
            },
        )
        if diagnosis and diagnosis.strip():
            try:
                save_patient_diagnosis(patient["id"], diagnosis)
            except (ApiError, ValueError) as exc:
                raise ApiPartialSuccessError(
                    patient,
                    f"Patient créé, mais le diagnostic n’a pas été enregistré : {exc}",
                    status_code=exc.status_code,
                ) from exc
        return patient

    patients_path = RAW_DIR / "patients.csv"

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if patients_path.exists():
        patients = pd.read_csv(patients_path)
    else:
        patients = pd.DataFrame(
            columns=[
                "id",
                "user_id",
                "first_name",
                "last_name",
                "date_of_birth",
                "patient_code",
                "therapist_id",
                "created_at",
            ]
        )

    # --------------------------------------
    # Generate ID
    # --------------------------------------

    if "id" in patients.columns and not patients.empty:
        numeric_ids = pd.to_numeric(
            patients["id"],
            errors="coerce",
        )

        next_id = (
            int(numeric_ids.max()) + 1
            if numeric_ids.notna().any()
            else 1
        )
    else:
        next_id = 1

    # --------------------------------------
    # Check patient code
    # --------------------------------------

    if (
        "patient_code" in patients.columns
        and patient_code
        and patient_code in patients["patient_code"].astype(str).values
    ):
        raise ValueError(
            "Ce code patient existe déjà."
        )

    # --------------------------------------
    # Build row
    # --------------------------------------

    new_patient = {
        "id": next_id,
        "user_id": None,
        "first_name": first_name.strip(),
        "last_name": last_name.strip(),
        "date_of_birth": date_of_birth,
        "patient_code": patient_code.strip(),
        "therapist_id": therapist_id,
        "created_at": pd.Timestamp.now(),
    }

    # Add missing columns if necessary

    for column in new_patient:
        if column not in patients.columns:
            patients[column] = None

    patients = pd.concat(
        [
            patients,
            pd.DataFrame([new_patient]),
        ],
        ignore_index=True,
    )

    patients.to_csv(
        patients_path,
        index=False,
    )

    # --------------------------------------
    # Save consultation if diagnosis exists
    # --------------------------------------

    if diagnosis.strip():

        consultations_path = RAW_DIR / "consultations.csv"

        if consultations_path.exists():
            consultations = pd.read_csv(
                consultations_path
            )
        else:
            consultations = pd.DataFrame(
                columns=[
                    "id",
                    "patient_id",
                    "therapist_id",
                    "consultation_date",
                    "diagnosis",
                ]
            )

        if "id" in consultations.columns and not consultations.empty:

            ids = pd.to_numeric(
                consultations["id"],
                errors="coerce",
            )

            next_consultation_id = (
                int(ids.max()) + 1
                if ids.notna().any()
                else 1
            )

        else:
            next_consultation_id = 1

        consultation = {
            "id": next_consultation_id,
            "patient_id": next_id,
            "therapist_id": therapist_id,
            "consultation_date": pd.Timestamp.today().date(),
            "diagnosis": diagnosis.strip(),
        }

        for column in consultation:
            if column not in consultations.columns:
                consultations[column] = None

        consultations = pd.concat(
            [
                consultations,
                pd.DataFrame([consultation]),
            ],
            ignore_index=True,
        )

        consultations.to_csv(
            consultations_path,
            index=False,
        )

    return next_id


# ==========================================================
# HELPERS
# ==========================================================

def safe_round(value, decimals=2):

    if pd.isna(value):
        return None

    return round(
        float(value),
        decimals,
    )


def format_percentage(value):

    if pd.isna(value):
        return "—"

    return f"{float(value):.1f}%"


def get_initials(first_name, last_name):

    first = str(first_name).strip()
    last = str(last_name).strip()

    initials = ""

    if first:
        initials += first[0].upper()

    if last:
        initials += last[0].upper()

    return initials or "KK"