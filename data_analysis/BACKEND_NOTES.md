# Notes pour l’équipe Backend

Le dashboard thérapeute (partie Data Analysis) est **entièrement fonctionnel avec l’API actuelle** :
connexion, liste des patients, séances, jeux, création de patient, diagnostic et assignation de jeux ont
été testés de bout en bout contre la branche `backend-fastapi` (PostgreSQL + migrations Alembic).

Sur la branche publiée `feature/dashboard-analytics`, aucun fichier du backend n’a été modifié.
La branche locale `local/back-connecte` propose une implémentation des points 1 à 3 ci-dessous,
plus les comptes patients (`POST /auth/activate`, routes `/me/*`) et `PUT /patient-games/{id}`
(voir le `README.md` à la racine). L’équipe backend peut la reprendre ou s’en inspirer. Les points ci-dessous relèvent du backend ; ils sont classés
par impact sur le dashboard et contournés côté dashboard en attendant.

## À traiter en priorité

| # | Constat | Impact | Contournement actuel | Proposition |
|---|---------|--------|----------------------|-------------|
| 1 | Pas de route de **lecture des consultations** (seulement `POST /consultations/`) | Le diagnostic d’un patient ne peut pas être affiché après rechargement | Le diagnostic saisi pendant la session est affiché ; message explicatif dans la fiche | `GET /consultations/patient/{patient_id}` (liste triée par date) |
| 2 | `GET /patients/code/{patient_code}` ne vérifie pas que le patient appartient au thérapeute connecté | **Sécurité** : tout compte authentifié peut lire n’importe quel patient s’il connaît son code | Le dashboard n’utilise pas cette route | Filtrer sur `therapist_id == current_user["user_id"]` (comme `get_patient`) |
| 3 | `created_at` d’une session est toujours la date d’enregistrement | Impossible d’importer un historique ou d’enregistrer une séance jouée hors ligne avec sa vraie date | Le dashboard lit `metrics.played_at` en priorité | Champ optionnel `played_at` dans `SessionCreate` |
| 4 | Pas de route listant **toutes les séances du thérapeute** | Le dashboard fait 1 + N patients + M associations appels (parallélisés, mis en cache 2 min) | Appels parallèles + cache | `GET /sessions/?from=&to=` filtré sur le thérapeute connecté |

## Contrat `metrics` à figer avec l’équipe Jeux

`metrics` est un JSON libre. Le dashboard attend (détails dans `README.md`, §5) :
`score` (0–100), `success_rate` (0–100), `repetitions`, `level_number`, `exercise_name`, et optionnellement
`played_at` et `progression`. Une validation Pydantic de ces clés côté API éviterait des séances inexploitables.

## Autres remarques

- `POST /consultations` est déclarée deux fois (`""` et `"/"`) : doublon dans Swagger.
- `POST /games/` est accessible à tout utilisateur authentifié (pas de contrôle de rôle).
- Le jeton expire après 60 min : le dashboard renvoie alors proprement vers l’écran de connexion.
- `requirements.txt` à la racine est encodé en UTF-16 : à convertir en UTF-8 pour éviter des erreurs `pip` hors Windows.
- `GET /auth/me` renvoie l’e-mail mais pas le nom complet du thérapeute (le dashboard affiche l’e-mail).
