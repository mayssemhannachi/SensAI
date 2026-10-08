# KineKids AI — Data Analysis & Therapist Dashboard

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

## 2. Lancer le dashboard

**Toujours depuis le dossier `data_analysis`** (pour que le thème `.streamlit/config.toml` soit appliqué) :

```powershell
streamlit run dashboard/app.py
```

Le dashboard s’ouvre en **mode Démo** par défaut. La source de données se change à tout moment dans le menu de gauche (**Démo / Backend**) — aucun redémarrage nécessaire.

| Mode | Données | Usage |
|------|---------|-------|
| **Démo** | CSV synthétiques de `data/` (20 patients, 500 séances, 3 jeux) | Présentation sans backend, toujours fonctionnelle |
| **Backend** | API FastAPI KineKids AI, après connexion du thérapeute | Fonctionnement réel |

Variables d’environnement optionnelles (ou fichier `.env`) :

```powershell
$env:KINEKIDS_DATA_SOURCE = "api"                  # source au démarrage : demo (défaut) ou api
$env:KINEKIDS_API_URL = "http://127.0.0.1:8000"    # adresse du backend
```

## 3. Utiliser le mode Backend

1. Démarrer le backend (voir le README à la racine) : `uvicorn app.main:app --reload`.
2. (Première fois) remplir le backend avec les données de démo :

   ```powershell
   python scripts/seed_backend.py --email demo@kinekids.tn --password demo1234 --register
   ```

   Le script crée le compte thérapeute, le catalogue de jeux, les 20 patients, leurs diagnostics, leurs jeux assignés et les 500 séances. Il ignore les patients déjà présents.
3. Dans le dashboard, choisir **Backend** puis se connecter avec ce compte.

Le dashboard n’accède **jamais** directement à PostgreSQL : il passe uniquement par l’API avec le jeton Bearer obtenu à la connexion. Les données sont mises en cache 2 minutes (bouton **↻ Actualiser** pour forcer).

## 4. Pages

| Page | Contenu |
|------|---------|
| **Vue globale** | KPI comparés à la période précédente (7 j / 30 j / 90 j / tout), tendance hebdomadaire score & réussite, répartition des taux de réussite, réussite par jeu, **patients à surveiller** avec la raison de l’alerte, dernières séances |
| **Patients** | Recherche (nom, code), filtre par statut, tri, cartes avec mini-courbe du score, export CSV |
| **Fiche patient** | Statut et alertes, diagnostic, KPI, **KineKids Intelligence** (lecture automatique de l’historique), courbes réussite / score / progression / par jeu, avant-maintenant par jeu, historique exportable ; en mode Backend : ajout de diagnostic et **assignation de jeux** |
| **Jeux** | Réussite par jeu et par semaine, difficulté par niveau, matrice patients × jeux |
| **Ajouter un patient** | Création du profil (backend : code patient généré par l’API) |

### Règles d’analyse (modifiables dans `dashboard/utils/analytics.py`)

- **Réussite faible** : dernière séance < 40 % de réussite.
- **Score en baisse** : pente du score ≤ −1 point par séance sur les 5 dernières séances.
- **Inactif** : aucune séance depuis plus de 14 jours.
- **Statut** : *À surveiller* (réussite faible ou score en baisse), *En progression* (pente ≥ +1), *Stable*, *Nouveau* (aucune séance).
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
