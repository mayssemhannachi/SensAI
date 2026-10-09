# SensAI — rééducation motrice pédiatrique par le jeu

Des **jeux de rééducation** pilotés par la **webcam** (vision par ordinateur, MediaPipe)
pour les enfants, et un **espace thérapeute** qui prescrit les jeux, règle chaque exercice
et analyse la progression de chaque enfant.

Ce dépôt contient **toute la plateforme, déjà connectée** : backend, base de données, site,
jeux et dashboard thérapeute. Après le clonage, il suffit de suivre les étapes ci-dessous :
aucune modification de code n'est nécessaire.

---

## Sommaire

1. [Ce qu'il faut installer avant](#1-ce-quil-faut-installer-avant)
2. [Installation (une seule fois)](#2-installation-une-seule-fois)
3. [Lancer la plateforme](#3-lancer-la-plateforme)
4. [Le parcours complet](#4-le-parcours-complet)
5. [Architecture](#5-architecture)
6. [Structure du dépôt](#6-structure-du-dépôt)
7. [Installation manuelle (sans les scripts)](#7-installation-manuelle-sans-les-scripts)
8. [Problèmes fréquents](#8-problèmes-fréquents)
9. [Ajouter un nouveau jeu](#9-ajouter-un-nouveau-jeu)
10. [Équipe](#10-équipe)

---

## 1. Ce qu'il faut installer avant

| Outil | Version | Lien | Remarque |
|-------|---------|------|----------|
| **Git** | récente | https://git-scm.com/downloads | pour cloner le dépôt |
| **Python** | 3.11 ou plus (3.13 conseillé) | https://www.python.org/downloads/ | Windows : cocher **« Add python.exe to PATH »** |
| **Node.js** | 20 LTS ou plus (22 conseillé) | https://nodejs.org | version **LTS** |
| **PostgreSQL** | 14 ou plus (16 conseillé) | https://www.postgresql.org/download/ | **retenir le mot de passe** de l'utilisateur `postgres` choisi pendant l'installation |

Une **webcam** et une **connexion Internet** sont nécessaires pour jouer avec la caméra
(les modèles de détection sont téléchargés au lancement du jeu). Sans caméra, les jeux
se jouent aussi **au clavier**.

---

## 2. Installation (une seule fois)

```powershell
git clone -b integration/plateforme-complete https://github.com/mayssemhannachi/SensAI.git
cd SensAI
```

Puis :

- **Windows** : double-cliquer sur **`installer.bat`**
- **Mac / Linux** : `./installer.sh`

Le script demande le **mot de passe PostgreSQL**, puis fait tout le reste :

| Étape | Ce qui est fait |
|-------|-----------------|
| 1 | vérifie Python et Node.js |
| 2 | crée l'environnement Python `.venv` et installe les dépendances (backend + dashboard) |
| 3 | crée le fichier `.env` (connexion à la base + clé secrète aléatoire), crée la base `sensai_db` et ses tables |
| 4 | installe les dépendances du site (`frontend/`) et crée `frontend/.env.local` |
| 5 | crée le **compte de démonstration** (thérapeute + 15 patients avec ~8 semaines de séances) |

Comptez **5 à 10 minutes** la première fois. Le script peut être relancé sans risque :
il ne refait que ce qui manque.

---

## 3. Lancer la plateforme

- **Windows** : double-cliquer sur **`demarrer.bat`**
  → trois fenêtres s'ouvrent (backend, dashboard, site) puis le navigateur s'ouvre sur le site.
  Pour arrêter : fermer les trois fenêtres « SensAI - … ».
- **Mac / Linux** : `./demarrer.sh` → `Ctrl + C` pour tout arrêter.

On n'ouvre qu'**une seule adresse : http://localhost:3000**. Le site envoie chacun au bon endroit.

| Service | Adresse | Rôle |
|---------|---------|------|
| Site SensAI | http://localhost:3000 | accueil, connexion, inscription, espace enfant, jeux |
| Dashboard thérapeute | http://localhost:8501 | patients, prescription des jeux, analyses (ouvert automatiquement après la connexion) |
| API (backend) | http://127.0.0.1:8000/docs | documentation interactive de l'API |

### Comptes de démonstration

| Rôle | E-mail | Mot de passe |
|------|--------|--------------|
| Thérapeute (15 patients suivis) | `demo@sensai.tn` | `demo1234` |
| Parent de Salma (2 jeux attribués) | `salma.parent@sensai.tn` | `demo1234` |

---

## 4. Le parcours complet

```
 Thérapeute                         Parent / enfant                      Thérapeute
 ──────────                         ───────────────                      ──────────
 /login → son dashboard             /login → « Activer mon compte »      ↻ Actualiser
 « Nouveau patient » :              code + e-mail + mot de passe         la séance apparaît :
  identité, diagnostic,      code    → espace de l'enfant         séance  scores, amplitude,
  jeu prescrit + réglages   ──────►  → joue (caméra ou clavier) ───────►  compensations,
  → code d'activation                → douleur / effort ressentis         douleur, alertes
```

1. **Une seule page de connexion** pour tout le monde. Un thérapeute arrive sur son dashboard,
   un parent arrive dans l'espace de son enfant.
2. **Le thérapeute** crée un compte (`/register`), puis un patient avec son diagnostic, le jeu
   prescrit et ses réglages. Un **code d'activation à 6 caractères** est généré
   (valable 30 jours, utilisable une seule fois).
3. **Le parent** active le compte de l'enfant avec ce code (lien « Activer mon compte » sur la
   page de connexion). Il ne voit que les données de son enfant : c'est le backend qui le garantit.
4. **L'enfant joue** chez lui. À la fin, il indique sa douleur et son effort, et la séance est
   envoyée automatiquement.
5. **Le thérapeute** retrouve la séance et ses analyses dans le dashboard, et peut modifier les
   réglages à tout moment.

### Les jeux disponibles

| Jeu | Mouvement | Réglages du thérapeute | Mesures analysées |
|-----|-----------|------------------------|-------------------|
| **Le Hibou** | rotation cervicale (tête) | angle cible, maintien, répétitions, vitesse, limite de sécurité, sensibilité caméra, inversion du sens | rotation gauche / droite, symétrie, maintien, fluidité, compensations (tête penchée) |
| **Le Gardien des Lucioles** | abduction de l'épaule (bras) | bras atteint, mode hémiplégie / bilatéral, seuil d'abduction, extension du coude, tolérance de l'autre bras, nombre de lucioles, maintien | abduction max, pic moyen, compensations (autre bras levé) |

Les deux jeux enregistrent aussi le score, le taux de réussite, la durée, la **douleur** et
l'**effort** déclarés par l'enfant. Le bouton **« J'ai mal / Stop »** arrête la séance à tout moment.

---

## 5. Architecture

```
┌──────────────────────────┐      ┌─────────────────────────┐      ┌──────────────┐
│ Site SensAI (Next.js)    │ JWT  │ API FastAPI             │ SQL  │ PostgreSQL   │
│ frontend/  :3000         │─────►│ app/  :8000             │─────►│ sensai_db    │
│ connexion, espace enfant,│      │ comptes, patients, jeux,│      └──────────────┘
│ jeux + MediaPipe (webcam)│      │ réglages, séances       │
└────────────┬─────────────┘      └────────────▲────────────┘
             │ connexion unique (jeton)        │ JWT
             ▼                                 │
┌──────────────────────────────────────────────┴──┐
│ Dashboard thérapeute (Streamlit)  data_analysis/ │
│ :8501 — patients, prescription, analyses, alertes│
└──────────────────────────────────────────────────┘
```

- **Backend** : FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, authentification JWT, rôles
  `therapist` et `patient`.
- **Site** : Next.js 16, React 19, Tailwind 4. Le jeu Le Gardien des Lucioles utilise
  Phaser + MediaPipe Pose, Le Hibou utilise MediaPipe FaceMesh.
- **Dashboard** : Streamlit, pandas, Plotly. Détails, règles d'analyse et contrat de données
  des jeux : [`data_analysis/README.md`](data_analysis/README.md).

---

## 6. Structure du dépôt

```
SensAI/
├── installer.bat / installer.sh   # installation en une commande
├── demarrer.bat  / demarrer.sh    # lancement des 3 services
├── scripts/                       # installer.py, demarrer.py (logique des deux commandes)
├── app/                           # backend FastAPI (routes, modèles, services)
├── alembic/                       # migrations de la base (tables + catalogue de jeux)
├── requirements.txt               # dépendances du backend
├── .env.example                   # modèle de configuration (le vrai .env est créé par l'installateur)
├── data_analysis/                 # dashboard thérapeute, analyses, notebooks, tests
│   └── scripts/seed_backend.py    # données de démonstration
├── frontend/                      # site SensAI (Next.js) + jeux
│   └── public/games/gardien-lucioles/   # jeu Le Gardien des Lucioles
└── docs/README_backend.md         # documentation détaillée du backend
```

Les fichiers `.env`, `.venv/`, `frontend/node_modules/` et `frontend/.env.local` sont créés
sur chaque ordinateur et **ne sont jamais publiés** (ils sont dans `.gitignore`).

---

## 7. Installation manuelle (sans les scripts)

<details>
<summary>Afficher les commandes (Windows PowerShell)</summary>

```powershell
# 1. Backend + dashboard
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r data_analysis\requirements.txt
Copy-Item .env.example .env      # puis remplacer YOUR_PASSWORD, kinekids_db et SECRET_KEY
# créer la base indiquée dans .env (pgAdmin ou : psql -U postgres -c "CREATE DATABASE sensai_db;")
python -m alembic upgrade head

# 2. Site
cd frontend
npm install
Copy-Item .env.example .env.local
cd ..

# 3. Lancer (3 terminaux, .venv activé pour les deux premiers)
uvicorn app.main:app --port 8000                                   # terminal 1, à la racine
cd data_analysis; streamlit run dashboard/app.py                   # terminal 2
cd frontend; npm run dev                                           # terminal 3

# 4. Données de démonstration (backend lancé)
cd data_analysis; python scripts/seed_backend.py --register
```
</details>

---

## 8. Problèmes fréquents

| Problème | Solution |
|----------|----------|
| `Connexion à PostgreSQL impossible` | PostgreSQL n'est pas démarré (Windows : Services → `postgresql-x64-…` → Démarrer) ou le mot de passe est faux. Supprimer `.env` et relancer `installer.bat`. |
| `Python n'est pas installé` | Réinstaller Python en cochant **Add python.exe to PATH**. |
| `Node.js n'est pas installé` | Installer Node.js LTS, puis **fermer et rouvrir** la fenêtre. |
| Une fenêtre « SensAI - … » affiche une erreur | Lire le message, puis la fermer et relancer `demarrer.bat`. Un port déjà utilisé signifie que le service tourne déjà. |
| La caméra ne démarre pas | Autoriser la caméra dans le navigateur, vérifier la connexion Internet, fermer les autres applications qui utilisent la webcam. Sinon, jouer au clavier. |
| Le hibou tourne dans le mauvais sens | Dashboard → fiche du patient → Jeux et réglages → activer « Inverser le sens de rotation ». |
| Après une mise à jour (`git pull`) | Relancer `installer.bat` : il applique les nouvelles migrations et dépendances. |
| Repartir d'une base vide | Supprimer la base `sensai_db` (pgAdmin), puis relancer `installer.bat`. |

---

## 9. Ajouter un nouveau jeu

1. **Backend** : une migration Alembic qui ajoute le jeu (nom, slug) dans la table `games`.
2. **Site** : une page `frontend/app/dashboard/game/<slug>/` ; déclarer le jeu dans
   `frontend/lib/games.ts` (`playable: true`). Le jeu lit ses réglages avec `GET /me/games`
   et envoie la séance avec `POST /me/sessions`.
3. **Dashboard** : ajouter le slug dans `PLAYABLE_GAME_SLUGS` et ses réglages par défaut dans
   `data_analysis/dashboard/utils/data.py`, ses champs dans
   `data_analysis/dashboard/components/game_settings.py`, sa section d'analyse dans
   `data_analysis/dashboard/pages/patient_detail.py`.

Le détail des mesures attendues est dans [`data_analysis/README.md`](data_analysis/README.md).

---

## 10. Équipe

| Partie | Contribution |
|--------|--------------|
| Site SensAI (UI / UX) | Mayssem — branche `sensAI-ui` |
| Backend FastAPI | branche `backend-fastapi` |
| Jeu Le Gardien des Lucioles | Maram — branche `maram-game` |
| Jeu Le Hibou (prototype Python / OpenCV) | Chahed — branche `feature/game-hibou` |
| Data Analysis & dashboard thérapeute, intégration de la plateforme | branche `feature/dashboard-analytics` |

Cette branche (`integration/plateforme-complete`) rassemble toutes les parties connectées.
Les branches de chacun restent inchangées.
