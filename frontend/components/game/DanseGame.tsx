"use client";

// La Danse des Lucioles — mémoire de séquence et coordination (jeu de Maram, ergothérapie).
// Le jeu tourne dans /games/danse-lucioles/ ; le cadre commun est EmbeddedGame.

import EmbeddedGame, { type EmbeddedGameSpec } from "./EmbeddedGame";
import { danseConfig } from "@/lib/games";

type Config = ReturnType<typeof danseConfig>;

const HANDS: Record<string, string> = {
  R: "right hand",
  L: "left hand",
  any: "either hand",
  alt: "alternating hands",
};
const LEVELS: Record<string, string> = { easy: "easy", mid: "medium", hard: "hard" };

const spec: EmbeddedGameSpec<Config> = {
  slug: "danse-lucioles",
  title: "Firefly Dance",
  image: "/Assets/dashboard/Magical Shape Quest with Friends.png",
  unit: "dances",
  config: danseConfig,
  params: (c) => ({ hand: c.hand_mode, level: c.level, reps: String(c.repetitions), size: c.target_size }),
  target: (c) => c.repetitions,
  subtitle: (c) => `Memory & coordination · ${HANDS[c.hand_mode] ?? "either hand"}`,
  badge: (c) => `🌸 Level: ${LEVELS[c.level] ?? "easy"}`,
  doneTitle: "Great job, all dances completed! 🎉",
  doneLine: (m, c) =>
    `${m.repetitions} / ${c.repetitions} dances · longest sequence: ${String(m.max_sequence ?? 0)} flowers · score ${m.score}`,
};

export default function DanseGame() {
  return <EmbeddedGame spec={spec} />;
}
