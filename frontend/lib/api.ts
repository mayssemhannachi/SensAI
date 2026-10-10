// ──────────────────────────────────────────────────────────────────────────────
// Client de l'API FastAPI KineKids / SensAI
// Toutes les données réelles (comptes, patients, jeux, séances) passent ici.
// ──────────────────────────────────────────────────────────────────────────────

export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
export const ANALYTICS_URL = process.env.NEXT_PUBLIC_DASHBOARD_URL || "http://localhost:8501";

const TOKEN_KEY = "sensai_token";
const ROLE_KEY = "sensai_role";

export type Role = "therapist" | "patient";
export type TherapistSpecialty = "kinesitherapist" | "ergotherapist";

// ─── Types renvoyés par l'API ────────────────────────────────────────────────
export type Me = {
  user_id: number;
  sub: string;
  role: Role;
  full_name?: string | null;
  patient_id?: number | null;
  specialty?: TherapistSpecialty | null;
};
export type Patient = {
  id: number;
  first_name: string;
  last_name: string;
  age: number;
  patient_code: string;
  therapist_id: number;
  created_at: string;
};
export type Game = { id: number; name: string; slug: string; description?: string | null };
export type GameConfig = {
  target_angle?: number;
  hold_seconds?: number;
  repetitions?: number;
  speed?: "lente" | "moderee" | "rapide";
  difficulty?: "faible" | "moyenne" | "elevee";
  safety_limit?: number;
  active?: boolean;
  // Le Hibou : réglages de la caméra
  camera_gain?: number;
  invert_direction?: boolean;
  shoulder_threshold?: number;
  // Le Gardien des Lucioles (abduction de l'épaule)
  affected_arm?: "R" | "L" | "BI";
  mode?: "hemi" | "bi";
  direction?: "side" | "front" | "mid" | "any";
  elbow_min?: number;
  rest_tolerance?: number;
  [key: string]: unknown;
};
export type PatientGame = {
  id: number;
  patient_id: number;
  game_id: number;
  configuration: GameConfig;
  game_name?: string | null;
  game_slug?: string | null;
};
export type SessionMetrics = {
  score?: number;
  success_rate?: number;
  repetitions?: number;
  repetitions_target?: number;
  level_number?: number;
  exercise_name?: string;
  played_at?: string;
  rotation_left?: number;
  rotation_right?: number;
  hold_seconds_avg?: number;
  smoothness?: number;
  pain_level?: number;
  effort?: number;
  completed?: boolean;
  [key: string]: unknown;
};
export type GameSession = {
  id: number;
  patient_game_id: number;
  duration_sec: number;
  metrics: SessionMetrics;
  created_at: string;
  game_id?: number;
  game_name?: string | null;
  game_slug?: string | null;
};
export type Consultation = { id: number; patient_id: number; consultation_date: string; diagnosis: string | null };
export type MyProfile = {
  id: number;
  first_name: string;
  last_name: string;
  age: number;
  patient_code: string;
  therapist_name?: string | null;
  diagnosis?: string | null;
};

// ─── Jeton ───────────────────────────────────────────────────────────────────
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function getRole(): Role | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(ROLE_KEY) as Role | null;
  } catch {
    return null;
  }
}

export function saveSession(token: string, role: Role) {
  try {
    window.localStorage.setItem(TOKEN_KEY, token);
    window.localStorage.setItem(ROLE_KEY, role);
  } catch {
    /* stockage indisponible : la session ne survivra pas au rechargement */
  }
}

export function logout() {
  try {
    window.localStorage.removeItem(TOKEN_KEY);
    window.localStorage.removeItem(ROLE_KEY);
  } catch {
    /* rien à faire */
  }
}

export function homeFor(role: Role | null): string {
  return role === "patient" ? "/dashboard" : "/therapist";
}

/** Adresse de l'espace thérapeute (dashboard d'analyse) avec la session en cours. */
export function therapistSpaceUrl(): string {
  const token = getToken();
  return token ? `${ANALYTICS_URL}/?token=${encodeURIComponent(token)}` : "/login";
}

/** Envoie l'utilisateur vers son espace selon son rôle. */
export function goToSpace(role: Role, push: (path: string) => void) {
  if (role === "therapist") {
    window.location.href = therapistSpaceUrl();
  } else {
    push("/dashboard");
  }
}

