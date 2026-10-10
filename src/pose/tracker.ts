import { FilesetResolver, PoseLandmarker } from '@mediapipe/tasks-vision';
import type { Pose } from '../core/gestures';

/** Tout est local : wasm dans /mediapipe/wasm, modèle dans /models (voir README). */
export class Tracker {
  private lm!: PoseLandmarker;

  async init() {
    const fileset = await FilesetResolver.forVisionTasks('/mediapipe/wasm');
    const res = await fetch('/models/pose_landmarker_lite.task');
    const buf = await res.arrayBuffer();
    if (!res.ok || buf.byteLength < 1_000_000 || (res.headers.get('content-type') ?? '').includes('html')) {
      throw new Error('Modèle introuvable : placez pose_landmarker_lite.task dans public/models/');
    }
    this.lm = await PoseLandmarker.createFromOptions(fileset, {
      baseOptions: { modelAssetBuffer: new Uint8Array(buf), delegate: 'GPU' },
      runningMode: 'VIDEO',
      numPoses: 1,
    });
  }

  detect(video: HTMLVideoElement, tsMs: number): Pose | null {
    const r = this.lm.detectForVideo(video, tsMs);
    return (r.landmarks[0] as Pose | undefined) ?? null;
  }
}