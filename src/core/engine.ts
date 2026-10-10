import type { Kind } from './metrics';

export function buildTrials(n: number, goRatio: number, kinds: Kind[], rnd: () => number = Math.random): Kind[] {
  const go = Math.round(n * goRatio);
  const a: Kind[] = [];
  for (let i = 0; i < n; i++) a.push(i < go ? kinds[i % kinds.length] : 'enemy');
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rnd() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/** Difficulté adaptative : 2 réussites d'affilée = plus dur, 1 échec = plus facile. */
export class Staircase {
  private streak = 0;
  constructor(
    public value: number, private min: number, private max: number,
    private hardStep: number, private easeStep: number, private hardIsLower: boolean,
  ) {}
  update(ok: boolean) {
    const clamp = (v: number) => Math.min(this.max, Math.max(this.min, v));
    if (ok) {
      if (++this.streak >= 2) {
        this.value = clamp(this.value + (this.hardIsLower ? -this.hardStep : this.hardStep));
        this.streak = 0;
      }
    } else {
      this.streak = 0;
      this.value = clamp(this.value + (this.hardIsLower ? this.easeStep : -this.easeStep));
    }
  }
}