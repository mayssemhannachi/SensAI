"""Crée un compte de démonstration SensAI complet, via l'API (jamais en base directe).

Résultat : un thérapeute avec une quinzaine de patients suivis sur plusieurs semaines
au jeu « Le Hibou » (rotation cervicale) ou au « Gardien des Lucioles » (abduction de
l'épaule), avec des profils variés (en progression, stable, douleur élevée, inactif,
compensations…), leurs diagnostics, leurs réglages et un compte patient déjà activé
pour montrer l'espace enfant.

Exemple (depuis le dossier ``data_analysis``, backend démarré) :

    python scripts/seed_backend.py --register

Identifiants créés par défaut :
    kinésithérapeute : demo@sensai.tn / demo1234         (Le Hibou, Le Gardien des Lucioles)
    ergothérapeute   : ergo@sensai.tn / demo1234         (La Danse des Lucioles)
    patient (kiné)   : salma.parent@sensai.tn / demo1234
    patient (ergo)   : ines.parent@sensai.tn / demo1234

Le script est idempotent : un patient déjà présent (même prénom et nom) est ignoré.
Les séances portent leur date réelle dans ``metrics.played_at`` (l'API horodate
``created_at`` au moment de l'enregistrement).
"""

from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime, timedelta

import requests

DIFFICULTY_LEVEL = {"faible": 1, "moyenne": 2, "elevee": 3}

# prénom, nom, âge, diagnostic, profil
PATIENTS = [
    ("Salma", "Ben Ali", 8, "Torticolis post-traumatique", "progress"),
    ("Adam", "Trabelsi", 10, "Raideur cervicale après immobilisation", "progress"),
    ("Yasmine", "Bouzid", 12, "Cervicalgie posturale", "stable"),
    ("Rayan", "Mansouri", 7, "Torticolis musculaire congénital (suivi)", "pain"),
    ("Lina", "Chaouch", 9, "Rééducation après entorse cervicale", "progress"),
    ("Omar", "Dridi", 11, "Plagiocéphalie avec limitation de rotation", "asym"),
    ("Nour", "Zouari", 6, "Torticolis post-traumatique", "progress"),
    ("Eya", "Haddad", 13, "Cervicalgie posturale", "decline"),
    ("Malek", "Hamdi", 9, "Raideur cervicale après immobilisation", "inactive"),
    ("Hiba", "Khelifi", 8, "Torticolis musculaire congénital (suivi)", "stable"),
    ("Zied", "Gharbi", 14, "Rééducation après entorse cervicale", "progress"),
    ("Amira", "Jebali", 7, "Torticolis post-traumatique", "new"),
]

# Patients suivis au Gardien des Lucioles : prénom, nom, âge, diagnostic, profil, bras
LUCIOLES_PATIENTS = [
    ("Youssef", "Ayari", 9, "Hémiplégie droite (paralysie cérébrale)", "abd_progress", "R"),
    ("Mariem", "Saidi", 11, "Raideur de l'épaule après fracture de l'humérus", "abd_stable", "L"),
    ("Ilyes", "Ferchichi", 8, "Paralysie obstétricale du plexus brachial", "abd_comp", "R"),
]

LUCIOLES_PROFILES = {
    #               départ°, gain°/séance, séances/sem, compensations moy.
    "abd_progress": (62, 2.4, 3, 2.2),
    "abd_stable":   (98, 0.2, 3, 0.4),
    "abd_comp":     (58, 1.0, 3, 3.6),
}

PROFILES = {
    #            départ°, gain°/séance, séances/sem, asymétrie, douleur
    "progress": (16, 0.55, 3, 0.95, 1.2),
    "stable":   (24, 0.05, 3, 0.97, 1.0),
    "pain":     (18, 0.35, 3, 0.90, 3.4),
    "asym":     (18, 0.45, 3, 0.70, 1.5),
    "decline":  (27, -0.30, 2, 0.93, 2.2),
    "inactive": (15, 0.40, 2, 0.92, 1.4),
    "new":      (14, 0.60, 2, 0.94, 1.0),
}


