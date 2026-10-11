/**
 * Synthèse vocale (SpeechSynthesis API) – instructions orales en français.
 * Aucun fichier audio nécessaire, fonctionne dans tous les navigateurs modernes.
 */

let enVoice: SpeechSynthesisVoice | null = null;
let currentUtt: SpeechSynthesisUtterance | null = null;
let activeEndCallback: (() => void) | null = null;
let safetyTimeoutId: number | null = null;

/** Charge la voix anglaise dès que les voix sont disponibles. */
function loadEnVoice() {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
  const pick = () => {
    const voices = speechSynthesis.getVoices();
    enVoice =
      voices.find((v) => v.lang.startsWith('en') && v.localService) ??
      voices.find((v) => v.lang.startsWith('en')) ??
      voices[0] ??
      null;
  };
  pick();
  speechSynthesis.onvoiceschanged = pick;
}
loadEnVoice();

/**
 * Prononce un texte en anglais (en supprimant les emoji et les sauts de ligne).
 * @param text         Le texte à dire
 * @param onEndOrRate  Callback déclenché dès que la voix se termine, ou vitesse de lecture
 * @param rate         Vitesse de lecture si le 2ème argument est une fonction
 */
export function speak(
  text: string,
  onEndOrRate?: (() => void) | number,
  rate = 0.95
) {
  stopSpeech();

  const onEnd = typeof onEndOrRate === 'function' ? onEndOrRate : undefined;
  const actualRate = typeof onEndOrRate === 'number' ? onEndOrRate : rate;

  if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
    onEnd?.();
    return;
  }

  const clean = text
    .replace(/\n/g, ' ')
    .replace(/[\p{Emoji_Presentation}\p{Extended_Pictographic}]/gu, '')
    .trim();

  if (!clean) {
    onEnd?.();
    return;
  }

  const utt = new SpeechSynthesisUtterance(clean);
  utt.lang = 'en-US';
  utt.rate = actualRate;
  utt.pitch = 1.05;
  if (enVoice) utt.voice = enVoice;

  currentUtt = utt;
  activeEndCallback = onEnd ?? null;

  let completed = false;
  const finish = () => {
    if (completed) return;
    completed = true;
    if (safetyTimeoutId !== null) {
      clearTimeout(safetyTimeoutId);
      safetyTimeoutId = null;
    }
    const cb = activeEndCallback;
    activeEndCallback = null;
    currentUtt = null;
    cb?.();
  };

  utt.onend = finish;
  utt.onerror = finish;

  // Sécurité anti-blocage (au cas où le navigateur omet onend)
  const estimatedMs = Math.max(1200, Math.round((clean.length / 10) * 1000 / rate) + 800);
  safetyTimeoutId = window.setTimeout(finish, estimatedMs);

  speechSynthesis.speak(utt);
}

/** Arrête toute parole en cours sans déclencher le callback de fin. */
export function stopSpeech() {
  if (safetyTimeoutId !== null) {
    clearTimeout(safetyTimeoutId);
    safetyTimeoutId = null;
  }
  activeEndCallback = null;
  currentUtt = null;
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    speechSynthesis.cancel();
  }
}
