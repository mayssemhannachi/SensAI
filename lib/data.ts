// ──────────────────────────────────────────────────────────────────────────────
// Shared mock data store - in a real app this would be a database/API
// Both the patient dashboard and therapist dashboard read from this
// ──────────────────────────────────────────────────────────────────────────────

export type Session = {
  date: string;
  duration: string;
  gamesCompleted: string;
  score: number;
  status: "Complet" | "Partiel";
  painLevel: number;
  effort: number;
  rotationLeft: number;
  rotationRight: number;
};

export type Patient = {
  id: string;
  code: string;
  name: string;
  age: number;
  avatar: string;
  diagnosis: string;
  adherence: number;
  lastSession: string;
  lastSessionDuration: string;
  lastScore: number;
  lastSuccessRate: number;
  painLevel: number;
  // Le Hibou game stats
  targetAngle: number;
  targetHold: number;
  speedLimit: "Lente" | "Modérée" | "Rapide";
  difficulty: "Faible" | "Moyenne" | "Élevée";
  safetyLimit: number;
  sessions: Session[];
  activeGames: { title: string; category: string; image: string; status: "Actif" | "Inactif" }[];
};

// ─── PATIENT DATA (Salma / code 7F3A) ─────────────────────────────────────────
export const PATIENTS: Record<string, Patient> = {
  "7F3A-89K2": {
    id: "7F3A-89K2",
    code: "7F3A",
    name: "Salma",
    age: 8,
    avatar: "/Assets/dashboard/Playful Character Face Sticker Sheet.png",
    diagnosis: "Post-traumatic Neck Stiffness / Torticollis",
    adherence: 85,
    lastSession: "6 oct. 2026",
    lastSessionDuration: "15 min",
    lastScore: 420,
    lastSuccessRate: 92,
    painLevel: 4,
    targetAngle: 30,
    targetHold: 3,
    speedLimit: "Lente",
    difficulty: "Moyenne",
    safetyLimit: 35,
    sessions: [
      {
        date: "6 oct. 2026",
        duration: "15 min",
        gamesCompleted: "3 / 3",
        score: 420,
        status: "Complet",
        painLevel: 4,
        effort: 4,
        rotationLeft: 36,
        rotationRight: 46,
      },
      {
        date: "3 oct. 2026",
        duration: "14 min",
        gamesCompleted: "3 / 3",
        score: 398,
        status: "Complet",
        painLevel: 2,
        effort: 3,
        rotationLeft: 34,
        rotationRight: 42,
      },
      {
        date: "1 oct. 2026",
        duration: "12 min",
        gamesCompleted: "2 / 3",
        score: 310,
        status: "Partiel",
        painLevel: 3,
        effort: 3,
        rotationLeft: 30,
        rotationRight: 38,
      },
      {
        date: "29 sept. 2026",
        duration: "10 min",
        gamesCompleted: "3 / 3",
        score: 365,
        status: "Complet",
        painLevel: 1,
        effort: 2,
        rotationLeft: 28,
        rotationRight: 35,
      },
    ],
    activeGames: [
      {
        title: "Le Hibou",
        category: "Rotation cervicale",
        image: "/Assets/dashboard/Magical Owl Valley Adventure.png",
        status: "Actif",
      },
      {
        title: "Color Touch",
        category: "Précision",
        image: "/Assets/dashboard/Girl Activates a Magical Portal.png",
        status: "Actif",
      },
      {
        title: "Tremor Trace",
        category: "Contrôle du mouvement",
        image: "/Assets/dashboard/Chibi Sky Quest to the Star.png",
        status: "Actif",
      },
    ],
  },
};

// Helper to get a patient by their short code (e.g. "7F3A")
export function getPatientByShortCode(code: string): Patient | undefined {
  return Object.values(PATIENTS).find((p) => p.code === code);
}

// Helper to get a patient by their full code
export function getPatientByCode(code: string): Patient | undefined {
  return PATIENTS[code];
}

// Latest session stats (what appears on the patient dashboard)
export function getLatestSession(patient: Patient): Session | undefined {
  return patient.sessions[0];
}
