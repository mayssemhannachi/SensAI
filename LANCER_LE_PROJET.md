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
  → identité, diagnostic, jeu prescrit et ses réglages → un **code d'activation à 6 caractères** est généré.
  - **Le Hibou** (rotation cervicale) : angle cible, maintien, répétitions, vitesse, difficulté,
    limite de sécurité, sensibilité de la caméra, inversion du sens ;
  - **Le Gardien des Lucioles** (abduction de l'épaule, jeu de Maram) : bras à entraîner, mode
    hémiplégie / bilatéral, seuil d'abduction, extension du coude, tolérance de l'autre bras,
    nombre de lucioles, maintien.
- **Patient / parent** : `/activate` avec le code → crée son e-mail et son mot de passe
  → espace enfant → ses jeux (caméra, ou clavier : ← → pour le Hibou, ↑ ↓ pour les Lucioles)
  → auto-évaluation douleur / effort → séance envoyée.
- **Retour thérapeute** : « ↻ Actualiser » → la séance apparaît avec ses analyses (amplitude cervicale
  et symétrie pour le Hibou ; abduction et compensations pour les Lucioles ; douleur et effort).

> Le mode caméra télécharge les modèles MediaPipe sur Internet (connexion requise). Le mode clavier
> fonctionne sans Internet : utile en secours pendant une présentation.

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

Crée : thérapeute **demo@sensai.tn / demo1234** (12 patients au Hibou et 3 au Gardien des Lucioles,
~8 semaines de séances, profils variés) et un compte enfant **salma.parent@sensai.tn / demo1234**
(qui a les deux jeux). Le script est relançable : il n'ajoute que ce qui manque.

Après une mise à jour du projet, toujours relancer `python -m alembic upgrade head` (nouveaux jeux).

## Mode hors-ligne (développement uniquement)

`$env:KINEKIDS_DATA_SOURCE = "demo"` avant `streamlit run` affiche les données CSV synthétiques
sans backend. Ce mode n'est pas proposé dans l'interface.
