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
    category: "Rotation cervicale",
    limb: "Tête / Cou",
    playable: true,
    path: "/dashboard/game/le-hibou",
  },
  "color-touch": { image: "/Assets/dashboard/ex-color-touch.png", category: "Jeu de couleur", limb: "Main droite" },
  "reaction-speed": { image: "/Assets/dashboard/ex-reaction-speed.png", category: "Jeu de rapidité", limb: "Main gauche" },
  "sequence-memory": { image: "/Assets/dashboard/ex-sequence-memory.png", category: "Jeu de mémoire", limb: "Œil / Vision" },
  "tremor-trace": { image: "/Assets/dashboard/ex-tremor-trace.png", category: "Jeu de précision", limb: "Main gauche" },
  "target-tracking": { image: "/Assets/dashboard/ex-target-tracking.png", category: "Jeu de suivi", limb: "Tête / Cou" },
  "balance-builder": { image: "/Assets/dashboard/ex-balance-builder.png", category: "Jeu d'équilibre", limb: "Jambe" },
  "puzzle-motion": { image: "/Assets/dashboard/ex-puzzle-motion.png", category: "Jeu de coordination", limb: "Corps entier" },
};

const FALLBACK_META: GameMeta = {
  image: "/Assets/dashboard/Magical Shape Quest with Friends.png",
  category: "Jeu de rééducation",
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

export function withDefaults(config?: GameConfig) {
  return { ...DEFAULT_CONFIG, ...(config || {}) };
}

export const SPEED_LABELS: Record<string, string> = { lente: "Lente", moderee: "Modérée", rapide: "Rapide" };
export const DIFFICULTY_LABELS: Record<string, string> = { faible: "Faible", moyenne: "Moyenne", elevee: "Élevée" };
export const DIFFICULTY_LEVEL: Record<string, number> = { faible: 1, moyenne: 2, elevee: 3 };

// ─── Aides de calcul sur les séances ─────────────────────────────────────────
export function sessionDate(session: GameSession): Date {
  const raw = (session.metrics?.played_at as string) || session.created_at;
  // created_at du backend est en UTC sans fuseau
  return new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(raw) ? raw : `${raw}Z`);
}

export function sortByDateDesc(sessions: GameSession[]): GameSession[] {
  return [...sessions].sort((a, b) => sessionDate(b).getTime() - sessionDate(a).getTime());
}

export function formatDate(date: Date, withTime = false): string {
  return date.toLocaleDateString("fr-FR", {
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
