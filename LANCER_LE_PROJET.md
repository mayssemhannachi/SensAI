# SensAI — lancer la plateforme complète (version locale intégrée)

Une seule plateforme, trois services :

| Service | Dossier | Commande | Adresse |
|---------|---------|----------|---------|
| Backend (API) | `SensAI` | `uvicorn app.main:app --reload` | http://127.0.0.1:8000/docs |
| Site SensAI (accueil, connexion, espace enfant, jeu) | `SensAI-frontend` | `npm run dev` | **http://localhost:3000** |
| Espace thérapeute (dashboard d'analyse) | `SensAI/data_analysis` | `streamlit run dashboard/app.py` | http://localhost:8501 |

On n'ouvre que **http://localhost:3000** : le site envoie chacun au bon endroit.

## Parcours

- **Une seule page de connexion** (`/login`) pour tout le monde :
  - un **thérapeute** arrive directement sur son espace (dashboard), déjà connecté ;
  - un **patient** arrive sur son espace enfant (ses jeux).
- **Thérapeute** : `/register` pour créer son compte. Dans son espace : « Nouveau patient »
  → identité, diagnostic, jeu prescrit et ses réglages (angle cible, maintien, répétitions,
  vitesse, difficulté, limite de sécurité) → un **code d'activation à 6 caractères** est généré.
- **Patient / parent** : `/activate` avec le code → crée son e-mail et son mot de passe
  → espace enfant → Le Hibou (caméra, ou clavier ← →) → auto-évaluation douleur / effort → séance envoyée.
- **Retour thérapeute** : « ↻ Actualiser » → la séance, l'amplitude, la symétrie et la douleur apparaissent.

## Installation (une fois)

```powershell
cd SensAI
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m alembic upgrade head
cd data_analysis
pip install -r requirements.txt
cd ..\..\SensAI-frontend
npm install
Copy-Item .env.example .env.local
```

## Compte de démonstration (pour la présentation)

Backend démarré, depuis `SensAI\data_analysis` :

```powershell
python scripts/seed_backend.py --register
```

Crée : thérapeute **demo@sensai.tn / demo1234** (12 patients, ~8 semaines de séances du Hibou,
profils variés) et un compte enfant **salma.parent@sensai.tn / demo1234**.

## Mode hors-ligne (développement uniquement)

`$env:KINEKIDS_DATA_SOURCE = "demo"` avant `streamlit run` affiche les données CSV synthétiques
sans backend. Ce mode n'est pas proposé dans l'interface.
