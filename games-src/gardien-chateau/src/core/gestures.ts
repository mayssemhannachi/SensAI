// Logique pure (sans caméra) : testable seule.
export type Pt = { x: number; y: number; visibility?: number };
export type Pose = Pt[]; // 33 points MediaPipe, left/right = côtés anatomiques de l'enfant
export type Gesture = 'neutral' | 'right' | 'left' | 'both' | 'head' | 'duck' | 'unknown';

export type Posture = 'standing' | 'sitting';

const I = { nose: 0, lSh: 11, rSh: 12, lEl: 13, rEl: 14, lWr: 15, rWr: 16, lHip: 23, rHip: 24 };
const TRACKED = [I.nose, I.lSh, I.rSh, I.lEl, I.rEl, I.lWr, I.rWr, I.lHip, I.rHip];
const vis = (p?: Pt) => (p?.visibility ?? 1) > 0.5;

export function shoulderWidth(p: Pose): number {
  return Math.hypot(p[I.lSh].x - p[I.rSh].x, p[I.lSh].y - p[I.rSh].y) || 1e-6;
}

/** Poignet nettement au-dessus de l'épaule (y vers le bas). */
export function armUp(p: Pose, side: 'left' | 'right', margin = 0.25): boolean {
  const sh = p[side === 'left' ? I.lSh : I.rSh];
  const wr = p[side === 'left' ? I.lWr : I.rWr];
  return vis(sh) && vis(wr) && wr.y < sh.y - margin * shoulderWidth(p);
}

export function classifyGesture(
  p: Pose | null,
  base?: { noseY: number },
  posture: Posture = 'standing'
): Gesture {
  if (!p || p.length < 25 || !vis(p[I.lSh]) || !vis(p[I.rSh])) return 'unknown';
  const w = shoulderWidth(p), nose = p[I.nose];
  // Si assis, l'amplitude requise pour se baisser est réduite (penche le buste/tête)
  const duckMargin = posture === 'sitting' ? 0.3 * w : 0.5 * w;
  if (base && nose.y > base.noseY + duckMargin) return 'duck';
  const nearHead = (wr: Pt) => vis(wr) && Math.abs(wr.x - nose.x) < 0.35 * w && wr.y < nose.y + 0.1 * w && wr.y > nose.y - 0.9 * w;
  if (nearHead(p[I.lWr]) || nearHead(p[I.rWr])) return 'head'; // main sur la tête
  const r = armUp(p, 'right');
  const l = armUp(p, 'left');
  return r && l ? 'both' : r ? 'right' : l ? 'left' : 'neutral';
}

/** Vitesse des mouvements en largeurs d'épaules par seconde.
 * Capter à la fois la vitesse moyenne et les pointes sur une articulation (bras, main, tête)
 * pour ne pas diluer un mouvement d'un seul membre parmi les membres immobiles.
 */
export function motionSpeed(prev: Pose, cur: Pose, dtSec: number): number {
  if (dtSec <= 0) return 0;
  const w = shoulderWidth(cur);
  let s = 0, n = 0;
  let maxJoint = 0;
  for (const i of TRACKED) {
    if (!vis(prev[i]) || !vis(cur[i])) continue;
    const v = Math.hypot(cur[i].x - prev[i].x, cur[i].y - prev[i].y) / w / dtSec;
    s += v;
    if (v > maxJoint) maxJoint = v;
    n++;
  }
  if (!n) return 0;
  const avg = s / n;
  // Détection réactive : le moindre bras levé ou mouvement de tête est capté immédiatement
  return Math.max(avg * 1.5, maxJoint * 0.75);
}

/** Seuils immobile/mouvement à partir du bruit mesuré enfant immobile.
 * Utilise le 75ème percentile pour ignorer les à-coups isolés et borne les seuils.
 */
export function thresholds(noise: number[]) {
  if (!noise.length) return { still: 0.1, move: 0.35 };
  const sorted = [...noise].sort((a, b) => a - b);
  const p75 = sorted[Math.floor(sorted.length * 0.75)] ?? 0.1;
  const still = Math.min(0.22, Math.max(0.08, p75 * 1.3));
  // Le seuil 'move' reste toujours atteignable par un mouvement humain normal
  const move = Math.min(0.55, Math.max(0.25, still * 2.2));
  return { still, move };
}