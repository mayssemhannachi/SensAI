# Le Gardien du Château — v0.1 (prototype)

Jeu de mouvement à la webcam (Phaser + MediaPipe Pose + TypeScript/Vite).
Fée bleue = bras droit, fée rose = bras gauche, ennemi = statue.

## Démarrer
1. `npm install` (copie aussi les fichiers wasm de MediaPipe dans `public/mediapipe/wasm`).
2. Télécharger `pose_landmarker_lite.task` (page officielle MediaPipe « Pose Landmarker »)
   et le placer dans `public/models/`. Hébergé chez vous, le jeu marche hors ligne.
3. `npm run dev`, ouvrir dans Chrome, autoriser la caméra. `npm test` pour les tests de la logique.

## Structure
- `src/core/` : logique pure testée sans caméra (gestes, mesures, difficulté adaptative).
- `src/pose/tracker.ts` : enveloppe MediaPipe.
- `src/game/MainScene.ts` : scène Phaser (calibrage, essais, bilan, copie JSON).

## Non fait / non vérifié
- Jamais exécuté avec une vraie caméra ni sur des enfants ; `npm install` et les tests n'ont pas été lancés.
- Seuils (`gestures.ts`) et marges à calibrer sur des enfants de 6 à 10 ans.
- Absents : consentement, boutons d'effacement, envoi à la plateforme, comptes, accessibilité, sons.
- Mesures indicatives, sans validation clinique ni autorisation. Ne pas présenter comme test ou traitement.
