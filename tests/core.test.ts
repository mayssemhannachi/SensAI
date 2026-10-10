import { describe, it, expect } from 'vitest';
import { classifyGesture, motionSpeed, thresholds } from '../src/core/gestures';
import { summarize } from '../src/core/metrics';
import { Staircase, buildTrials } from '../src/core/engine';

const pose = (over: Record<number, [number, number]> = {}) => {
  const p = Array.from({ length: 33 }, () => ({ x: 0.5, y: 0.5, visibility: 1 }));
  p[11] = { x: 0.6, y: 0.4, visibility: 1 };
  p[12] = { x: 0.4, y: 0.4, visibility: 1 };
  p[15] = { x: 0.65, y: 0.7, visibility: 1 };
  p[16] = { x: 0.35, y: 0.7, visibility: 1 };
  for (const k in over) p[+k] = { x: over[k][0], y: over[k][1], visibility: 1 };
  return p;
};

describe('gestes', () => {
  it('reconnaît les bras', () => {
    expect(classifyGesture(pose())).toBe('neutral');
    expect(classifyGesture(pose({ 16: [0.35, 0.2] }))).toBe('right');
    expect(classifyGesture(pose({ 15: [0.65, 0.2] }))).toBe('left');
    expect(classifyGesture(pose({ 15: [0.65, 0.2], 16: [0.35, 0.2] }))).toBe('both');
    expect(classifyGesture(null)).toBe('unknown');
  });
  it('main sur la tête et accroupi', () => {
    expect(classifyGesture(pose({ 16: [0.52, 0.4] }))).toBe('head');
    expect(classifyGesture(pose({ 0: [0.5, 0.7] }), { noseY: 0.5 })).toBe('duck');
  });
  it('vitesse nulle si immobile', () => {
    expect(motionSpeed(pose(), pose(), 0.1)).toBe(0);
    expect(motionSpeed(pose(), pose({ 16: [0.35, 0.2] }), 0.1)).toBeGreaterThan(0);
  });
  it('seuils croissants avec le bruit', () => {
    expect(thresholds([0.2]).still).toBeGreaterThan(thresholds([0.01]).still);
  });
});

describe('mesures', () => {
  it('résume une séance', () => {
    const s = summarize([
      { kind: 'fairy_r', ok: true, rtMs: 800 },
      { kind: 'fairy_l', ok: false, wrongArm: true },
      { kind: 'fairy_r', ok: false },
      { kind: 'enemy', ok: false, stopMs: 500, agitation: 0.5 },
      { kind: 'enemy', ok: true, stopMs: null, agitation: 0.1 },
      { kind: 'enemy', ok: true, stopMs: null, agitation: 0.1 },
    ]);
    expect(s).toMatchObject({ fairies: 3, omissions: 1, wrongArms: 1, enemies: 3, falseAlarms: 1, rtMeanMs: 800, stopMeanMs: 500 });
  });
});

describe('moteur', () => {
  it('difficulté adaptative', () => {
    const s = new Staircase(2000, 1200, 3000, 150, 200, true);
    s.update(true); s.update(true);
    expect(s.value).toBe(1850);
    s.update(false);
    expect(s.value).toBe(2050);
  });
  it('construit les essais', () => {
    const t = buildTrials(40, 0.8, ['fairy_r', 'fairy_l']);
    expect(t).toHaveLength(40);
    expect(t.filter((k) => k === 'enemy')).toHaveLength(8);
  });
});