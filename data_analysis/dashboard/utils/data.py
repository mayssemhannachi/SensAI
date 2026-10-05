from pathlib import Path

import pandas as pd


# ==========================================================
# PATHS
# ==========================================================

DATA_ANALYSIS_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = DATA_ANALYSIS_ROOT / "data"

RAW_DIR = DATA_DIR / "raw"

PROCESSED_DIR = DATA_DIR / "processed"


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


# ==========================================================
# PATIENTS
# ==========================================================

def load_patients():

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
    return load_csv(RAW_DIR / "games.csv")


# ==========================================================
# SAVE PATIENT
# ==========================================================

def save_patient(
    first_name,
    last_name,
    date_of_birth,
    patient_code,
    diagnosis="",
    therapist_id=None,
):
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