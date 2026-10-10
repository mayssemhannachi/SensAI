// ──────────────────────────────────────────────────────────────────────────────
// Lien avec la plateforme SensAI (ajout pour l'intégration, le jeu reste celui de Chahed)
//
//  - Réglages de l'ergothérapeute reçus par l'URL :
//      gestes=fairy_r,fairy_l,star   les 3 défis prescrits (sinon l'enfant les choisit)
//      essais=40                     nombre d'essais de la vraie partie
//      go=80                         % d'essais « défi » (le reste = l'ogre statue)
//  - Messages envoyés à la page SensAI (postMessage, source « gardien-chateau ») :
//      started, progress (essais faits / prévus), done (résumé de la séance).
//  - Message reçu : { source: 'sensai', type: 'stop' } → fin anticipée de la séance.
// ──────────────────────────────────────────────────────────────────────────────

import type { Kind } from './core/metrics';

export const SLUG = 'gardien-chateau';

const GO_KINDS: Kind[] = ['fairy_r', 'fairy_l', 'star', 'crown', 'dragon'];
const Q = new URLSearchParams(location.search);
const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

function prescribedKinds(): Kind[] | null {
  const list = (Q.get('gestes') ?? '').split(',').filter((k): k is Kind => GO_KINDS.includes(k as Kind));
  const unique = [...new Set(list)];
  return unique.length === 3 ? unique : null;
}

export const PRESCRIPTION = {
  /** Les 3 défis choisis par l'ergothérapeute, ou null : l'enfant les choisit lui-même. */
  kinds: prescribedKinds(),
  trials: Q.has('essais') ? clamp(Math.round(Number(Q.get('essais')) || 40), 10, 80) : 40,
  goRatio: Q.has('go') ? clamp(Number(Q.get('go')) || 80, 50, 95) / 100 : 0.8,
};

const embedded = window.parent !== window;

export function toPlatform(msg: Record<string, unknown>) {
  if (embedded) window.parent.postMessage({ source: SLUG, ...msg }, location.origin);
}

let stopHandler: (() => void) | null = null;
/** La scène de jeu indique quoi faire si la page SensAI demande l'arrêt (« J'ai mal / Stop »). */
export function onStopRequest(fn: (() => void) | null) {
  stopHandler = fn;
}
window.addEventListener('message', (e) => {
  if (e.origin !== location.origin || e.data?.source !== 'sensai') return;
  if (e.data.type === 'stop') stopHandler?.();
});
