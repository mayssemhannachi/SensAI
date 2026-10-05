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

La connexion à l’API FastAPI/PostgreSQL sera intégrée après confirmation du contrat des routes et des métriques des jeux. Le dashboard ne se connecte pas directement à PostgreSQL.

## Navigation actuelle

- Vue globale : indicateurs filtrables par période, graphiques, signaux à revoir et séances récentes.
- Patients : recherche et accès aux fiches.
- Fiche patient : historique, indicateurs et diagnostic.
- Ajouter un patient : création d’un profil de démonstration.
