import { FilesetResolver, PoseLandmarker } from '@mediapipe/tasks-vision';
import type { Pose } from '../core/gestures';

// Intégration SensAI : comme les autres jeux de la plateforme, les fichiers de
// MediaPipe (wasm + modèle) sont chargés depuis le CDN officiel au lieu d'être
// copiés dans le dépôt (plus de 40 Mo). Même version que le paquet npm.
const MP_WASM = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm';
const POSE_MODEL =
  'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task';

export class Tracker {
  private lm!: PoseLandmarker;

  async init() {
    const fileset = await FilesetResolver.forVisionTasks(MP_WASM);
    let lastError: unknown = null;
    for (const delegate of ['GPU', 'CPU'] as const) {
      try {
        this.lm = await PoseLandmarker.createFromOptions(fileset, {
          baseOptions: { modelAssetPath: POSE_MODEL, delegate },
          runningMode: 'VIDEO',
          numPoses: 1,
        });
        return;
      } catch (e) {
        lastError = e;
      }
    }
    throw new Error('Modèle de détection introuvable (connexion Internet nécessaire). ' + String(lastError ?? ''));
  }

  detect(video: HTMLVideoElement, tsMs: number): Pose | null {
    const r = this.lm.detectForVideo(video, tsMs);
    return (r.landmarks[0] as Pose | undefined) ?? null;
  }
}
