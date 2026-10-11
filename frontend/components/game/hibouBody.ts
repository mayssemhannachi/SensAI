// ──────────────────────────────────────────────────────────────────────────────
// Le Hibou — suivi des épaules et de la main (portage de hibou.py, Chahed)
//
//  - Épaules (MediaPipe Pose) : stabilité 2D du buste — inclinaison de la ligne
//    d'épaules, bascule latérale, rotation (rétrécissement de la largeur).
//    Sert au cadrage et à la détection de compensation.
//  - Main (MediaPipe Hands) : pouce vers le bas = « J'ai mal / Stop »,
//    nombre de doigts levés = échelle de douleur.
//
// Les modèles sont chargés à la demande depuis le CDN de MediaPipe. Sans Internet
// (ou si le chargement échoue), le jeu fonctionne sans ces deux fonctions.
// ──────────────────────────────────────────────────────────────────────────────

const MP_URL = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14";
const POSE_MODEL =
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task";
const HAND_MODEL =
  "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task";

export type Point = { x: number; y: number; z?: number; visibility?: number };
type Detector = { detectForVideo: (video: HTMLVideoElement, time: number) => { landmarks?: Point[][] }; close?: () => void };

export type BodyTrackers = { pose: Detector | null; hands: Detector | null };

/** Charge les modèles Pose et Hands (GPU si possible, sinon CPU). */
export async function loadBodyTrackers(): Promise<BodyTrackers> {
  // Import direct depuis le CDN (non regroupé par le bundler).
  const vision = await import(/* webpackIgnore: true */ `${MP_URL}/vision_bundle.mjs`);
  const fileset = await vision.FilesetResolver.forVisionTasks(`${MP_URL}/wasm`);
  const create = async (factory: { createFromOptions: (f: unknown, o: unknown) => Promise<Detector> },
    model: string, extra: Record<string, unknown>): Promise<Detector | null> => {
    for (const delegate of ["GPU", "CPU"]) {
      try {
        return await factory.createFromOptions(fileset, {
          baseOptions: { modelAssetPath: model, delegate }, runningMode: "VIDEO", ...extra,
        });
      } catch {
        /* essai suivant */
      }
    }
    return null;
  };
  const [pose, hands] = await Promise.all([
    create(vision.PoseLandmarker, POSE_MODEL, { numPoses: 1 }),
    create(vision.HandLandmarker, HAND_MODEL, { numHands: 1, minHandDetectionConfidence: 0.55 }),
  ]);
  return { pose, hands };
}

// ─── Épaules ──────────────────────────────────────────────────────────────────
export type Shoulders = { tilt: number; cx: number; cy: number; width: number };

/** ShoulderTracker.track de hibou.py : épaules 11 et 12, visibilité ≥ 0,35. */
export function shouldersFrom(lm: Point[] | undefined, videoW: number, videoH: number): Shoulders | null {
  const l = lm?.[11];
  const r = lm?.[12];
  if (!l || !r) return null;
  if ((l.visibility ?? 1) < 0.35 || (r.visibility ?? 1) < 0.35) return null;
  const dx = (r.x - l.x) * videoW;
  const dy = (r.y - l.y) * videoH;
  return {
    tilt: (Math.atan2(dy, Math.max(1e-3, Math.abs(dx))) * 180) / Math.PI,
    cx: (l.x + r.x) / 2,
    cy: (l.y + r.y) / 2,
    width: Math.abs(l.x - r.x),
  };
}

/** Écart du buste par rapport à la position neutre (°), comme dans hibou.py. */
export function shoulderDeviation(current: Shoulders, neutral: Shoulders): number {
  const devTilt = Math.abs(current.tilt - neutral.tilt); // haussement / inclinaison
  const devShift = Math.abs(current.cx - neutral.cx) * 100 * 1.5; // bascule latérale
  const ratio = Math.min(1, Math.max(0.4, current.width / Math.max(1e-4, neutral.width)));
  const devRot = (Math.acos(ratio) * 180) / Math.PI; // rotation du buste
  return Math.max(devTilt, devShift, devRot);
}

/** Framing hint based on shoulders (hibou.py thresholds), or null if well positioned. */
export function shoulderFramingHint(s: Shoulders | null): string | null {
  if (!s) return "Step back a bit so we can see your shoulders";
  if (s.width < 0.22) return "Move a bit closer to the camera";
  if (s.width > 0.6) return "Step back a bit from the screen";
  // Non-mirrored image: child's right is on the left of the image.
  if (s.cx < 0.38) return "Shift slightly to the left";
  if (s.cx > 0.62) return "Shift slightly to the right";
  return null;
}

export function median(values: number[]): number {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted.length ? sorted[Math.floor(sorted.length / 2)] : 0;
}

// ─── Main ─────────────────────────────────────────────────────────────────────
const dist = (a: Point, b: Point) => Math.hypot(a.x - b.x, a.y - b.y);

/** HandTracker.detect_thumb_pain : 3 doigts repliés et pouce franchement vers le bas. */
export function thumbDown(lm: Point[] | undefined): boolean {
  if (!lm || lm.length < 21) return false;
  const wrist = lm[0];
  let folded = 0;
  for (const [tip, pip] of [[8, 6], [12, 10], [16, 14], [20, 18]]) {
    if (dist(lm[tip], wrist) < dist(lm[pip], wrist) * 1.2) folded += 1;
  }
  const down = lm[4].y > lm[3].y && lm[4].y > lm[2].y && lm[4].y > wrist.y + 0.02;
  return folded >= 3 && down;
}

/** HandTracker.count_fingers : 0 à 5 doigts levés. */
export function countFingers(lm: Point[] | undefined): number | null {
  if (!lm || lm.length < 21) return null;
  const wrist = lm[0];
  let n = 0;
  for (const [tip, pip] of [[8, 6], [12, 10], [16, 14], [20, 18]]) {
    if (lm[tip].y < lm[pip].y) n += 1;
  }
  if (lm[4].y < lm[2].y || dist(lm[4], wrist) > 0.18) n += 1;
  return n;
}

/** Doigts (1 = pas mal … 5 = très mal) → échelle de douleur SensAI (0 à 5). */
export function painFromFingers(n: number): number {
  return Math.round(((n - 1) * 5) / 4);
}
