"""Peuple le backend KineKids AI avec les données de démonstration (via l'API).

Le script n'accède jamais à la base de données : il utilise uniquement les routes
publiques de l'API FastAPI, exactement comme le feraient les jeux.

Exemple (depuis le dossier ``data_analysis``) :

    python scripts/seed_backend.py --email demo@kinekids.tn --password demo1234 --register

Options utiles :
    --api-url http://127.0.0.1:8000   URL du backend
    --register                         crée le compte thérapeute s'il n'existe pas
    --limit-patients 8                 ne crée qu'une partie des patients

Le script est idempotent pour les patients : un patient déjà présent (même prénom
et même nom pour ce thérapeute) est ignoré avec ses séances.

Note : les séances portent leur date réelle dans ``metrics.played_at``, car
l'API fixe ``created_at`` à la date d'enregistrement. Le dashboard lit
``played_at`` en priorité.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"


class Api:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.http = requests.Session()
        self.token = None

    def call(self, method: str, path: str, payload=None, auth=True):
        headers = {"Authorization": f"Bearer {self.token}"} if auth and self.token else {}
        response = self.http.request(method, self.base_url + path, json=payload,
                                     headers=headers, timeout=20)
        if not response.ok:
            raise RuntimeError(f"{method} {path} → {response.status_code} : {response.text[:300]}")
        return response.json() if response.content else None


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--full-name", default="Thérapeute Démo")
    parser.add_argument("--register", action="store_true", help="créer le compte s'il n'existe pas")
    parser.add_argument("--limit-patients", type=int, default=None)
    args = parser.parse_args()

    api = Api(args.api_url)
    try:
        api.call("GET", "/health", auth=False)
    except Exception as exc:  # noqa: BLE001
        print(f"✗ Backend injoignable à {args.api_url} : {exc}")
        return 1

    # 1. Authentification -------------------------------------------------
    credentials = {"email": args.email, "password": args.password}
    try:
        api.token = api.call("POST", "/auth/login", credentials, auth=False)["access_token"]
    except RuntimeError:
        if not args.register:
            print("✗ Connexion refusée. Ajoutez --register pour créer le compte.")
            return 1
        api.call("POST", "/auth/register", {"full_name": args.full_name, **credentials}, auth=False)
        api.token = api.call("POST", "/auth/login", credentials, auth=False)["access_token"]
        print(f"✓ Compte créé : {args.email}")
    print(f"✓ Connecté en tant que {args.email}")

    # 2. Données de démonstration ----------------------------------------
    patients = pd.read_csv(RAW / "patients.csv")
    games = pd.read_csv(RAW / "games.csv")
    sessions = pd.read_csv(PROCESSED / "session_analysis.csv")
    consultations_path = RAW / "consultations.csv"
    consultations = pd.read_csv(consultations_path) if consultations_path.exists() else pd.DataFrame()
    reference = pd.to_datetime(sessions["session_date"]).max()
    if args.limit_patients:
        patients = patients.head(args.limit_patients)

    # 3. Catalogue de jeux -----------------------------------------------
    existing_games = {g["name"]: g for g in api.call("GET", "/games/")}
    game_ids = {}
    for game in games.itertuples(index=False):
        if game.name not in existing_games:
            created = api.call("POST", "/games/", {
                "name": game.name, "slug": slugify(game.name), "description": game.description,
            })
            existing_games[game.name] = created
            print(f"  + jeu « {game.name} »")
        game_ids[int(game.id)] = int(existing_games[game.name]["id"])

    # 4. Patients, diagnostics, jeux assignés, séances -------------------
    existing_patients = {
        (p["first_name"].lower(), p["last_name"].lower()) for p in api.call("GET", "/patients/")
    }
    created_patients = created_sessions = 0
    for patient in patients.itertuples(index=False):
        key = (patient.first_name.lower(), patient.last_name.lower())
        if key in existing_patients:
            print(f"  = {patient.first_name} {patient.last_name} existe déjà, ignoré")
            continue
        birth = pd.Timestamp(patient.date_of_birth)
        age = reference.year - birth.year - ((reference.month, reference.day) < (birth.month, birth.day))
        created = api.call("POST", "/patients/", {
            "first_name": patient.first_name, "last_name": patient.last_name, "age": int(age),
        })
        created_patients += 1

        if not consultations.empty:
            for row in consultations[consultations["patient_id"] == patient.id].itertuples(index=False):
                api.call("POST", "/consultations/", {
                    "patient_id": created["id"],
                    "consultation_date": str(pd.Timestamp(row.consultation_date).date()),
                    "diagnosis": row.diagnosis,
                })

        history = sessions[sessions["patient_id"] == patient.id].sort_values("session_date")
        patient_game_ids = {}
        for demo_game_id in history["game_id"].unique():
            association = api.call("POST", "/patient-games/", {
                "patient_id": created["id"],
                "game_id": game_ids[int(demo_game_id)],
                "configuration": {"source": "demo-seed"},
            })
            patient_game_ids[int(demo_game_id)] = association["id"]

        for session in history.itertuples(index=False):
            metrics = {
                "score": float(session.score),
                "success_rate": float(session.success_rate),
                "repetitions": int(session.repetitions),
                "level_number": int(session.level_number),
                "exercise_name": session.name,
                "played_at": pd.Timestamp(session.session_date).isoformat(),
            }
            if pd.notna(session.progression):
                metrics["progression"] = float(session.progression)
            api.call("POST", "/sessions/", {
                "patient_game_id": patient_game_ids[int(session.game_id)],
                "duration_sec": int(session.duration * 60),
                "metrics": metrics,
            })
            created_sessions += 1
        print(f"  + {patient.first_name} {patient.last_name} ({created['patient_code']}) "
              f"· {len(history)} séance(s)")

    print(f"✓ Terminé : {created_patients} patient(s) et {created_sessions} séance(s) créés.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
