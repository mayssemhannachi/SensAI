"use client";

// Le Gardien du Château — attention et contrôle des gestes (jeu de Chahed, ergothérapie).
// Le jeu (Phaser + MediaPipe, sources dans games-src/gardien-chateau) est compilé dans
// /games/gardien-chateau/ ; le cadre commun est EmbeddedGame.

import EmbeddedGame, { type EmbeddedGameSpec } from "./EmbeddedGame";
import { chateauConfig } from "@/lib/games";

type Config = ReturnType<typeof chateauConfig>;

export const CHATEAU_GESTURE_LABELS: Record<string, string> = {
  fairy_r: "🔵 Blue fairy (right arm)",
  fairy_l: "💗 Pink fairy (left arm)",
  star: "⭐ Star (both arms)",
  crown: "👑 Crown (hand on head)",
  dragon: "🐉 Dragon (duck down)",
};

const spec: EmbeddedGameSpec<Config> = {
  slug: "gardien-chateau",
  title: "Guardian of the Castle",
  image: "/Assets/gardien chateau/Whimsical Purple Castle Icon.png",
  unit: "challenges",
  config: chateauConfig,
  params: (c) => ({ gestes: c.gestures.join(","), essais: String(c.trials), go: String(c.go_percent) }),
  target: (c) => c.trials,
  subtitle: () => "Attention and movement control · standing in front of the camera",
  badge: () => "🐻 Beware of the ogre!",
  doneTitle: "Well done, the castle is safe! 🏰",
  doneLine: (m, c) =>
    `${m.repetitions} / ${c.trials} challenges · ${m.success_rate ?? 0}% success · statues: ${String(m.nogo_success_rate ?? 0)}%`,
};

export default function ChateauGame() {
  return <EmbeddedGame spec={spec} />;
}
