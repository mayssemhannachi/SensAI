# SensAI — Jeu du Hibou (branche `feature/game-hibou`)

> **KineKids AI** — Module de kinésithérapie pédiatrique assistée par IA.  
> Cette branche ajoute **Le Hibou**, un mini-jeu de rotation du cou utilisant la webcam et MediaPipe.

---

## Table des matières

1. [Aperçu du projet](#aperçu-du-projet)
2. [Prérequis](#prérequis)
3. [Cloner le projet & choisir la branche](#cloner-le-projet--choisir-la-branche)
4. [Environnement virtuel](#environnement-virtuel)
5. [Dépendances](#dépendances)
6. [Configuration PostgreSQL & variables d'environnement](#configuration-postgresql--variables-denvironnement)
7. [Migrations Alembic](#migrations-alembic)
8. [Lancer le backend FastAPI](#lancer-le-backend-fastapi)
9. [Jeu du Hibou — `hibou.py`](#jeu-du-hibou--hiboupy)
10. [Architecture du projet](#architecture-du-projet)
11. [API — Référence rapide](#api--référence-rapide)
12. [Sécurité](#sécurité)

---

## Aperçu du projet

| Composant | Description |
|---|---|
| **Backend** | FastAPI + PostgreSQL + SQLAlchemy + Alembic |
| **Jeu Hibou** | Script Python (OpenCV + MediaPipe) — rotation du cou guidée |
| **Branche** | `feature/game-hibou` |
| **Fichier jeu** | `hibou.py` |

---

## Prérequis

- Python **3.10+** (testé avec 3.12)
- PostgreSQL **14+**
- Git
- Une webcam (pour le jeu du Hibou en mode caméra)
- `pip` à jour : `pip install --upgrade pip`

---

## Cloner le projet & choisir la branche

```bash
# 1. Cloner le dépôt principal
git clone <URL_DU_REPOSITORY>
cd SensAI

# 2. Basculer sur la branche du jeu Hibou
git checkout feature/game-hibou
```

---

## Environnement virtuel

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

> Lorsque l'environnement est actif, le terminal affiche `(.venv)`.

---

## Dépendances

### 1. Dépendances du backend (depuis `requirements.txt`)

```bash
pip install -r requirements.txt
```

Principales bibliothèques incluses :

| Bibliothèque | Version | Rôle |
|---|---|---|
| `fastapi` | 0.141.1 | Framework API |
| `uvicorn` | 0.54.0 | Serveur ASGI |
| `SQLAlchemy` | 2.1.1 | ORM |
| `alembic` | 1.20.0 | Migrations BDD |
| `pydantic` | 2.13.5 | Validation des données |
| `psycopg2-binary` | 2.9.13 | Driver PostgreSQL |
| `python-jose` | 3.5.0 | JWT |
| `passlib` + `bcrypt` | 1.7.4 / 5.0.0 | Hachage mots de passe |
| `python-dotenv` | 1.2.3 | Variables d'environnement |

### 2. Dépendances supplémentaires pour le jeu Hibou

Ces paquets **ne sont pas** dans `requirements.txt` (spécifiques au module jeu) :

```bash
pip install opencv-python mediapipe numpy
```

| Bibliothèque | Rôle |
|---|---|
| `opencv-python` | Capture webcam & affichage |
| `mediapipe` | Détection du visage & squelette |
| `numpy` | Calculs d'angles |

---

## Configuration PostgreSQL & variables d'environnement

### 1. Créer la base de données

```sql
CREATE DATABASE kinekids_db;
```

### 2. Créer le fichier `.env` à la racine du projet

```env
# Connexion base de données
DATABASE_URL=postgresql+psycopg2://postgres:VOTRE_MOT_DE_PASSE@localhost:5432/kinekids_db

# Sécurité JWT
SECRET_KEY=changez_cette_cle_secrete_en_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (optionnel)
CORS_ORIGINS='["http://localhost:3000","http://localhost:5173"]'
```

> ⚠️ **Ne jamais committer ce fichier.** Il est déjà dans `.gitignore`.

---

## Migrations Alembic

```bash
# Appliquer toutes les migrations existantes
python -m alembic upgrade head

# Générer une nouvelle migration après modification des modèles
python -m alembic revision --autogenerate -m "description de la migration"
```

---

## Lancer le backend FastAPI

```bash
uvicorn app.main:app --reload
```

| URL | Description |
|---|---|
| `http://127.0.0.1:8000` | API principale |
| `http://127.0.0.1:8000/docs` | Documentation Swagger interactive |
| `http://127.0.0.1:8000/openapi.json` | Schéma OpenAPI |
| `GET /health` | Vérification de disponibilité |

---

## Jeu du Hibou — `hibou.py`

Le Hibou est un exercice de kinésithérapie pédiatrique qui guide l'enfant dans des rotations du cou (gauche/droite) via une animation interactive et la détection du visage par webcam.

### Lancement rapide

```bash
# Mode standard (webcam, paramètres par défaut)
python hibou.py

# Mode clavier (sans caméra — A = gauche, D = droite)
python hibou.py --kb

# Avec envoi du bilan au backend
python hibou.py --api http://localhost:8000/sessions/
```

### Options disponibles

| Option | Défaut | Description |
|---|---|---|
| `--cible` | `35` | Amplitude cible en degrés |
| `--limite` | `55` | Limite de sécurité en degrés |
| `--maintien` | `3` | Temps de maintien à la cible (secondes) |
| `--reps` | `6` | Nombre de répétitions total |
| `--vmax` | `40` | Vitesse maximale autorisée (deg/s) |
| `--cote` | `both` | Côté(s) : `droite`, `gauche`, `both` |
| `--camera` | `0` | Index de la caméra |
| `--gain` | `1.25` | Gain de l'angle de rotation |
| `--seuil-epaule` | `18.0` | Seuil détection compensation épaules (deg) |
| `--inv` | — | Inverser le sens de rotation |
| `--kb` | — | Mode clavier (sans caméra) |
| `--api` | — | URL du backend pour envoi du bilan JSON |

### Touches pendant le jeu

| Touche | Action |
|---|---|
| `C` | Recalibrer la position neutre |
| `S` | Signaler douleur / arrêter |
| `Q` | Quitter |

### Exemples avancés

```bash
# Séance personnalisée : 40° cible, 3s maintien, 8 reps
python hibou.py --cible 40 --limite 60 --maintien 3 --reps 8 --cote both

# Hibou inversé (caméra miroir)
python hibou.py --inv

# Envoi des résultats au backend
python hibou.py --api http://localhost:8000/sessions/
```

---

## Architecture du projet

```
SensAI/
│
├── app/
│   ├── core/           # Config, sécurité, JWT
│   ├── database/       # Connexion SQLAlchemy
│   ├── models/         # Modèles ORM
│   ├── repositories/   # Accès données
│   ├── routers/        # Routes FastAPI
│   ├── schemas/        # Schémas Pydantic
│   ├── services/       # Logique métier
│   ├── utils/          # Utilitaires
│   └── main.py         # Point d'entrée FastAPI
│
├── alembic/            # Migrations BDD
├── hibou.py            # Jeu du Hibou (cette branche)
├── alembic.ini
├── requirements.txt    # Dépendances backend
├── .env                # Variables d'environnement (non commité)
└── README.md
```

**Flux applicatif backend :**

```
Router → Service → Repository → SQLAlchemy Model → PostgreSQL
```

---

## API — Référence rapide

Toutes les routes (sauf `GET /health`) nécessitent un **Bearer Token**.

### Authentification

```
POST /auth/register    { "full_name", "email", "password" }
POST /auth/login       { "email", "password" }  → access_token
GET  /auth/me
```

### Patients

```
POST   /patients/
GET    /patients/
GET    /patients/{patient_id}
PUT    /patients/{patient_id}
DELETE /patients/{patient_id}
GET    /patients/code/{patient_code}
POST   /patients/{patient_id}/regenerate-code
```

### Jeux & Sessions

```
GET  /games/
POST /games/
POST /patient-games/
GET  /patient-games/patient/{patient_id}
POST /sessions/
GET  /sessions/patient-game/{patient_game_id}
POST /session-events/
GET  /session-events/session/{session_id}
```

---

## Sécurité

Ne jamais ajouter au dépôt Git :

- `.env`
- Mots de passe PostgreSQL
- Clés secrètes JWT
- Dossier environnement virtuel (`.venv/`)

`.gitignore` minimal recommandé :

```gitignore
.venv/
.env
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
dist/
```

---

*Branche maintenue par l'équipe **feature/game-hibou** — Hackathon KineKids AI 2026.*