class Api:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.http = requests.Session()
        self.token = None

    def call(self, method: str, path: str, payload=None, auth=True, token=None):
        bearer = token or (self.token if auth else None)
        headers = {"Authorization": f"Bearer {bearer}"} if bearer else {}
        response = self.http.request(method, self.base_url + path, json=payload, headers=headers, timeout=20)
        if not response.ok:
            raise RuntimeError(f"{method} {path} → {response.status_code} : {response.text[:300]}")
        return response.json() if response.content else None


def clamp(value, low, high):
    return max(low, min(high, value))


def simulate_sessions(profile: str, weeks: int, rng: random.Random, now: datetime):
    """Séances simulées d'un patient, de la plus ancienne à la plus récente."""
    start, gain, per_week, asym, pain_base = PROFILES[profile]
    if profile == "new":
        weeks = 2
    end = now - timedelta(days=24) if profile == "inactive" else now - timedelta(hours=20)
    first_day = end - timedelta(weeks=weeks)
    total = max(3, weeks * per_week + rng.randint(-2, 1))
    sessions = []
    for k in range(total):
        played = first_day + (end - first_day) * (k / max(total - 1, 1))
        played = played.replace(hour=rng.choice([10, 14, 16, 17, 18]), minute=rng.choice([0, 15, 30, 45]))
        amplitude = start + gain * k + rng.gauss(0, 1.6)
        # Objectif fixé par le thérapeute : un peu sous l'amplitude atteinte (palier de 5°),
        # trop ambitieux pour le profil « douleur », figé pour le profil « en baisse ».
        target = int(clamp(5 * ((amplitude - 1) // 5), 15, 35))
        if profile == "pain":
            target = int(clamp(target + 5, 15, 40))
        if profile == "decline":
            target = 25
        weak_side = rng.random() < 0.5
        right = clamp(amplitude * (asym if weak_side else 1) + rng.gauss(0, 1), 5, 60)
        left = clamp(amplitude * (1 if weak_side else asym) + rng.gauss(0, 1), 5, 60)
        reps = 6
        # Répétitions alternées droite / gauche : réussie si le côté atteint l'objectif.
        reached = sum(
            1 for r in range(reps)
            if (right if r % 2 == 0 else left) + rng.gauss(0, 2.5) >= target
        )
        success = reached / reps * 100
        peak = (left + right) / 2
        overshoots = 1 if max(left, right) > target + 12 and rng.random() < 0.3 else 0
        score = clamp(round(success * 0.7 + min(1, peak / target) * 30 - overshoots * 2), 0, 100)
        recent = k >= total - 3
        pain = clamp(round(pain_base + (1.4 if profile == "pain" and recent else 0) + rng.gauss(0, 0.7)), 0, 5)
        effort = clamp(round(2 + (target - 20) / 8 + rng.gauss(0, 0.8)), 0, 5)
        difficulty = "faible" if target <= 20 else "moyenne" if target <= 30 else "elevee"
        sessions.append({
            "played_at": played,
            "duration_sec": int(rng.randint(150, 330)),
            "metrics": {
                "score": score,
                "success_rate": round(success, 1),
                "repetitions": reached,
                "repetitions_target": reps,
                "level_number": DIFFICULTY_LEVEL[difficulty],
                "exercise_name": "Rotation cervicale",
                "played_at": played.isoformat(),
                "rotation_left": round(left),
                "rotation_right": round(right),
                "hold_seconds_avg": round(clamp(2.4 + rng.gauss(0.4, 0.5), 0.5, 5), 1),
                "smoothness": int(clamp(70 + k * 0.6 + rng.gauss(0, 6), 40, 98)),
                "overshoots": overshoots,
                "completed": reached == reps or rng.random() < 0.7,
                "pain_level": pain,
                "effort": effort,
                "target_angle": target,
                "input_mode": "camera",
            },
            "target": target,
            "difficulty": difficulty,
        })
    return sessions


def simulate_lucioles(profile: str, arm: str, weeks: int, rng: random.Random, now: datetime):
    """Séances simulées du Gardien des Lucioles (abduction de l'épaule)."""
    start, gain, per_week, comp_base = LUCIOLES_PROFILES[profile]
    end = now - timedelta(hours=26)
    first_day = end - timedelta(weeks=weeks)
    total = max(3, weeks * per_week + rng.randint(-2, 1))
    sessions = []
    for k in range(total):
        played = first_day + (end - first_day) * (k / max(total - 1, 1))
        played = played.replace(hour=rng.choice([10, 14, 16, 17, 18]), minute=rng.choice([0, 15, 30, 45]))
        level = start + gain * k + rng.gauss(0, 3)
        threshold = int(clamp(5 * ((level - 4) // 5), 40, 150))
        target_reps = 10
        peaks = [clamp(level + rng.gauss(0, 6), 20, 175) for _ in range(target_reps)]
        valid = [p for p in peaks if p >= threshold]
        success = len(valid) / target_reps * 100
        mean_peak = round(sum(valid) / len(valid)) if valid else 0
        decay = 0.6 if profile == "abd_progress" else 1.0
        comps = max(0, round(comp_base * (decay ** (k / 6)) + rng.gauss(0, 0.9)))
        score = clamp(round(success * 0.7 + min(1, mean_peak / threshold) * 30 - comps * 2), 0, 100)
        difficulty = "faible" if threshold <= 70 else "moyenne" if threshold <= 110 else "elevee"
        sessions.append({
            "played_at": played,
            "duration_sec": int(rng.randint(180, 420)),
            "metrics": {
                "score": score,
                "success_rate": round(success, 1),
                "repetitions": len(valid),
                "repetitions_target": target_reps,
                "level_number": DIFFICULTY_LEVEL[difficulty],
                "exercise_name": "Abduction de l'épaule",
                "played_at": played.isoformat(),
                "abduction_max": round(max(peaks)),
                "abduction_mean_peak": mean_peak,
                "compensations": comps,
                "affected_arm": arm,
                "mode": "hemi",
                "direction": "side",
                "target_angle": threshold,
                "elbow_min": 140,
                "rest_tolerance": 35,
                "completed": len(valid) >= target_reps or rng.random() < 0.6,
                "pain_level": clamp(round(1 + rng.gauss(0, 0.8)), 0, 5),
                "effort": clamp(round(2 + (threshold - 80) / 30 + rng.gauss(0, 0.8)), 0, 5),
                "input_mode": "camera",
            },
            "target": threshold,
            "difficulty": difficulty,
        })
    return sessions


# Patients suivis en ergothérapie (La Danse des Lucioles) : prénom, nom, âge, diagnostic, profil, main
ERGO_PATIENTS = [
    ("Ines", "Mabrouk", 7, "Trouble développemental de la coordination (dyspraxie)", "seq_progress", "any"),
    ("Aziz", "Kammoun", 9, "TDAH : difficultés de planification et d'attention", "seq_errors", "any"),
    ("Sarra", "Sassi", 8, "Hémiplégie cérébrale infantile : coordination des deux mains", "seq_progress", "alt"),
    ("Mehdi", "Toumi", 10, "Retard de développement : autonomie dans les gestes du quotidien", "seq_stable", "R"),
    ("Lyna", "Belhadj", 6, "Trouble développemental de la coordination (dyspraxie)", "new", "any"),
]

SEQ_PROFILES = {
    #               séquence de départ, gain/séance, séances/sem, erreurs moyennes, aides moyennes
    "seq_progress": (2.0, 0.12, 3, 1.6, 0.8),
    "seq_errors":   (2.2, 0.04, 3, 4.6, 1.8),
    "seq_stable":   (3.0, 0.02, 2, 1.2, 0.4),
    "new":          (2.0, 0.15, 2, 2.0, 1.0),
}


def simulate_danse(profile: str, weeks: int, rng: random.Random, now: datetime):
    """Séances simulées de La Danse des Lucioles (mémoire de séquence)."""
    start, gain, per_week, err_base, hint_base = SEQ_PROFILES[profile]
    if profile == "new":
        weeks = 2
    end = now - timedelta(hours=22)
    first_day = end - timedelta(weeks=weeks)
    total = max(3, weeks * per_week + rng.randint(-2, 1))
    sessions = []
    for k in range(total):
        played = first_day + (end - first_day) * (k / max(total - 1, 1))
        played = played.replace(hour=rng.choice([10, 14, 16, 17]), minute=rng.choice([0, 15, 30, 45]))
        span = clamp(start + gain * k + rng.gauss(0, 0.35), 2, 5)
        level = "easy" if span < 2.8 else "mid" if span < 3.8 else "hard"
        target = 5
        decay = 0.7 if profile != "seq_errors" else 1.0
        errors = max(0, round(err_base * (decay ** (k / 6)) + rng.gauss(0, 0.9)))
        hints = max(0, round(hint_base * (decay ** (k / 6)) + rng.gauss(0, 0.5)))
        done = int(clamp(target - max(0, errors - 3) // 2 + (0 if rng.random() < 0.8 else -1), 1, target))
        success = done / target * 100
        max_seq = int(round(span))
        score = clamp(round(success * 0.7 + min(1, max_seq / 5) * 30 - errors * 2 - hints), 0, 100)
        sessions.append({
            "played_at": played,
            "duration_sec": int(rng.randint(200, 420)),
            "metrics": {
                "score": score,
                "success_rate": round(success, 1),
                "repetitions": done,
                "repetitions_target": target,
                "level_number": {"easy": 1, "mid": 2, "hard": 3}[level],
                "exercise_name": "Séquence de fleurs (mémoire et coordination)",
                "played_at": played.isoformat(),
                "max_sequence": max_seq,
                "sequence_errors": errors,
                "hints_used": hints,
                "mean_step_sec": round(clamp(3.2 - 0.04 * k + rng.gauss(0, 0.35), 1.1, 5), 2),
                "level": level,
                "completed": done >= target,
                "pain_level": clamp(round(0.4 + rng.gauss(0, 0.6)), 0, 5),
                "effort": clamp(round(1.5 + (max_seq - 2) * 0.6 + rng.gauss(0, 0.8)), 0, 5),
                "input_mode": "camera",
            },
            "level": level,
        })
    return sessions


def seed_ergo(args, rng: random.Random, now: datetime) -> tuple[int, int]:
    """Compte ergothérapeute de démonstration et ses patients (La Danse des Lucioles)."""
    api = Api(args.api_url)
    credentials = {"email": args.ergo_email, "password": args.password}
    try:
        api.token = api.call("POST", "/auth/login", credentials, auth=False)["access_token"]
    except RuntimeError:
        api.call("POST", "/auth/register", {"full_name": args.ergo_name, "specialty": "ergotherapist",
                                            **credentials}, auth=False)
        api.token = api.call("POST", "/auth/login", credentials, auth=False)["access_token"]
        print(f"✓ Compte ergothérapeute créé : {args.ergo_email}")
    games = {g["slug"]: g for g in api.call("GET", "/games/")}
    danse = games.get("danse-lucioles")
    if not danse:
        print("! La Danse des Lucioles est absente du catalogue ergothérapeute : "
              "lancez `python -m alembic upgrade head`.")
        return 0, 0
    existing = {(p["first_name"].lower(), p["last_name"].lower()) for p in api.call("GET", "/patients/")}
    created_patients = created_sessions = 0
    for first, last, age, diagnosis, profile, hand in ERGO_PATIENTS:
        if (first.lower(), last.lower()) in existing:
            print(f"  = {first} {last} existe déjà, ignoré")
            continue
        patient = api.call("POST", "/patients/", {"first_name": first, "last_name": last, "age": age})
        created_patients += 1
        history = simulate_danse(profile, args.weeks, rng, now)
        api.call("POST", "/consultations/", {
            "patient_id": patient["id"],
            "consultation_date": (history[0]["played_at"] - timedelta(days=3)).date().isoformat(),
            "diagnosis": diagnosis,
        })
        level = history[-1]["level"]
        config = {"hand_mode": hand, "level": level, "repetitions": 5, "target_size": "big",
                  "difficulty": {"easy": "faible", "mid": "moyenne", "hard": "elevee"}[level], "active": True}
        association = api.call("POST", "/patient-games/", {
            "patient_id": patient["id"], "game_id": danse["id"], "configuration": config,
        })
        for session in history:
            for key in ("hand_mode",):
                session["metrics"][key] = hand
            api.call("POST", "/sessions/", {
                "patient_game_id": association["id"],
                "duration_sec": session["duration_sec"],
                "metrics": session["metrics"],
            })
            created_sessions += 1
        print(f"  + {first} {last} ({profile}, Danse des Lucioles) · {len(history)} séance(s)")
        if first == "Ines" and args.ergo_patient_email:
            code = api.call("POST", "/activation-codes/", {"patient_id": patient["id"]})["code"]
            try:
                api.call("POST", "/auth/activate", {
                    "code": code, "email": args.ergo_patient_email, "password": args.patient_password,
                }, auth=False)
                print(f"    ✓ compte patient activé : {args.ergo_patient_email} / {args.patient_password}")
            except RuntimeError as error:
                print(f"    ! compte patient non créé ({error}) — code d’activation : {code}")
    return created_patients, created_sessions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--email", default="demo@sensai.tn")
    parser.add_argument("--password", default="demo1234")
    parser.add_argument("--full-name", default="Dr Sarah Ben Youssef")
    parser.add_argument("--register", action="store_true", help="créer le compte thérapeute s'il n'existe pas")
    parser.add_argument("--weeks", type=int, default=8)
    parser.add_argument("--patient-email", default="salma.parent@sensai.tn")
    parser.add_argument("--patient-password", default="demo1234")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--ergo-email", default="ergo@sensai.tn")
    parser.add_argument("--ergo-name", default="Dr Amel Gharbi")
    parser.add_argument("--ergo-patient-email", default="ines.parent@sensai.tn")
    parser.add_argument("--no-ergo", action="store_true", help="ne pas créer le compte ergothérapeute")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    api = Api(args.api_url)
    try:
        api.call("GET", "/health", auth=False)
    except Exception as exc:  # noqa: BLE001
        print(f"✗ Backend injoignable à {args.api_url} : {exc}")
        return 1

    credentials = {"email": args.email, "password": args.password}
    try:
        api.token = api.call("POST", "/auth/login", credentials, auth=False)["access_token"]
    except RuntimeError:
        if not args.register:
            print("✗ Connexion refusée. Ajoutez --register pour créer le compte.")
            return 1
        api.call("POST", "/auth/register",
                 {"full_name": args.full_name, "specialty": "kinesitherapist", **credentials}, auth=False)
        api.token = api.call("POST", "/auth/login", credentials, auth=False)["access_token"]
        print(f"✓ Compte thérapeute créé : {args.email}")
    print(f"✓ Connecté : {args.email}")

    games = {g["slug"]: g for g in api.call("GET", "/games/")}
    hibou = games.get("le-hibou")
    if not hibou:
        print("✗ Le jeu « Le Hibou » est absent du catalogue : lancez `python -m alembic upgrade head`.")
        return 1

    lucioles = games.get("gardien-lucioles")
    existing = {(p["first_name"].lower(), p["last_name"].lower()) for p in api.call("GET", "/patients/")}
    now = datetime.now()
    created_patients = created_sessions = 0
    for first, last, age, diagnosis, profile in PATIENTS:
        if (first.lower(), last.lower()) in existing:
            print(f"  = {first} {last} existe déjà, ignoré")
            continue
        patient = api.call("POST", "/patients/", {"first_name": first, "last_name": last, "age": age})
        created_patients += 1
        history = simulate_sessions(profile, args.weeks, rng, now)
        first_date = history[0]["played_at"] if history else now
        api.call("POST", "/consultations/", {
            "patient_id": patient["id"],
            "consultation_date": (first_date - timedelta(days=3)).date().isoformat(),
            "diagnosis": diagnosis,
        })
        last_session = history[-1]
        config = {
            "target_angle": last_session["target"],
            "hold_seconds": 3,
            "repetitions": 6,
            "speed": "lente",
            "difficulty": last_session["difficulty"],
            "safety_limit": last_session["target"] + 10,
            "active": True,
        }
        association = api.call("POST", "/patient-games/", {
            "patient_id": patient["id"], "game_id": hibou["id"], "configuration": config,
        })
        for session in history:
            api.call("POST", "/sessions/", {
                "patient_game_id": association["id"],
                "duration_sec": session["duration_sec"],
                "metrics": session["metrics"],
            })
            created_sessions += 1
        print(f"  + {first} {last} ({profile}) · {len(history)} séance(s)")

        # Compte patient de démonstration (espace enfant)
        if first == "Salma" and args.patient_email:
            code = api.call("POST", "/activation-codes/", {"patient_id": patient["id"]})["code"]
            try:
                api.call("POST", "/auth/activate", {
                    "code": code, "email": args.patient_email, "password": args.patient_password,
                }, auth=False)
                print(f"    ✓ compte patient activé : {args.patient_email} / {args.patient_password}")
            except RuntimeError as error:
                print(f"    ! compte patient non créé ({error}) — code d’activation : {code}")

    # Patients suivis au Gardien des Lucioles
    if not lucioles:
        print("! Le Gardien des Lucioles est absent du catalogue : lancez `python -m alembic upgrade head`.")
    for first, last, age, diagnosis, profile, arm in (LUCIOLES_PATIENTS if lucioles else []):
        if (first.lower(), last.lower()) in existing:
            print(f"  = {first} {last} existe déjà, ignoré")
            continue
        patient = api.call("POST", "/patients/", {"first_name": first, "last_name": last, "age": age})
        created_patients += 1
        history = simulate_lucioles(profile, arm, args.weeks, rng, now)
        api.call("POST", "/consultations/", {
            "patient_id": patient["id"],
            "consultation_date": (history[0]["played_at"] - timedelta(days=3)).date().isoformat(),
            "diagnosis": diagnosis,
        })
        last_session = history[-1]
        config = {
            "affected_arm": arm, "mode": "hemi", "direction": "side", "target_angle": last_session["target"],
            "elbow_min": 140, "rest_tolerance": 35, "repetitions": 10, "hold_seconds": 1,
            "difficulty": last_session["difficulty"], "active": True,
        }
        association = api.call("POST", "/patient-games/", {
            "patient_id": patient["id"], "game_id": lucioles["id"], "configuration": config,
        })
        for session in history:
            api.call("POST", "/sessions/", {
                "patient_game_id": association["id"],
                "duration_sec": session["duration_sec"],
                "metrics": session["metrics"],
            })
            created_sessions += 1
        print(f"  + {first} {last} ({profile}, Lucioles) · {len(history)} séance(s)")

    # Salma joue aussi au Gardien des Lucioles (espace enfant avec deux jeux)
    if lucioles:
        salma = next((p for p in api.call("GET", "/patients/")
                      if (p["first_name"], p["last_name"]) == ("Salma", "Ben Ali")), None)
        if salma:
            assigned = {pg["game_id"] for pg in api.call("GET", f"/patient-games/patient/{salma['id']}")}
            if lucioles["id"] not in assigned:
                api.call("POST", "/patient-games/", {
                    "patient_id": salma["id"], "game_id": lucioles["id"],
                    "configuration": {"affected_arm": "R", "mode": "hemi", "direction": "side", "target_angle": 80,
                                      "elbow_min": 140, "rest_tolerance": 35, "repetitions": 8,
                                      "hold_seconds": 1, "difficulty": "moyenne", "active": True},
                })
                print("  + Gardien des Lucioles ajouté à Salma Ben Ali")

    if not args.no_ergo:
        print("— Espace ergothérapeute —")
        ergo_patients, ergo_sessions = seed_ergo(args, rng, now)
        created_patients += ergo_patients
        created_sessions += ergo_sessions

    print(f"✓ Terminé : {created_patients} patient(s), {created_sessions} séance(s).")
    print(f"  Kinésithérapeute : {args.email} / {args.password}")
    if args.patient_email:
        print(f"  Patient (kiné)   : {args.patient_email} / {args.patient_password}")
    if not args.no_ergo:
        print(f"  Ergothérapeute   : {args.ergo_email} / {args.password}")
        print(f"  Patient (ergo)   : {args.ergo_patient_email} / {args.patient_password}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