// ─── Requêtes ────────────────────────────────────────────────────────────────
export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(message: string, status: number, detail = "") {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

const MESSAGES: Record<number, string> = {
  400: "La requête est invalide.",
  401: "Session expirée ou identifiants invalides.",
  403: "Accès refusé.",
  404: "Élément introuvable.",
  409: "Conflit : cet élément existe déjà ou a déjà été utilisé.",
  410: "Ce code a expiré.",
  422: "Certaines informations sont manquantes ou invalides.",
};

async function request<T>(method: string, path: string, body?: unknown, auth = true): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const token = getToken();
  if (auth && token) headers.Authorization = `Bearer ${token}`;

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(
      `Impossible de joindre le serveur (${API_URL}). Vérifiez que le backend est démarré.`,
      0,
    );
  }

  if (!response.ok) {
    let detail = "";
    try {
      const data = await response.json();
      detail = typeof data?.detail === "string" ? data.detail : "";
    } catch {
      /* pas de JSON */
    }
    if (response.status === 401 && auth && token) logout();
    throw new ApiError(MESSAGES[response.status] || `Erreur serveur (${response.status}).`, response.status, detail);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

// ─── Authentification ────────────────────────────────────────────────────────
export async function login(email: string, password: string): Promise<Role> {
  try {
    const result = await request<{ access_token: string; role?: Role }>(
      "POST", "/auth/login", { email, password }, false,
    );
    saveSession(result.access_token, result.role || "therapist");
    return result.role || "therapist";
  } catch (error) {
    if (error instanceof ApiError && [401, 422].includes(error.status)) {
      throw new ApiError("Adresse e-mail ou mot de passe incorrect.", error.status);
    }
    throw error;
  }
}

export async function registerTherapist(
  fullName: string,
  email: string,
  password: string,
  specialty: TherapistSpecialty,
) {
  try {
    await request("POST", "/auth/register", { full_name: fullName, email, password, specialty }, false);
  } catch (error) {
    if (error instanceof ApiError && error.status === 400) {
      throw new ApiError("Cette adresse e-mail est déjà utilisée.", 400);
    }
    if (error instanceof ApiError && error.status === 422) {
      throw new ApiError("Vérifiez l’adresse e-mail saisie.", 422);
    }
    throw error;
  }
  return login(email, password);
}

export async function activateAccount(code: string, email: string, password: string) {
  const result = await request<{ access_token: string }>(
    "POST", "/auth/activate", { code, email, password }, false,
  );
  saveSession(result.access_token, "patient");
}

export const getMe = () => request<Me>("GET", "/auth/me");

// ─── Thérapeute ──────────────────────────────────────────────────────────────
export const listPatients = () => request<Patient[]>("GET", "/patients/");
export const createPatient = (first_name: string, last_name: string, age: number) =>
  request<Patient>("POST", "/patients/", { first_name, last_name, age });
export const listGames = () => request<Game[]>("GET", "/games/");
export const listPatientGames = (patientId: number) =>
  request<PatientGame[]>("GET", `/patient-games/patient/${patientId}`);
export const assignGame = (patient_id: number, game_id: number, configuration: GameConfig) =>
  request<PatientGame>("POST", "/patient-games/", { patient_id, game_id, configuration });
export const updateGameConfig = (patientGameId: number, configuration: GameConfig) =>
  request<PatientGame>("PUT", `/patient-games/${patientGameId}`, { configuration });
export const listSessions = (patientGameId: number) =>
  request<GameSession[]>("GET", `/sessions/patient-game/${patientGameId}`);
export const listConsultations = (patientId: number) =>
  request<Consultation[]>("GET", `/consultations/patient/${patientId}`);
export const createConsultation = (patient_id: number, diagnosis: string) =>
  request<Consultation>("POST", "/consultations/", {
    patient_id,
    diagnosis,
    consultation_date: new Date().toISOString().slice(0, 10),
  });
export const createActivationCode = (patient_id: number) =>
  request<{ code: string; expires_at: string }>("POST", "/activation-codes/", { patient_id });

// ─── Patient connecté ────────────────────────────────────────────────────────
export const getMyProfile = () => request<MyProfile>("GET", "/me/patient");
export const getMyGames = () => request<PatientGame[]>("GET", "/me/games");
export const getMySessions = () => request<GameSession[]>("GET", "/me/sessions");
export const saveMySession = (patient_game_id: number, duration_sec: number, metrics: SessionMetrics) =>
  request<GameSession>("POST", "/me/sessions", { patient_game_id, duration_sec, metrics });
