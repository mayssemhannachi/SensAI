// Présentation des jeux SensAI (image, catégorie…) et réglages par défaut.
// Les jeux eux-mêmes viennent du backend (GET /games/) ; on les relie ici par leur slug.

import type { GameConfig, GameSession, PatientGame } from "./api";

export type GameMeta = {
  image: string;
  category: string;
  limb: string;
  playable?: boolean; // un jeu réellement jouable existe dans le site
  path?: string;
};

export const GAME_META: Record<string, GameMeta> = {
  "le-hibou": {
    image: "/Assets/dashboard/Magical Owl Valley Adventure.png",
    category: "Cervical Rotation",
    limb: "Head / Neck",
    playable: true,
    path: "/dashboard/game/le-hibou",
  },
  "gardien-lucioles": {
    image: "/Assets/dashboard/Chibi Sky Quest to the Star.png",
    category: "Shoulder Abduction",
    limb: "Shoulder / Arm",
    playable: true,
    path: "/dashboard/game/gardien-lucioles",
  },
  "danse-lucioles": {
    image: "/Assets/dashboard/Magical Shape Quest with Friends.png",
    category: "Memory & Coordination",
    limb: "Hands / Arms",
    playable: true,
    path: "/dashboard/game/danse-lucioles",
  },
  "gardien-chateau": {
    image: "/Assets/gardien chateau/Whimsical Purple Castle Icon.png",
    category: "Attention & Gesture Control",
    limb: "Whole Body",
    playable: true,
    path: "/dashboard/game/gardien-chateau",
  },
  "color-touch": { image: "/Assets/dashboard/Girl Activates a Magical Portal.png", category: "Color Game", limb: "Right Hand" },
  "reaction-speed": { image: "/Assets/dashboard/Kawaii Cosmic Ring Adventure.png", category: "Speed Game", limb: "Left Hand" },
  "sequence-memory": { image: "/Assets/dashboard/Magical Shape Quest with Friends.png", category: "Memory Game", limb: "Eye / Vision" },
  "tremor-trace": { image: "/Assets/dashboard/Chibi Sky Quest to the Star.png", category: "Precision Game", limb: "Left Hand" },
  "target-tracking": { image: "/Assets/dashboard/Whimsical Starry Meadow Archery.png", category: "Tracking Game", limb: "Head / Neck" },
  "balance-builder": { image: "/Assets/dashboard/Balancing Star in a Whimsical Meadow.png", category: "Balance Game", limb: "Leg" },
  "puzzle-motion": { image: "/Assets/dashboard/Kawaii Puzzle Play in Dreamy Park.png", category: "Coordination Game", limb: "Whole Body" },
};

const FALLBACK_META: GameMeta = {
  image: "/Assets/dashboard/Magical Shape Quest with Friends.png",
  category: "Rehabilitation Game",
  limb: "—",
};

export function gameMeta(slug?: string | null): GameMeta {
  return (slug && GAME_META[slug]) || FALLBACK_META;
}

export const DEFAULT_CONFIG: Required<Pick<GameConfig,
  "target_angle" | "hold_seconds" | "repetitions" | "speed" | "difficulty" | "safety_limit" | "active">> = {
  target_angle: 30,
  hold_seconds: 3,
  repetitions: 6,
  speed: "lente",
  difficulty: "moyenne",
  safety_limit: 35,
  active: true,
};

export const LUCIOLES_DEFAULTS = {
  affected_arm: "R" as "R" | "L" | "BI",
  mode: "hemi" as "hemi" | "bi",
  direction: "side" as "side" | "front" | "mid" | "any",
  target_angle: 90,
  elbow_min: 140,
  rest_tolerance: 35,
  repetitions: 10,
  hold_seconds: 1,
  active: true,
};

export function luciolesConfig(config?: GameConfig) {
  return { ...LUCIOLES_DEFAULTS, ...(config || {}) } as typeof LUCIOLES_DEFAULTS;
}

export const DANSE_DEFAULTS = {
  hand_mode: "any" as "R" | "L" | "any" | "alt",
  level: "easy" as "easy" | "mid" | "hard",
  repetitions: 5,
  target_size: "big" as "big" | "mid" | "small",
  active: true,
};

export function danseConfig(config?: GameConfig) {
  return { ...DANSE_DEFAULTS, ...(config || {}) } as typeof DANSE_DEFAULTS;
}

// Castle Guardian game
export const CHATEAU_GESTURES = ["fairy_r", "fairy_l", "star", "crown", "dragon"] as const;
export const CHATEAU_DEFAULTS = {
  gestures: ["fairy_r", "fairy_l", "star"] as string[],
  trials: 40,
  go_percent: 80,
  active: true,
};

export function chateauConfig(config?: GameConfig) {
  const merged = { ...CHATEAU_DEFAULTS, ...(config || {}) } as typeof CHATEAU_DEFAULTS;
  const gestures = Array.isArray(merged.gestures)
    ? merged.gestures.filter((g) => (CHATEAU_GESTURES as readonly string[]).includes(g))
    : [];
  return { ...merged, gestures: gestures.length === 3 ? gestures : CHATEAU_DEFAULTS.gestures };
}

export function withDefaults(config?: GameConfig) {
  return { ...DEFAULT_CONFIG, ...(config || {}) };
}

export const SPEED_LABELS: Record<string, string> = { lente: "Slow", moderee: "Moderate", rapide: "Fast" };
export const DIFFICULTY_LABELS: Record<string, string> = { faible: "Low", moyenne: "Medium", elevee: "High" };
export const DIFFICULTY_LEVEL: Record<string, number> = { faible: 1, moyenne: 2, elevee: 3 };

// ─── Session calculation helpers ─────────────────────────────────────────
export function sessionDate(session: GameSession): Date {
  const raw = (session.metrics?.played_at as string) || session.created_at;
  return new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(raw) ? raw : `${raw}Z`);
}

export function sortByDateDesc(sessions: GameSession[]): GameSession[] {
  return [...sessions].sort((a, b) => sessionDate(b).getTime() - sessionDate(a).getTime());
}

export function formatDate(date: Date, withTime = false): string {
  return date.toLocaleDateString("en-US", {
    day: "numeric",
    month: withTime ? "long" : "short",
    year: "numeric",
    ...(withTime ? { hour: "2-digit", minute: "2-digit" } : {}),
  });
}

export function formatDuration(seconds: number): string {
  if (!seconds) return "—";
  const minutes = Math.floor(seconds / 60);
  const rest = Math.round(seconds % 60);
  return minutes ? `${minutes} min${rest ? ` ${rest} s` : ""}` : `${rest} s`;
}

/** Séances des 7 derniers jours rapportées à l'objectif hebdomadaire (3 par défaut). */
export function adherence(sessions: GameSession[], perWeek = 3): number {
  const weekAgo = Date.now() - 7 * 24 * 3600 * 1000;
  const recent = sessions.filter((s) => sessionDate(s).getTime() >= weekAgo).length;
  return Math.min(100, Math.round((recent / perWeek) * 100));
}

/** Niveau ludique : un niveau toutes les 6 séances réussies. */
export function playerLevel(sessions: GameSession[]) {
  const done = sessions.filter((s) => s.metrics?.completed !== false).length;
  return { level: 1 + Math.floor(done / 6), progress: done % 6, step: 6 };
}

export function activeGames(games: PatientGame[]): PatientGame[] {
  return games.filter((g) => g.configuration?.active !== false);
}
