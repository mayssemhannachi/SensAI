"""Couche d'accès aux données du dashboard thérapeute.

Deux sources interchangeables, qui produisent EXACTEMENT le même format :

* ``demo`` : données synthétiques (CSV du dossier ``data/``), aucune dépendance ;
* ``api``  : backend FastAPI KineKids AI (jeton Bearer obtenu à la connexion).

Les pages ne manipulent que le format normalisé décrit ci-dessous, elles ne
savent pas d'où viennent les données.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import streamlit as st

from dashboard.utils import state
from dashboard.utils.api_client import (
    ApiError,
    ApiPartialSuccessError,
    api_base_url,
    get as api_get,
    post as api_post,
    put as api_put,
)

# ==========================================================
# CHEMINS & SCHÉMA NORMALISÉ
# ==========================================================

DATA_ANALYSIS_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = DATA_ANALYSIS_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

PATIENT_COLUMNS = [
    "id", "first_name", "last_name", "full_name", "age", "patient_code",
    "therapist_id", "created_at", "diagnosis",
]

SESSION_COLUMNS = [
    "session_id", "patient_id", "patient_game_id", "game_id", "game_name",
    "body_part", "exercise_name", "level", "session_date", "duration_min",
    "score", "success_rate", "repetitions", "progression",
    "first_name", "last_name", "patient_name",
]

GAME_COLUMNS = ["id", "name", "body_part", "description"]

PATIENT_GAME_COLUMNS = ["patient_game_id", "patient_id", "game_id", "game_name", "configuration"]

# Réglages d'un jeu assigné (même vocabulaire que le frontend et les jeux).
GAME_SETTINGS_DEFAULTS = {
    "target_angle": 30,      # degrés
    "hold_seconds": 3,       # secondes de maintien
    "repetitions": 6,        # répétitions par séance
    "speed": "lente",        # lente | moderee | rapide
    "difficulty": "moyenne", # faible | moyenne | elevee
    "safety_limit": 35,      # degrés à ne pas dépasser
    "active": True,
}

NUMERIC_SESSION_COLUMNS = [
    "session_id", "patient_id", "patient_game_id", "game_id", "level",
    "duration_min", "score", "success_rate", "repetitions", "progression",
]

API_CACHE_TTL = 120  # secondes


@dataclass
class Dataset:
    """Toutes les données nécessaires aux pages, déjà normalisées."""

    source: str
    patients: pd.DataFrame
    sessions: pd.DataFrame
    games: pd.DataFrame
    patient_games: pd.DataFrame = field(
        default_factory=lambda: pd.DataFrame(columns=PATIENT_GAME_COLUMNS)
    )
    reference_date: pd.Timestamp = field(default_factory=pd.Timestamp.now)
    diagnosis_readable: bool = True

    @property
    def is_demo(self) -> bool:
        return self.source == "demo"

    def patient(self, patient_id) -> pd.Series | None:
        match = self.patients[self.patients["id"] == patient_id]
        return None if match.empty else match.iloc[0]

    def sessions_of(self, patient_id) -> pd.DataFrame:
        return (
            self.sessions[self.sessions["patient_id"] == patient_id]
            .sort_values("session_date")
            .reset_index(drop=True)
        )


# ==========================================================
# OUTILS DE NORMALISATION (purs, testables)
# ==========================================================

def _empty(columns) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def age_from_birth_date(birth_dates: pd.Series, reference: pd.Timestamp) -> pd.Series:
    birth = pd.to_datetime(birth_dates, errors="coerce")
    years = reference.year - birth.dt.year
    before_birthday = (birth.dt.month > reference.month) | (
        (birth.dt.month == reference.month) & (birth.dt.day > reference.day)
    )
    return (years - before_birthday.astype("Int64")).astype("Int64")


def normalize_patients(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy() if df is not None else pd.DataFrame()
    for column in PATIENT_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA
    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df = df.dropna(subset=["id"]).copy()
    df["id"] = df["id"].astype(int)
    for column in ["first_name", "last_name", "patient_code"]:
        df[column] = df[column].fillna("").astype(str).str.strip()
    df["full_name"] = (df["first_name"] + " " + df["last_name"]).str.strip()
    df["age"] = pd.to_numeric(df["age"], errors="coerce").astype("Int64")
    df["therapist_id"] = pd.to_numeric(df["therapist_id"], errors="coerce").astype("Int64")
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["diagnosis"] = df["diagnosis"].astype("object").where(df["diagnosis"].notna(), "")
    df["diagnosis"] = df["diagnosis"].astype(str).str.strip()
    return df[PATIENT_COLUMNS].sort_values(["last_name", "first_name"]).reset_index(drop=True)


def derive_progression(sessions: pd.DataFrame) -> pd.Series:
    """Variation du score (%) par rapport à la séance précédente du même exercice.

    Utilisée uniquement pour compléter une progression absente des métriques.
    """
    if sessions.empty:
        return pd.Series(dtype=float)
    ordered = sessions.assign(
        _exercise=sessions["exercise_name"].astype("object").fillna("").astype(str)
    ).sort_values("session_date", kind="stable")
    previous = ordered.groupby(
        ["patient_id", "game_id", "_exercise"], dropna=False
    )["score"].shift(1)
    change = (ordered["score"] - previous) / previous.abs() * 100
    change = change.where(previous.notna() & (previous != 0))
    return change.reindex(sessions.index).round(2)


def normalize_sessions(df: pd.DataFrame, patients: pd.DataFrame | None = None,
                       fill_progression: bool = False) -> pd.DataFrame:
    df = df.copy() if df is not None else pd.DataFrame()
    for column in SESSION_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA
    for column in NUMERIC_SESSION_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df["session_date"] = pd.to_datetime(df["session_date"], errors="coerce", utc=True)
    df["session_date"] = df["session_date"].dt.tz_localize(None)
    df = df.dropna(subset=["patient_id"]).copy()

    # Taux de réussite exprimé en ratio 0-1 → pourcentage 0-100.
    success = df["success_rate"]
    if success.notna().any() and success.max() <= 1:
        df["success_rate"] = success * 100

    df["game_name"] = df["game_name"].astype("object").where(df["game_name"].notna(), None)
    missing_game = df["game_name"].isna()
    df.loc[missing_game, "game_name"] = "Jeu " + df.loc[missing_game, "game_id"].astype("Int64").astype(str)

    if fill_progression:
        df["progression"] = df["progression"].fillna(derive_progression(df))

    if patients is not None and not patients.empty:
        names = patients.set_index("id")[["first_name", "last_name", "full_name"]]
        df["first_name"] = df["patient_id"].map(names["first_name"]).fillna(df["first_name"])
        df["last_name"] = df["patient_id"].map(names["last_name"]).fillna(df["last_name"])
    df["first_name"] = df["first_name"].fillna("").astype(str)
    df["last_name"] = df["last_name"].fillna("").astype(str)
    df["patient_name"] = (df["first_name"] + " " + df["last_name"]).str.strip()

    return df[SESSION_COLUMNS].sort_values("session_date").reset_index(drop=True)


def _metric(metrics: dict, *names):
    for name in names:
        value = metrics.get(name)
        if value is not None and value != "":
            return value
    return None


def api_session_to_row(session: dict, patient_id: int, patient_game_id: int,
                       game: dict) -> dict:
    """Transforme une session API (``metrics`` JSON libre) en ligne normalisée."""
    metrics = session.get("metrics") or {}
    if not isinstance(metrics, dict):
        metrics = {}
    duration_sec = pd.to_numeric(
        _metric({"d": session.get("duration_sec")}, "d"), errors="coerce"
    )
    # Le jeu peut fournir la date réelle de la séance ; sinon date d'enregistrement.
    played_at = _metric(metrics, "played_at", "session_date", "date")
    return {
        "session_id": session.get("id"),
        "patient_id": patient_id,
        "patient_game_id": patient_game_id,
        "game_id": game.get("id"),
        "game_name": game.get("name"),
        "body_part": _metric(metrics, "body_part") or game.get("body_part"),
        "exercise_name": _metric(metrics, "exercise_name", "name_exercise", "exercise"),
        "level": _metric(metrics, "level_number", "level"),
        "session_date": played_at or session.get("created_at"),
        "duration_min": duration_sec / 60 if pd.notna(duration_sec) else None,
        "score": _metric(metrics, "score"),
        "success_rate": _metric(metrics, "success_rate", "successRate", "accuracy"),
        "repetitions": _metric(metrics, "repetitions", "reps"),
        "progression": _metric(metrics, "progression"),
    }


# ==========================================================
# SOURCE DÉMO (CSV synthétiques)
# ==========================================================

@st.cache_data(show_spinner=False)
def _read_demo_files() -> dict:
    sessions = _read_csv(PROCESSED_DIR / "session_analysis.csv")
    patients = _read_csv(RAW_DIR / "patients.csv")
    games = _read_csv(RAW_DIR / "games.csv")
    consultations = _read_csv(RAW_DIR / "consultations.csv")
    return {
        "sessions": sessions,
        "patients": patients,
        "games": games,
        "consultations": consultations,
    }


def _latest_diagnoses(consultations: pd.DataFrame) -> dict:
    if consultations.empty or not {"patient_id", "diagnosis"} <= set(consultations.columns):
        return {}
    consultations = consultations.copy()
    if "consultation_date" in consultations.columns:
        consultations["consultation_date"] = pd.to_datetime(
            consultations["consultation_date"], errors="coerce"
        )
        consultations = consultations.sort_values("consultation_date")
    consultations = consultations.dropna(subset=["diagnosis"])
    latest = consultations.groupby("patient_id")["diagnosis"].last()
    return {int(k): str(v) for k, v in latest.items()}


def _demo_store() -> dict:
    """Modifications faites pendant la démo (en mémoire, rien n'est écrit sur disque)."""
    return st.session_state.setdefault(
        "demo_store", {"patients": [], "diagnoses": {}}
    )


def load_demo_dataset() -> Dataset:
    files = _read_demo_files()
    raw_sessions = files["sessions"].drop(columns=["session_id"], errors="ignore").rename(
        columns={
            "id_session": "session_id",
            "name_game": "game_name",
            "name": "exercise_name",
            "level_number": "level",
            "duration": "duration_min",
        }
    )
    sessions_dates = pd.to_datetime(raw_sessions.get("session_date"), errors="coerce")
    reference = (
        sessions_dates.max().normalize() if sessions_dates is not None and sessions_dates.notna().any()
        else pd.Timestamp.now().normalize()
    )

    patients = files["patients"].copy()
    store = _demo_store()
    if store["patients"]:
        patients = pd.concat([patients, pd.DataFrame(store["patients"])], ignore_index=True)
    if "date_of_birth" in patients.columns:
        computed = age_from_birth_date(patients["date_of_birth"], reference)
        patients["age"] = (
            pd.to_numeric(patients["age"], errors="coerce").astype("Int64").fillna(computed)
            if "age" in patients.columns else computed
        )
    diagnoses = _latest_diagnoses(files["consultations"])
    diagnoses.update(store["diagnoses"])
    patients["diagnosis"] = patients["id"].map(diagnoses)
    patients = normalize_patients(patients)

    games = files["games"].copy()
    for column in GAME_COLUMNS:
        if column not in games.columns:
            games[column] = pd.NA

    sessions = normalize_sessions(raw_sessions, patients)
    patient_games = (
        sessions[["patient_id", "game_id", "game_name"]]
        .drop_duplicates()
        .assign(patient_game_id=pd.NA, configuration=None)[PATIENT_GAME_COLUMNS]
    )
    return Dataset(
        source="demo",
        patients=patients,
        sessions=sessions,
        games=games[GAME_COLUMNS],
        patient_games=patient_games,
        reference_date=reference,
        diagnosis_readable=True,
    )


# ==========================================================
# SOURCE BACKEND (FastAPI)
# ==========================================================

def _require_token() -> str:
    token = state.get_token()
    if not token:
        raise ApiError("Connectez-vous pour accéder aux données du backend.", 401)
    return token


def fetch_api_payload(token: str) -> dict:
    """Récupère patients, jeux, associations et séances accessibles au thérapeute.

    Le backend expose les séances par association patient-jeu : on parcourt donc
    patients → jeux associés → séances (appels parallélisés).
    """
    patients = api_get("/patients/", token) or []
    games = api_get("/games/", token) or []
    games_by_id = {int(g["id"]): g for g in games if g.get("id") is not None}

    def patient_games_of(patient: dict) -> list[dict]:
        return api_get(f"/patient-games/patient/{int(patient['id'])}", token) or []

    with ThreadPoolExecutor(max_workers=8) as pool:
        associations_per_patient = list(pool.map(patient_games_of, patients))

    associations = [pg for group in associations_per_patient for pg in group]

    def sessions_of(pg: dict) -> list[dict]:
        return api_get(f"/sessions/patient-game/{int(pg['id'])}", token) or []

    with ThreadPoolExecutor(max_workers=8) as pool:
        sessions_per_association = list(pool.map(sessions_of, associations))

    session_rows, pg_rows = [], []
    for pg, sessions in zip(associations, sessions_per_association):
        game = games_by_id.get(int(pg["game_id"]), {"id": pg["game_id"]})
        pg_rows.append({
            "patient_game_id": pg["id"],
            "patient_id": pg["patient_id"],
            "game_id": pg["game_id"],
            "game_name": game.get("name") or f"Jeu {pg['game_id']}",
            "configuration": pg.get("configuration") or {},
        })
        for session in sessions:
            session_rows.append(
                api_session_to_row(session, int(pg["patient_id"]), int(pg["id"]), game)
            )

    # Diagnostic : dernière consultation de chaque patient (route récente du backend).
    def latest_diagnosis(patient: dict):
        try:
            consultations = api_get(f"/consultations/patient/{int(patient['id'])}", token) or []
        except ApiError as error:
            if error.status_code in {404, 405}:
                return None  # route absente sur cette version du backend
            raise
        for consultation in consultations:
            if consultation.get("diagnosis"):
                return consultation["diagnosis"]
        return ""

    with ThreadPoolExecutor(max_workers=8) as pool:
        diagnoses_list = list(pool.map(latest_diagnosis, patients))
    readable = bool(patients) and all(d is not None for d in diagnoses_list)
    diagnoses = {int(p["id"]): d for p, d in zip(patients, diagnoses_list) if d}

    return {
        "patients": patients,
        "games": games,
        "patient_games": pg_rows,
        "sessions": session_rows,
        "diagnoses": diagnoses,
        "diagnosis_readable": readable,
    }


@st.cache_data(ttl=API_CACHE_TTL, show_spinner=False)
def _cached_api_payload(token: str, base_url: str) -> dict:  # base_url = clé de cache
    return fetch_api_payload(token)


def build_api_dataset(payload: dict, diagnoses: dict | None = None) -> Dataset:
    patients = pd.DataFrame(payload.get("patients") or [])
    merged = {**(payload.get("diagnoses") or {}), **(diagnoses or {})}
    if not patients.empty:
        patients["diagnosis"] = patients["id"].map(merged)
    patients = normalize_patients(patients)

    games = pd.DataFrame(payload.get("games") or [], columns=None)
    for column in GAME_COLUMNS:
        if column not in games.columns:
            games[column] = pd.NA

    sessions = normalize_sessions(
        pd.DataFrame(payload.get("sessions") or []), patients, fill_progression=True
    )
    patient_games = pd.DataFrame(payload.get("patient_games") or [], columns=PATIENT_GAME_COLUMNS)

    return Dataset(
        source="api",
        patients=patients,
        sessions=sessions,
        games=games[GAME_COLUMNS],
        patient_games=patient_games,
        reference_date=pd.Timestamp.now().normalize(),
        diagnosis_readable=bool(payload.get("diagnosis_readable")),
    )


def _session_diagnoses() -> dict:
    """Diagnostics envoyés au backend pendant cette session (non relisibles via l'API)."""
    return st.session_state.setdefault("api_saved_diagnoses", {})


def load_api_dataset() -> Dataset:
    payload = _cached_api_payload(_require_token(), api_base_url())
    return build_api_dataset(payload, _session_diagnoses())


# ==========================================================
# POINT D'ENTRÉE UNIQUE
# ==========================================================

def load_dataset() -> Dataset:
    if state.api_mode_enabled():
        return load_api_dataset()
    return load_demo_dataset()


def refresh_data() -> None:
    st.cache_data.clear()


# ==========================================================
# ÉCRITURES
# ==========================================================

def save_patient(first_name: str, last_name: str, age: int | None = None,
                 diagnosis: str = "") -> dict:
    first_name, last_name = first_name.strip(), last_name.strip()
    diagnosis = (diagnosis or "").strip()
    if not first_name or not last_name:
        raise ValueError("Le prénom et le nom sont obligatoires.")
    if age is None:
        raise ValueError("L’âge du patient est obligatoire.")

    if state.api_mode_enabled():
        patient = api_post(
            "/patients/",
            _require_token(),
            {"first_name": first_name, "last_name": last_name, "age": int(age)},
        )
        if diagnosis:
            try:
                save_patient_diagnosis(patient["id"], diagnosis)
            except (ApiError, ValueError) as exc:
                raise ApiPartialSuccessError(
                    patient,
                    f"Patient créé, mais le diagnostic n’a pas été enregistré : {exc}",
                    status_code=getattr(exc, "status_code", None),
                ) from exc
        refresh_data()
        return patient

    dataset = load_demo_dataset()
    next_id = int(dataset.patients["id"].max()) + 1 if not dataset.patients.empty else 1
    patient = {
        "id": next_id,
        "first_name": first_name,
        "last_name": last_name,
        "age": int(age),
        "patient_code": f"KK-DEMO-{next_id:03d}",
        "therapist_id": pd.NA,
        "created_at": pd.Timestamp.now(),
    }
    store = _demo_store()
    store["patients"].append(patient)
    if diagnosis:
        store["diagnoses"][next_id] = diagnosis
    return patient


def save_patient_diagnosis(patient_id: int, diagnosis: str) -> None:
    diagnosis = (diagnosis or "").strip()
    if not diagnosis:
        raise ValueError("Le diagnostic ne peut pas être vide.")
    if state.api_mode_enabled():
        api_post(
            "/consultations/",
            _require_token(),
            {
                "patient_id": int(patient_id),
                "consultation_date": pd.Timestamp.today().date().isoformat(),
                "diagnosis": diagnosis,
            },
        )
        _session_diagnoses()[int(patient_id)] = diagnosis
        refresh_data()
        return
    _demo_store()["diagnoses"][int(patient_id)] = diagnosis


def assign_game(patient_id: int, game_id: int, configuration: dict | None = None) -> dict:
    """Associe un jeu à un patient avec ses réglages (backend uniquement)."""
    if not state.api_mode_enabled():
        raise ValueError("L’association de jeux est disponible en mode Backend.")
    result = api_post(
        "/patient-games/",
        _require_token(),
        {"patient_id": int(patient_id), "game_id": int(game_id),
         "configuration": configuration if configuration is not None else dict(GAME_SETTINGS_DEFAULTS)},
    )
    refresh_data()
    return result


def update_game_settings(patient_game_id: int, configuration: dict) -> dict:
    """Modifie les réglages d'un jeu assigné (backend uniquement)."""
    if not state.api_mode_enabled():
        raise ValueError("La modification des réglages est disponible en mode Backend.")
    result = api_put(f"/patient-games/{int(patient_game_id)}", _require_token(),
                     {"configuration": configuration})
    refresh_data()
    return result


def create_activation_code(patient_id: int) -> dict:
    """Génère le code à 6 caractères que le patient saisit sur le site pour créer son compte."""
    if not state.api_mode_enabled():
        raise ValueError("Les codes d’activation sont disponibles en mode Backend.")
    return api_post("/activation-codes/", _require_token(), {"patient_id": int(patient_id)})
