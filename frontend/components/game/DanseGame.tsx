"use client";

// La Danse des Lucioles — mémoire de séquence et coordination (jeu de Maram, ergothérapie).
// Le jeu tourne dans /games/danse-lucioles/ ; le cadre commun est EmbeddedGame.

import EmbeddedGame, { type EmbeddedGameSpec } from "./EmbeddedGame";
import { danseConfig } from "@/lib/games";

type Config = ReturnType<typeof danseConfig>;

const HANDS: Record<string, string> = {
  R: "main droite",
  L: "main gauche",
  any: "main au choix",
  alt: "les deux mains à tour de rôle",
};
const LEVELS: Record<string, string> = { easy: "facile", mid: "moyen", hard: "difficile" };

const spec: EmbeddedGameSpec<Config> = {
  slug: "danse-lucioles",
  title: "La Danse des Lucioles",
  image: "/Assets/dashboard/Magical Shape Quest with Friends.png",
  unit: "danses",
  config: danseConfig,
  params: (c) => ({ hand: c.hand_mode, level: c.level, reps: String(c.repetitions), size: c.target_size }),
  target: (c) => c.repetitions,
  subtitle: (c) => `Mémoire et coordination · ${HANDS[c.hand_mode] ?? "main au choix"}`,
  badge: (c) => `🌸 Niveau ${LEVELS[c.level] ?? "facile"}`,
  doneTitle: "Bravo, toutes les danses sont réussies ! 🎉",
  doneLine: (m, c) =>
    `${m.repetitions} / ${c.repetitions} danses · plus longue : ${String(m.max_sequence ?? 0)} fleurs · score ${m.score}`,
};

export default function DanseGame() {
  return <EmbeddedGame spec={spec} />;
}
