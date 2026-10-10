"use client";

// Le Gardien du Château — attention et contrôle des gestes (jeu de Chahed, ergothérapie).
// Le jeu (Phaser + MediaPipe, sources dans games-src/gardien-chateau) est compilé dans
// /games/gardien-chateau/ ; le cadre commun est EmbeddedGame.

import EmbeddedGame, { type EmbeddedGameSpec } from "./EmbeddedGame";
import { chateauConfig } from "@/lib/games";

type Config = ReturnType<typeof chateauConfig>;

export const CHATEAU_GESTURE_LABELS: Record<string, string> = {
  fairy_r: "🔵 Fée bleue (bras droit)",
  fairy_l: "💗 Fée rose (bras gauche)",
  star: "⭐ Étoile (les deux bras)",
  crown: "👑 Couronne (main sur la tête)",
  dragon: "🐉 Dragon (se baisser)",
};

const spec: EmbeddedGameSpec<Config> = {
  slug: "gardien-chateau",
  title: "Le Gardien du Château",
  image: "/Assets/dashboard/Girl Activates a Magical Portal.png",
  unit: "défis",
  config: chateauConfig,
  params: (c) => ({ gestes: c.gestures.join(","), essais: String(c.trials), go: String(c.go_percent) }),
  target: (c) => c.trials,
  subtitle: () => "Attention et contrôle des gestes · debout devant la caméra",
  badge: () => "👹 Gare à l’ogre !",
  doneTitle: "Bravo, le château est protégé ! 🏰",
  doneLine: (m, c) =>
    `${m.repetitions} / ${c.trials} défis · réussite ${m.success_rate ?? 0} % · statues réussies ${String(m.nogo_success_rate ?? 0)} %`,
};

export default function ChateauGame() {
  return <EmbeddedGame spec={spec} />;
}
