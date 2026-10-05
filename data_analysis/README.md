# KineKids AI — Analyse et tableau de bord thérapeute

Ce dossier contient le prototype Streamlit du tableau de bord thérapeute et les modules d’analyse de données.

## Lancer le dashboard

Depuis le dossier `data_analysis` :

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run dashboard/app.py
```

Ouvrir l’adresse locale affichée par Streamlit dans le navigateur.

## Données de démonstration

Le dashboard lit actuellement les patients dans `data/raw/patients.csv` et les séances analysées dans `data/processed/session_analysis.csv`. Ces fichiers sont des données de démonstration synthétiques ; ils ne doivent pas être remplacés par des données médicales identifiantes dans le dépôt.

Le mode CSV reste le mode par défaut et permet de présenter le prototype sans backend.

## Connexion au backend FastAPI

Le dashboard appelle l’API FastAPI ; il ne se connecte jamais directement à PostgreSQL. L’équipe backend doit d’abord démarrer l’API, appliquer ses migrations et fournir un compte thérapeute de test. L’URL locale par défaut est `http://127.0.0.1:8000`.

Dans PowerShell, depuis le dossier `data_analysis`, activez le mode API avant de lancer Streamlit :

```powershell
$env:KINEKIDS_DATA_SOURCE = "api"
$env:KINEKIDS_API_URL = "http://127.0.0.1:8000"
streamlit run dashboard/app.py
```

Le dashboard affiche alors un formulaire de connexion. Il utilise `POST /auth/login` puis envoie le jeton reçu dans l’en-tête Bearer des appels protégés. Aucun mot de passe ni jeton ne doit être inscrit dans le code ou commité.

Pour revenir au mode CSV dans le terminal courant, définissez `KINEKIDS_DATA_SOURCE` à `csv` ou ouvrez un nouveau terminal.

### Contrat actuel côté API

- Création patient : `POST /patients/` avec `first_name`, `last_name` et `age`. L’API produit le code patient et rattache le thérapeute connecté. Le formulaire utilise donc l’âge dans ce mode ; la date de naissance et le code personnalisé sont uniquement disponibles en mode CSV.
- Jeux : le dashboard lit `GET /games/` et les associations par `GET /patient-games/patient/{patient_id}`.
- Séances : l’API les expose par `GET /sessions/patient-game/{patient_game_id}`. Le dashboard les rassemble en parcourant les patients et leurs jeux associés.
- Durée : l’API fournit `duration_sec`; le dashboard la convertit en minutes pour correspondre aux graphiques CSV existants.
- Mesures : les jeux et l’équipe backend doivent convenir des clés JSON `metrics` communes. Le dashboard reconnaît `score`, `success_rate`, `progression`, `repetitions`, `level_number`, `exercise_id` et `exercise_name`. `success_rate` doit être un pourcentage de 0 à 100 ; progression est un pourcentage signé. Les mesures absentes restent indisponibles, elles ne sont pas inventées.
- Diagnostic : l’API permet de créer une consultation avec `POST /consultations/`, mais n’expose pas encore de route de lecture des consultations. Le dashboard peut soumettre le diagnostic lors de la création du patient, mais ne peut pas ensuite l’afficher dans la fiche.

**À confirmer avec l’équipe backend avant la démonstration :** les jeux doivent être initialisés dans le catalogue de l’API et envoyer les mêmes clés et unités pour `metrics`. Pour des volumes supérieurs au prototype, une route API de synthèse listant les séances accessibles au thérapeute évitera les appels successifs par patient et par jeu.

## Navigation actuelle

- Vue globale : indicateurs filtrables par période, graphiques, signaux à revoir et séances récentes.
- Patients : recherche et accès aux fiches.
- Fiche patient : historique, indicateurs et diagnostic.
- Ajouter un patient : création d’un profil de démonstration.
