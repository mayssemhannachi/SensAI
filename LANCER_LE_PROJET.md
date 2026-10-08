# Lancer SensAI / KineKids AI en entier (version locale intégrée)

Trois applications tournent ensemble :

| Partie | Dossier | Commande | Adresse |
|--------|---------|----------|---------|
| Backend FastAPI | `SensAI` (branche `local/back-connecte`) | `uvicorn app.main:app --reload` | http://127.0.0.1:8000/docs |
| Site Next.js (thérapeute + patient + jeu) | `SensAI-frontend` (branche `local/front-connecte`) | `npm run dev` | http://localhost:3000 |
| Dashboard d'analyse Streamlit | `SensAI/data_analysis` | `streamlit run dashboard/app.py` | http://localhost:8501 |

## Première installation

```powershell
# Backend
cd SensAI
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m alembic upgrade head      # ajoute les comptes patients + le catalogue de jeux

# Dashboard
cd data_analysis
pip install -r requirements.txt
cd ..

# Frontend
cd ..\SensAI-frontend
npm install
Copy-Item .env.example .env.local
```

## Parcours complet

1. **Thérapeute** — http://localhost:3000/register : créer un compte, puis :
   - « Nouveau patient » (prénom, nom, âge, diagnostic) ;
   - « Ajouter un jeu » → Le Hibou, avec ses réglages (angle cible, maintien, répétitions, vitesse, difficulté, limite) ;
   - « Générer un code d’activation » → code à 6 caractères à donner au patient.
2. **Patient / parent** — http://localhost:3000/activate : saisir le code, un e-mail et un mot de passe → espace patient.
3. **Jeu** — « Commencer un exercice » → Le Hibou, avec la caméra (ou au clavier : flèches ← →).
   À la fin, l’enfant indique sa douleur et son effort, puis la séance est envoyée.
4. **Suivi** — le thérapeute voit la séance sur `/therapist` (amplitude, symétrie, douleur, historique)
   et dans le dashboard Streamlit (mode **Backend**, même compte) pour l’analyse détaillée.

## Ce que la version locale ajoute au backend

- `POST /auth/activate` : création du compte patient avec le code d’activation (6 caractères).
- `GET/POST /me/...` : profil, jeux attribués (avec réglages) et séances du patient connecté.
- `PUT /patient-games/{id}` : modification des réglages d’un jeu attribué.
- `GET /consultations/patient/{id}` : relecture des diagnostics.
- Routes du thérapeute interdites aux comptes patients ; `GET /patients/code/{code}` limité aux patients du thérapeute.
- Migration : `patients.user_id` + catalogue des jeux SensAI (Le Hibou, Color Touch, …).

Ces changements sont sur des branches **locales** : quand l’équipe publiera ses versions, récupérer ses mises à jour avec `git fetch` puis les fusionner (`git merge origin/<branche>`).
