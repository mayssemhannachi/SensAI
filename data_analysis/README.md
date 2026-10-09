# SensAI — Data Analysis & espace thérapeute

Ce dossier contient la partie **Data Analysis** du projet SensAI / KineKids AI :

- `notebooks/` et `src/` : pipeline d’analyse des données synthétiques (chargement, nettoyage, intégration, KPI, progression) ;
- `dashboard/` : le **tableau de bord thérapeute** (Streamlit), connecté au backend FastAPI **ou** aux données de démonstration ;
- `scripts/seed_backend.py` : remplit le backend avec les données de démo, via l’API ;
- `tests/` : tests automatiques (calculs, contrat API, rendu de chaque page).

```
🎮 Jeux + Computer Vision → 📊 métriques → PostgreSQL → FastAPI → 📈 Dashboard → 👩‍⚕️ Thérapeute
                                                                    ↑
                                              data/ (CSV synthétiques, mode Démo)
```

## 1. Installation

Depuis le dossier `data_analysis` :

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## 2. Lancer l'espace thérapeute

**Toujours depuis le dossier `data_analysis`** (pour que le thème `.streamlit/config.toml` soit appliqué) :

```powershell
streamlit run dashboard/app.py
```

Le thérapeute n'ouvre pas cette adresse lui-même : il se connecte (ou s'inscrit) sur le site SensAI
(http://localhost:3000/login), qui le redirige ici déjà connecté. Une connexion directe reste possible
depuis la page d'accueil du dashboard.

Variables d'environnement optionnelles (ou fichier `.env`) :

```powershell
$env:KINEKIDS_API_URL = "http://127.0.0.1:8000"     # backend
$env:KINEKIDS_SITE_URL = "http://localhost:3000"    # site SensAI (liens connexion / déconnexion)
$env:KINEKIDS_DATA_SOURCE = "demo"                  # hors-ligne sur CSV synthétiques (développement)
```

## 3. Données de démonstration

```powershell
python scripts/seed_backend.py --register
```

Crée via l'API un thérapeute **demo@sensai.tn / demo1234**, 12 patients suivis au jeu Le Hibou
pendant ~8 semaines (profils variés : progression, douleur élevée, asymétrie, inactif…) et un compte
enfant **salma.parent@sensai.tn / demo1234**.

## 4. Pages

| Page | Contenu |
|------|---------|
| **Vue globale** | KPI comparés à la période précédente (7 j / 30 j / 90 j / tout), tendance hebdomadaire score & réussite, répartition des taux de réussite, réussite par jeu, **patients à surveiller** avec la raison de l’alerte, dernières séances |
| **Patients** | Recherche (nom, code), filtre par statut, tri, cartes avec mini-courbe du score, export CSV |
| **Fiche patient** | Statut et alertes, diagnostic, KPI, **KineKids Intelligence** (lecture automatique de l’historique), courbes réussite / score / progression / par jeu, avant-maintenant par jeu, historique exportable ; en mode Backend : ajout de diagnostic et **assignation de jeux** |
| **Jeux** | Réussite par jeu et par semaine, difficulté par niveau, matrice patients × jeux |
| **Nouveau patient** | Identité, diagnostic, jeu prescrit et ses réglages ; génère le code d’activation à remettre au patient |

### Règles d’analyse (modifiables dans `dashboard/utils/analytics.py`)

- **Douleur élevée** : douleur déclarée ≥ 4/5 à la dernière séance.
- **Réussite faible** : dernière séance < 40 % de réussite.
- **Score en baisse** : score moyen des 3 dernières séances ≥ 10 points sous celui des 5 précédentes.
- **Amplitude en baisse** : rotation moyenne des 3 dernières séances ≥ 3° sous celle des 5 précédentes.
- **Inactif** : aucune séance depuis plus de 14 jours.
- **Statut** : *À surveiller* (une alerte ci-dessus), *En progression* (score en hausse ou amplitude +2°), *Stable*, *Nouveau* (aucune séance).
- **Progression** : variation du score (%) par rapport à la séance précédente du même exercice ; calculée par le dashboard si le jeu ne l’envoie pas.

Ce sont des indicateurs d’aide à la décision, pas des critères diagnostiques.

## 5. Contrat de données attendu des jeux (`metrics` d’une session)

`POST /sessions/` avec `patient_game_id`, `duration_sec` et un objet `metrics` :

| Clé | Type | Obligatoire | Description |
|-----|------|-------------|-------------|
| `score` | nombre 0–100 | oui | Score de la séance |
| `success_rate` | nombre 0–100 (ou ratio 0–1) | oui | Taux de réussite |
| `repetitions` | entier | conseillé | Nombre de répétitions |
| `level_number` | entier | conseillé | Niveau de l’exercice |
| `exercise_name` | texte | conseillé | Nom de l’exercice |
| `played_at` | date ISO 8601 | optionnel | Date réelle de la séance (sinon `created_at`) |
| `progression` | nombre (%) | optionnel | Sinon calculée par le dashboard |

Alias acceptés : `reps`, `level`, `successRate`, `accuracy`, `name_exercise`, `session_date`.

## 6. Tests

```powershell
python -m pytest -q
```

32 tests : calculs d’analyse, normalisation des données API, contrat d’écriture vers l’API, rendu de chaque page et de chaque fiche patient en mode démo, écran de connexion.

## 7. Structure

```
dashboard/
├── app.py                 # point d’entrée : thème, menu, source de données, connexion, routage
├── navigation.py          # pages et navigation
├── pages/                 # global_view, patients, patient_detail, games, add_patient, login
├── components/            # ui (cartes, badges, KPI), charts (Plotly), patient_table
└── utils/
    ├── api_client.py      # client HTTP du backend + messages d’erreur
    ├── data.py            # sources Démo / Backend → même format normalisé
    ├── analytics.py       # calculs purs (KPI, tendances, alertes, insights)
    ├── state.py           # source de données, jeton, patient sélectionné
    └── theme.py           # design system (couleurs, CSS)
```

Les points qui relèvent du backend (et non du dashboard) sont listés dans `BACKEND_NOTES.md`.
