"use client";

// Le Gardien des Lucioles — élévation du bras / épaule (jeu de Maram, kinésithérapie).
// Le jeu tourne dans /games/gardien-lucioles/ ; le cadre commun est EmbeddedGame.

import EmbeddedGame, { type EmbeddedGameSpec } from "./EmbeddedGame";
import { luciolesConfig } from "@/lib/games";

type Config = ReturnType<typeof luciolesConfig>;

const EXERCISES: Record<string, string> = {
  side: "Shoulder Abduction",
  front: "Shoulder Flexion",
  mid: "Shoulder Flexion-Adduction",
  any: "Arm Elevation",
};

const spec: EmbeddedGameSpec<Config> = {
  slug: "gardien-lucioles",
  title: "Firefly Guardian",
  image: "/Assets/dashboard/Chibi Sky Quest to the Star.png",
  unit: "fireflies",
  config: luciolesConfig,
  params: (c) => ({
    side: c.affected_arm,
    dir: c.direction,
    thr: String(c.target_angle),
    elb: String(c.elbow_min),
    rest: String(c.rest_tolerance),
    reps: String(c.repetitions),
    hold: String(c.hold_seconds),
  }),
  target: (c) => c.repetitions,
  subtitle: (c) =>
    `${EXERCISES[c.direction] ?? "Arm Elevation"} · ${
      c.affected_arm === "BI" ? "both arms" : c.affected_arm === "L" ? "left arm" : "right arm"}`,
  badge: (c) => `🎯 ${c.target_angle}°`,
  doneTitle: "Great job, all the fireflies are home! 🎉",
  doneLine: (m, c) =>
    `${m.repetitions} / ${c.repetitions} fireflies · arm raised up to ${String(m.abduction_max ?? 0)}° · score ${m.score}`,
};

export default function LuciolesGame() {
  return <EmbeddedGame spec={spec} />;
}
