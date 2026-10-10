"use client";

// Le Gardien des Lucioles — élévation du bras / épaule (jeu de Maram, kinésithérapie).
// Le jeu tourne dans /games/gardien-lucioles/ ; le cadre commun est EmbeddedGame.

import EmbeddedGame, { type EmbeddedGameSpec } from "./EmbeddedGame";
import { luciolesConfig } from "@/lib/games";

type Config = ReturnType<typeof luciolesConfig>;

const EXERCISES: Record<string, string> = {
  side: "Abduction de l’épaule",
  front: "Flexion de l’épaule",
  mid: "Flexion-adduction de l’épaule",
  any: "Élévation du bras",
};

const spec: EmbeddedGameSpec<Config> = {
  slug: "gardien-lucioles",
  title: "Le Gardien des Lucioles",
  image: "/Assets/dashboard/Chibi Sky Quest to the Star.png",
  unit: "lucioles",
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
    `${EXERCISES[c.direction] ?? "Élévation du bras"} · ${
      c.affected_arm === "BI" ? "les deux bras" : c.affected_arm === "L" ? "bras gauche" : "bras droit"}`,
  badge: (c) => `🎯 ${c.target_angle}°`,
  doneTitle: "Bravo, toutes les lucioles sont rentrées ! 🎉",
  doneLine: (m, c) =>
    `${m.repetitions} / ${c.repetitions} lucioles · bras levé jusqu’à ${String(m.abduction_max ?? 0)}° · score ${m.score}`,
};

export default function LuciolesGame() {
  return <EmbeddedGame spec={spec} />;
}
