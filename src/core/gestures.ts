// Logique pure (sans caméra) : testable seule.
export type Pt = { x: number; y: number; visibility?: number };
export type Pose = Pt[]; // 33 points MediaPipe, left/right = côtés anatomiques de l'enfant
export type Gesture = 'neutral' | 'right' | 'left' | 'both' | 'head' | 'duck' | 'unknown';

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

export function classifyGesture(p: Pose | null, base?: { noseY: number }): Gesture {
  if (!p || p.length < 25 || !vis(p[I.lSh]) || !vis(p[I.rSh])) return 'unknown';
  const w = shoulderWidth(p), nose = p[I.nose];
  if (base && nose.y > base.noseY + 0.5 * w) return 'duck'; // accroupi : le nez descend
  const nearHead = (wr: Pt) => vis(wr) && Math.abs(wr.x - nose.x) < 0.35 * w && wr.y < nose.y + 0.1 * w && wr.y > nose.y - 0.9 * w;
  if (nearHead(p[I.lWr]) || nearHead(p[I.rWr])) return 'head'; // main sur la tête
  const r = armUp(p, 'right');
  const l = armUp(p, 'left');
  return r && l ? 'both' : r ? 'right' : l ? 'left' : 'neutral';
}

/** Vitesse moyenne des articulations, en largeurs d'épaules par seconde. */
export function motionSpeed(prev: Pose, cur: Pose, dtSec: number): number {
  if (dtSec <= 0) return 0;
  const w = shoulderWidth(cur);
  let s = 0, n = 0;
  for (const i of TRACKED) {
    if (!vis(prev[i]) || !vis(cur[i])) continue;
    s += Math.hypot(cur[i].x - prev[i].x, cur[i].y - prev[i].y) / w;
    n++;
  }
  return n ? s / n / dtSec : 0;
}

/** Seuils immobile/mouvement à partir du bruit mesuré enfant immobile. */
export function thresholds(noise: number[]) {
  const max = noise.reduce((a, b) => Math.max(a, b), 0);
  const still = Math.max(0.1, max * 1.5);
  return { still, move: Math.max(0.4, still * 3) };
}