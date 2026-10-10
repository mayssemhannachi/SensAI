export type Kind = 'fairy_r' | 'fairy_l' | 'star' | 'crown' | 'dragon' | 'enemy';

export interface TrialResult {
  kind: Kind;
  ok: boolean;
  rtMs?: number;          // fée : délai jusqu'au début du geste tenu
  wrongArm?: boolean;     // fée : mauvais bras levé
  stopMs?: number | null; // ennemi : temps pour se figer (si l'enfant bougeait)
  agitation?: number;     // ennemi : vitesse moyenne / seuil de mouvement
}

export interface Summary {
  fairies: number; omissions: number; wrongArms: number;
  enemies: number; falseAlarms: number;
  rtMeanMs: number; rtSdMs: number; thirds: number[];
  stopMeanMs: number | null; agitation: number;
}

const avg = (a: number[]) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0);
const sd = (a: number[]) => { const m = avg(a); return Math.sqrt(avg(a.map((x) => (x - m) ** 2))); };

export function summarize(rs: TrialResult[]): Summary {
  const F = rs.filter((r) => r.kind !== 'enemy');
  const E = rs.filter((r) => r.kind === 'enemy');
  const rts = F.filter((r) => r.ok && r.rtMs != null).map((r) => r.rtMs as number);
  const stops = E.map((r) => r.stopMs).filter((v): v is number => v != null);
  const sz = Math.ceil(rs.length / 3) || 1;
  const thirds = [0, 1, 2].map((i) => {
    const s = rs.slice(i * sz, i * sz + sz);
    return s.length ? Math.round((100 * s.filter((r) => r.ok).length) / s.length) : 0;
  });
  return {
    fairies: F.length,
    omissions: F.filter((r) => !r.ok && !r.wrongArm).length,
    wrongArms: F.filter((r) => r.wrongArm).length,
    enemies: E.length,
    falseAlarms: E.filter((r) => !r.ok).length,
    rtMeanMs: Math.round(avg(rts)),
    rtSdMs: rts.length > 2 ? Math.round(sd(rts)) : 0,
    thirds,
    stopMeanMs: stops.length ? Math.round(avg(stops)) : null,
    agitation: Math.round(100 * avg(E.map((r) => r.agitation ?? 0))),
  };
}