"use client";

// ──────────────────────────────────────────────────────────────────────────────
// Le Hibou — exercice de rotation cervicale
// L'enfant tourne la tête vers la souris, maintient la position, puis revient au
// centre. Les réglages viennent du thérapeute (configuration du jeu assigné) et
// la séance est enregistrée dans le backend à la fin (POST /me/sessions).
//
// Deux modes d'entrée :
//  - caméra : MediaPipe FaceMesh (scripts chargés par la page) → angle de lacet ;
//  - clavier / boutons : flèches ← → (démo, test ou absence de caméra).
// ──────────────────────────────────────────────────────────────────────────────

import React, { useCallback, useEffect, useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { Camera, Keyboard } from "lucide-react";
import { getMyGames, saveMySession, type PatientGame, type SessionMetrics } from "@/lib/api";
import { DIFFICULTY_LEVEL, SPEED_LABELS, withDefaults } from "@/lib/games";
import { useRequireAuth } from "@/lib/useAuth";
import RatingRow from "./RatingRow";

type Phase = "loading" | "intro" | "calibrating" | "playing" | "rating" | "saving" | "done" | "error";
type Step = "turn" | "hold" | "return";
type InputMode = "camera" | "keyboard";

// Vitesse maximale (°/s, mesurée sur une vitesse lissée — cf. hibou.py de Chahed, vmax 40°/s).
const SPEED_LIMIT_DEG_S: Record<string, number> = { lente: 45, moderee: 70, rapide: 110 };
const CENTER_ZONE = 8; // ° : zone considérée comme « au centre »
const DEFAULT_CAMERA_GAIN = 1.25; // gain du ratio nez / visage (hibou.py)
const TILT_LIMIT = 15; // ° d'inclinaison de la tête au-delà desquels on parle de compensation
const COMPENSATION_DELAY = 0.35; // s de confirmation avant d'afficher l'alerte (hibou.py)

type Landmark = { x: number; y: number; z: number };
type FaceMeshResults = { multiFaceLandmarks?: Landmark[][] };
type FaceMeshInstance = {
  setOptions: (o: Record<string, unknown>) => void;
  onResults: (cb: (r: FaceMeshResults) => void) => void;
  send: (input: { image: HTMLVideoElement }) => Promise<void>;
  close?: () => void;
};
type CameraInstance = { start: () => Promise<void>; stop: () => void };
declare global {
  interface Window {
    FaceMesh?: new (config: { locateFile: (file: string) => string }) => FaceMeshInstance;
    Camera?: new (video: HTMLVideoElement, options: { onFrame: () => Promise<void>; width: number; height: number }) => CameraInstance;
  }
}

/** Lacet (°) : positif quand l'enfant tourne la tête vers SA droite. */
function yawFromLandmarks(points: Landmark[], gain = DEFAULT_CAMERA_GAIN): number | null {
  const nose = points[1];
  const left = points[234];
  const right = points[454];
  if (!nose || !left || !right) return null;
  const half = (right.x - left.x) / 2;
  if (Math.abs(half) < 1e-4) return null;
  const ratio = ((nose.x - (left.x + right.x) / 2) / half) * gain;
  const clamped = Math.max(-1, Math.min(1, ratio));
  // Image caméra non inversée : la droite de l'enfant est à gauche de l'image.
  return (-Math.asin(clamped) * 180) / Math.PI;
}

/** Inclinaison de la tête (°) : angle de la ligne des yeux. Sert à repérer la compensation
 *  (l'enfant penche la tête au lieu de la tourner), comme le contrôle des épaules de hibou.py. */
function rollFromLandmarks(points: Landmark[]): number | null {
  const a = points[33];
  const b = points[263];
  if (!a || !b) return null;
  return (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI;
}

type Tracker = {
  rep: number;
  step: Step;
  holdStart: number;
  successes: number;
  holds: number[];
  maxLeft: number;
  maxRight: number;
  overshoots: number;
  overshooting: boolean;
  fastMoves: number;
  speed: number;
  compensations: number;
  compTimer: number;
  compensating: boolean;
  lastYaw: number;
  lastDelta: number;
  lastTime: number;
  jitter: number[];
  startedAt: number;
};

const newTracker = (): Tracker => ({
  rep: 0,
  step: "turn",
  holdStart: 0,
  successes: 0,
  holds: [],
  maxLeft: 0,
  maxRight: 0,
  overshoots: 0,
  overshooting: false,
  fastMoves: 0,
  speed: 0,
  compensations: 0,
  compTimer: 0,
  compensating: false,
  lastYaw: 0,
  lastDelta: 0,
  lastTime: 0,
  jitter: [],
  startedAt: 0,
});

export default function LeHibouGame() {
  const { me } = useRequireAuth("patient");
  const videoRef = useRef<HTMLVideoElement>(null);
  const [phase, setPhase] = useState<Phase>("loading");
  const [error, setError] = useState<string | null>(null);
  const [assignment, setAssignment] = useState<PatientGame | null>(null);
  const [mode, setMode] = useState<InputMode>("camera");
  const [cameraState, setCameraState] = useState<"off" | "starting" | "on" | "failed">("off");
  const [faceVisible, setFaceVisible] = useState(true);

  // Valeurs affichées (rafraîchies ~15 fois / s)
  const [view, setView] = useState({ yaw: 0, rep: 0, step: "turn" as Step, hold: 0, successes: 0, tooFast: false, tooFar: false, tilted: false });
  const [result, setResult] = useState<{ metrics: SessionMetrics; duration: number } | null>(null);
  const [pain, setPain] = useState<number | null>(null);
  const [effort, setEffort] = useState<number | null>(null);

  const yawRef = useRef(0);
  const rawYawRef = useRef<number | null>(null);
  const rawRollRef = useRef<number | null>(null);
  const baselineRef = useRef(0);
  const baselineRollRef = useRef(0);
  const calibrationRef = useRef<number[]>([]);
  const rollCalibrationRef = useRef<number[]>([]);
  const trackerRef = useRef<Tracker>(newTracker());
  const keysRef = useRef({ left: false, right: false });
  const phaseRef = useRef<Phase>("loading");
  const modeRef = useRef<InputMode>("camera");
  const cameraRef = useRef<CameraInstance | null>(null);
  const faceMeshRef = useRef<FaceMeshInstance | null>(null);

  const config = withDefaults(assignment?.configuration);
  const configRef = useRef(config);
  useEffect(() => {
    configRef.current = config;
  });
  useEffect(() => {
    phaseRef.current = phase;
  }, [phase]);
  useEffect(() => {
    modeRef.current = mode;
  }, [mode]);

  // ── Chargement du jeu assigné (réglages du thérapeute) ──────────────────────
  useEffect(() => {
    if (!me) return;
    const pgParam = Number(new URLSearchParams(window.location.search).get("pg"));
    getMyGames()
      .then((games) => {
        const found =
          games.find((g) => g.id === pgParam) ?? games.find((g) => g.game_slug === "le-hibou");
        if (!found) {
          setError("Le Hibou ne t’a pas encore été attribué par ton thérapeute.");
          setPhase("error");
          return;
        }
        if (found.configuration?.active === false) {
          setError("Ce jeu est en pause : ton thérapeute l’a désactivé pour le moment.");
          setPhase("error");
          return;
        }
        setAssignment(found);
        setPhase("intro");
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Chargement impossible.");
        setPhase("error");
      });
  }, [me]);

  // ── Caméra + FaceMesh ───────────────────────────────────────────────────────
  const stopCamera = useCallback(() => {
    cameraRef.current?.stop();
    cameraRef.current = null;
    faceMeshRef.current?.close?.();
    faceMeshRef.current = null;
    const stream = videoRef.current?.srcObject as MediaStream | null;
    stream?.getTracks().forEach((t) => t.stop());
    if (videoRef.current) videoRef.current.srcObject = null;
  }, []);

  const startCamera = useCallback(async (): Promise<boolean> => {
    setCameraState("starting");
    // Les scripts MediaPipe sont chargés par la page : on leur laisse quelques secondes.
    for (let i = 0; i < 40 && (!window.FaceMesh || !window.Camera); i++) {
      await new Promise((r) => setTimeout(r, 150));
    }
    if (!window.FaceMesh || !window.Camera || !videoRef.current || !navigator.mediaDevices) {
      setCameraState("failed");
      return false;
    }
    try {
      const faceMesh = new window.FaceMesh({
        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`,
      });
      faceMesh.setOptions({ maxNumFaces: 1, refineLandmarks: false, minDetectionConfidence: 0.5, minTrackingConfidence: 0.5 });
      faceMesh.onResults((results) => {
        const landmarks = results.multiFaceLandmarks?.[0];
        const c = configRef.current;
        const gain = Number(c.camera_gain) || DEFAULT_CAMERA_GAIN;
        const raw = landmarks ? yawFromLandmarks(landmarks, gain) : null;
        const yaw = raw === null ? null : c.invert_direction ? -raw : raw;
        rawYawRef.current = yaw;
        rawRollRef.current = landmarks ? rollFromLandmarks(landmarks) : null;
        setFaceVisible(yaw !== null);
      });
      const camera = new window.Camera(videoRef.current, {
        onFrame: async () => {
          if (videoRef.current) await faceMesh.send({ image: videoRef.current });
        },
        width: 640,
        height: 480,
      });
      await camera.start();
      faceMeshRef.current = faceMesh;
      cameraRef.current = camera;
      setCameraState("on");
      return true;
    } catch {
      setCameraState("failed");
      stopCamera();
      return false;
    }
  }, [stopCamera]);

  useEffect(() => stopCamera, [stopCamera]);

  // ── Clavier (mode sans caméra) ──────────────────────────────────────────────
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") keysRef.current.left = true;
      if (e.key === "ArrowRight") keysRef.current.right = true;
    };
    const up = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") keysRef.current.left = false;
      if (e.key === "ArrowRight") keysRef.current.right = false;
    };
    window.addEventListener("keydown", down);
    window.addEventListener("keyup", up);
    return () => {
      window.removeEventListener("keydown", down);
      window.removeEventListener("keyup", up);
    };
  }, []);

  // ── Fin de partie ───────────────────────────────────────────────────────────
  const finish = useCallback((stoppedEarly: boolean) => {
    const t = trackerRef.current;
    const c = configRef.current;
    const reps = c.repetitions;
    const duration = Math.max(1, Math.round((performance.now() - (t.startedAt || performance.now())) / 1000));
    const successRate = reps ? (t.successes / reps) * 100 : 0;
    const peak = (t.maxLeft + t.maxRight) / 2;
    const amplitudeScore = Math.min(1, peak / c.target_angle) * 30;
    const score = Math.max(0, Math.min(100, Math.round(successRate * 0.7 + amplitudeScore - t.overshoots * 2)));
    const jitter = t.jitter.length ? t.jitter.reduce((a, b) => a + b, 0) / t.jitter.length : 0;
    const metrics: SessionMetrics = {
      score,
      success_rate: Math.round(successRate * 10) / 10,
      repetitions: t.successes,
      repetitions_target: reps,
      level_number: DIFFICULTY_LEVEL[c.difficulty] ?? 1,
      exercise_name: "Rotation cervicale",
      played_at: new Date().toISOString(),
      rotation_left: Math.round(t.maxLeft),
      rotation_right: Math.round(t.maxRight),
      hold_seconds_avg: t.holds.length ? Math.round((t.holds.reduce((a, b) => a + b, 0) / t.holds.length) * 10) / 10 : 0,
      smoothness: Math.max(0, Math.min(100, Math.round(100 - jitter * 25))),
      overshoots: t.overshoots,
      compensations: t.compensations,
      fast_moves: Math.round(t.fastMoves * 10) / 10,
      completed: !stoppedEarly && t.successes >= reps,
      stopped_early: stoppedEarly,
      input_mode: modeRef.current,
      target_angle: c.target_angle,
    };
    setResult({ metrics, duration });
    stopCamera();
    setPhase("rating");
  }, [stopCamera]);

  // ── Boucle de jeu ───────────────────────────────────────────────────────────
  useEffect(() => {
    let frame = 0;
    let lastRender = 0;
    let last = performance.now();
    const loop = (now: number) => {
      const dt = Math.min(0.1, (now - last) / 1000);
      last = now;
      const c = configRef.current;
      const p = phaseRef.current;

      // 1. Lecture de l'angle courant
      if (modeRef.current === "keyboard") {
        const { left, right } = keysRef.current;
        const goal = right && !left ? c.target_angle + 6 : left && !right ? -(c.target_angle + 6) : 0;
        const speed = goal === 0 ? 55 : 40; // °/s
        const diff = goal - yawRef.current;
        yawRef.current += Math.sign(diff) * Math.min(Math.abs(diff), speed * dt);
      } else if (rawYawRef.current !== null) {
        if (p === "calibrating") {
          calibrationRef.current.push(rawYawRef.current);
          if (rawRollRef.current !== null) rollCalibrationRef.current.push(rawRollRef.current);
        }
        const target = rawYawRef.current - baselineRef.current;
        yawRef.current += (target - yawRef.current) * 0.5; // lissage léger
      }

      // 2. Calibrage (caméra) : position neutre = moyenne de ~1,5 s
      if (p === "calibrating" && calibrationRef.current.length >= 25) {
        const sorted = [...calibrationRef.current].sort((a, b) => a - b);
        baselineRef.current = sorted[Math.floor(sorted.length / 2)];
        const rolls = [...rollCalibrationRef.current].sort((a, b) => a - b);
        baselineRollRef.current = rolls.length ? rolls[Math.floor(rolls.length / 2)] : 0;
        yawRef.current = 0;
        trackerRef.current = { ...newTracker(), startedAt: performance.now(), lastTime: now };
        setPhase("playing");
      }

      // 3. Logique de l'exercice
      const t = trackerRef.current;
      let tooFast = false;
      let tooFar = false;
      let tilted = false;
      if (p === "playing") {
        const yaw = yawRef.current;
        const direction = t.rep % 2 === 0 ? 1 : -1; // droite puis gauche
        const toward = yaw * direction;
        if (yaw > 0) t.maxRight = Math.max(t.maxRight, yaw);
        if (yaw < 0) t.maxLeft = Math.max(t.maxLeft, -yaw);

        if (t.lastTime) {
          const velocity = Math.abs(yaw - t.lastYaw) / Math.max(dt, 1e-3);
          t.speed += (velocity - t.speed) * 0.2; // vitesse lissée (hibou.py)
          // Fluidité : variation brusque de la vitesse (dérivée seconde de l'angle)
          const delta = yaw - t.lastYaw;
          t.jitter.push(Math.min(4, Math.abs(delta - t.lastDelta)));
          t.lastDelta = delta;
          if (t.jitter.length > 600) t.jitter.shift();
          if (t.speed > (SPEED_LIMIT_DEG_S[c.speed] ?? 45) && modeRef.current === "camera") {
            tooFast = true;
            t.fastMoves += dt;
          }
        }
        t.lastYaw = yaw;
        t.lastTime = now;

        // Compensation : tête penchée plutôt que tournée, confirmée pendant 0,35 s.
        if (modeRef.current === "camera" && rawRollRef.current !== null) {
          const deviating = Math.abs(rawRollRef.current - baselineRollRef.current) > TILT_LIMIT;
          t.compTimer = deviating ? t.compTimer + dt : Math.max(0, t.compTimer - dt * 2.5);
          const compensating = t.compTimer >= COMPENSATION_DELAY || (t.compensating && t.compTimer > 0.15);
          if (compensating && !t.compensating) t.compensations += 1;
          t.compensating = compensating;
          tilted = compensating;
        }

        tooFar = Math.abs(yaw) > c.safety_limit;
        if (tooFar && !t.overshooting) t.overshoots += 1;
        t.overshooting = tooFar;

        if (t.step === "turn" && toward >= c.target_angle) {
          t.step = "hold";
          t.holdStart = now;
        } else if (t.step === "hold") {
          if (toward < c.target_angle - 3) {
            t.step = "turn"; // maintien interrompu
          } else if ((now - t.holdStart) / 1000 >= c.hold_seconds) {
            t.successes += 1;
            t.holds.push((now - t.holdStart) / 1000);
            t.step = "return";
          }
        } else if (t.step === "return" && Math.abs(yaw) <= CENTER_ZONE) {
          t.rep += 1;
          t.step = "turn";
          if (t.rep >= c.repetitions) {
            phaseRef.current = "rating";
            finish(false);
          }
        }
      }

      // 4. Rendu (limité)
      if (now - lastRender > 66) {
        lastRender = now;
        setView({
          yaw: yawRef.current,
          rep: t.rep,
          step: t.step,
          hold: t.step === "hold" ? Math.min(1, (now - t.holdStart) / 1000 / c.hold_seconds) : t.step === "return" ? 1 : 0,
          successes: t.successes,
          tooFast,
          tooFar,
          tilted,
        });
      }
      frame = requestAnimationFrame(loop);
    };
    frame = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(frame);
  }, [finish]);

  // ── Actions ─────────────────────────────────────────────────────────────────
  const start = async (selected: InputMode) => {
    setMode(selected);
    modeRef.current = selected;
    yawRef.current = 0;
    calibrationRef.current = [];
    rollCalibrationRef.current = [];
    if (selected === "camera") {
      const ok = await startCamera();
      if (!ok) {
        setMode("keyboard");
        modeRef.current = "keyboard";
        trackerRef.current = { ...newTracker(), startedAt: performance.now() };
        setPhase("playing");
        return;
      }
      setPhase("calibrating");
    } else {
      trackerRef.current = { ...newTracker(), startedAt: performance.now() };
      setPhase("playing");
    }
  };

  const submit = async () => {
    if (!assignment || !result) return;
    setPhase("saving");
    try {
      await saveMySession(assignment.id, result.duration, {
        ...result.metrics,
        pain_level: pain ?? 0,
        effort: effort ?? 0,
      });
      setPhase("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Enregistrement impossible.");
      setPhase("rating");
    }
  };

  const restart = () => {
    setResult(null);
    setPain(null);
    setEffort(null);
    setError(null);
    trackerRef.current = newTracker();
    setPhase("intro");
  };

  const holdKey = (side: "left" | "right", pressed: boolean) => {
    keysRef.current[side] = pressed;
  };

  // ── Rendu ───────────────────────────────────────────────────────────────────
  const reps = config.repetitions;
  const direction = view.rep % 2 === 0 ? "droite" : "gauche";
  const currentAngle = Math.abs(Math.round(view.yaw));
  const gaugePct = Math.min(1, Math.abs(view.yaw) / Math.max(config.target_angle, 1));
  const instruction =
    view.tooFar ? "Trop loin ! Reviens doucement 🛡️"
      : view.tilted ? "Garde la tête bien droite, tourne-la seulement 🙂"
      : view.tooFast ? "Plus doucement… 🪶"
        : view.step === "turn" ? `Regarde la souris… tourne doucement à ${direction} !`
          : view.step === "hold" ? "Bravo, reste comme ça…"
            : "Super ! Reviens au centre";

  return (
    <div className="min-h-screen bg-[#F3F5FA] font-outfit p-4 flex flex-col gap-4 relative overflow-hidden h-screen">
      {/* ── HEADER BAR ── */}
      <header className="relative z-10 flex items-center justify-between bg-white/80 backdrop-blur-md px-4 py-2.5 rounded-[2rem] shadow-sm border border-white/50">
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="flex items-center gap-2.5">
            <div className="w-9 h-9 relative flex-shrink-0">
              <Image src="/assets_flat/sensai-mascot.png" alt="SensAI Logo" width={36} height={36} className="w-full h-full object-contain" priority />
            </div>
            <span className="font-outfit text-xl font-black tracking-tight text-slate-900">
              Sens<span className="text-[#FF6B8B]">A</span><span className="text-[#7C3AED]">I</span>
            </span>
          </Link>
          <div className="w-px h-8 bg-slate-200"></div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-50 rounded-2xl flex items-center justify-center p-1 border border-indigo-100 shadow-sm">
              <Image src="/Assets/dashboard/Magical Owl Valley Adventure.png" width={32} height={32} alt="Hibou" className="object-cover rounded-xl" />
            </div>
            <div className="flex flex-col">
              <h2 className="text-sm font-black text-slate-800 leading-tight">Le Hibou <span className="text-slate-400 font-bold">— Chasse aux souris</span></h2>
              <span className="text-[10px] font-bold text-slate-400">Exercice de rotation cervicale</span>
            </div>
          </div>
        </div>

        <div className="flex flex-col items-center">
          <span className="text-[10px] font-bold text-slate-700 mb-1">
            Répétition <span className="font-black" data-testid="rep-counter">{Math.min(view.rep + 1, reps)} / {reps}</span>
          </span>
          <RepDots total={reps} current={view.rep} done={view.rep} />
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-50/50 rounded-full border border-blue-100 text-[10px] font-bold text-blue-600">
            🪶 Mouvement {SPEED_LABELS[config.speed]?.toLowerCase()}
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-50/50 rounded-full border border-indigo-100 text-[10px] font-bold text-indigo-600">
            🛡️ Zone sûre
          </div>
          <div className="flex items-center gap-1.5 px-4 py-2 bg-emerald-50 rounded-full border border-emerald-100 text-[11px] font-extrabold text-emerald-600 ml-2">
            {mode === "keyboard" ? <><Keyboard size={14} /> Mode clavier</> : <><Camera size={14} /> {cameraState === "on" ? "Caméra active" : "Caméra en pause"}</>}
          </div>
        </div>
      </header>

      {/* ── MAIN CONTENT ── */}
      <main className="relative z-10 flex-1 flex gap-4 min-h-0">
        <div className="flex-1 flex flex-col gap-4 min-w-0">
          <div className="flex-1 rounded-[2rem] overflow-hidden relative shadow-sm border border-white bg-gradient-to-b from-[#1E1B4B] to-[#312E81] flex items-center justify-center">
            <video ref={videoRef} className={`absolute top-0 left-0 w-full h-full object-cover transform scale-x-[-1] ${cameraState === "on" ? "opacity-60" : "opacity-0"}`} playsInline autoPlay muted />

            {/* Souris (cible) */}
            {(phase === "playing" || phase === "calibrating") && (
              <div
                className={`absolute top-1/2 -translate-y-1/2 text-6xl transition-all duration-500 ${view.step === "return" ? "opacity-30" : "opacity-100 animate-pulse"}`}
                style={{ [direction === "droite" ? "right" : "left"]: "8%" } as React.CSSProperties}
                aria-hidden
              >
                🐭
              </div>
            )}

            {/* Hibou qui suit l'angle de la tête */}
            <div
              className="relative z-10 transition-transform duration-75"
              style={{ transform: `translateX(${Math.max(-1, Math.min(1, view.yaw / 45)) * 22}vw)` }}
            >
              <Image src="/Assets/dashboard/Magical Owl Valley Adventure.png" width={260} height={260} alt="Hibou" className="drop-shadow-2xl rounded-full" />
            </div>

            {/* Écrans d'état */}
            {phase === "loading" && <Overlay><p className="text-white font-black text-xl animate-pulse">Chargement du jeu…</p></Overlay>}
            {phase === "error" && (
              <Overlay>
                <div className="bg-white rounded-3xl p-6 max-w-md text-center">
                  <div className="text-4xl">🦉</div>
                  <p className="font-black text-slate-800 mt-2">{error}</p>
                  <Link href="/dashboard" className="inline-block mt-4 px-5 py-2 rounded-full bg-[#7C3AED] text-white text-sm font-black">Retour à mon espace</Link>
                </div>
              </Overlay>
            )}
            {phase === "intro" && (
              <Overlay>
                <div className="bg-white rounded-3xl p-6 max-w-lg text-center shadow-xl">
                  <div className="text-5xl">🦉</div>
                  <h3 className="text-xl font-black text-indigo-900 mt-2">Aide le hibou à attraper les souris !</h3>
                  <p className="text-sm font-bold text-slate-500 mt-2">
                    Tourne doucement la tête vers la souris jusqu’à {config.target_angle}°, garde la position {config.hold_seconds} s,
                    puis reviens au centre. {reps} répétitions, en alternant droite et gauche.
                  </p>
                  <div className="flex gap-3 justify-center mt-5 flex-wrap">
                    <button onClick={() => start("camera")} className="px-5 py-2.5 rounded-full bg-[#7C3AED] text-white text-sm font-black flex items-center gap-2">
                      <Camera size={16} /> Jouer avec la caméra
                    </button>
                    <button onClick={() => start("keyboard")} className="px-5 py-2.5 rounded-full bg-slate-100 text-slate-700 text-sm font-black flex items-center gap-2">
                      <Keyboard size={16} /> Jouer au clavier
                    </button>
                  </div>
                  {cameraState === "failed" && (
                    <p className="text-xs font-bold text-amber-600 mt-3">Caméra indisponible : le mode clavier a été activé.</p>
                  )}
                </div>
              </Overlay>
            )}
            {phase === "calibrating" && (
              <Overlay transparent>
                <p className="text-white font-black text-lg bg-black/40 px-5 py-3 rounded-full">
                  {faceVisible ? "Regarde droit devant… calibrage 📷" : "Je ne vois pas ton visage, place-toi face à la caméra"}
                </p>
              </Overlay>
            )}
            {phase === "rating" && result && (
              <Overlay>
                <div className="bg-white rounded-3xl p-6 max-w-lg w-full text-center shadow-xl">
                  <h3 className="text-xl font-black text-indigo-900">{result.metrics.completed ? "Bravo, exercice terminé ! 🎉" : "Séance arrêtée"}</h3>
                  <p className="text-sm font-bold text-slate-500 mt-1">
                    {result.metrics.repetitions} / {reps} souris attrapées · score {result.metrics.score}
                  </p>
                  <RatingRow label="As-tu eu mal ?" value={pain} onChange={setPain} faces={["😀", "🙂", "😐", "😕", "😣", "😭"]} testId="pain" />
                  <RatingRow label="C’était difficile ?" value={effort} onChange={setEffort} faces={["😴", "🙂", "😊", "😤", "🥵", "🤯"]} testId="effort" />
                  {error && <p className="text-xs font-bold text-rose-600 mt-2">{error}</p>}
                  <button
                    onClick={submit}
                    disabled={pain === null || effort === null}
                    className="mt-5 px-6 py-2.5 rounded-full bg-[#7C3AED] disabled:opacity-40 text-white text-sm font-black"
                  >
                    Envoyer à mon thérapeute
                  </button>
                </div>
              </Overlay>
            )}
            {phase === "saving" && <Overlay><p className="text-white font-black text-xl animate-pulse">Enregistrement…</p></Overlay>}
            {phase === "done" && result && (
              <Overlay>
                <div className="bg-white rounded-3xl p-6 max-w-md text-center shadow-xl">
                  <div className="text-5xl">🏆</div>
                  <h3 className="text-xl font-black text-indigo-900 mt-2">Séance enregistrée !</h3>
                  <p className="text-sm font-bold text-slate-500 mt-1">Ton thérapeute pourra voir tes progrès.</p>
                  <div className="flex gap-3 justify-center mt-5">
                    <button onClick={restart} className="px-5 py-2.5 rounded-full bg-slate-100 text-slate-700 text-sm font-black">Rejouer</button>
                    <Link href="/dashboard" className="px-5 py-2.5 rounded-full bg-[#7C3AED] text-white text-sm font-black">Retour à mon espace</Link>
                  </div>
                </div>
              </Overlay>
            )}

            {phase === "playing" && (
              <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-white/95 backdrop-blur-sm px-10 py-3 rounded-full shadow-lg border border-white/50 flex items-center gap-4 z-20">
                <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">🦉</div>
                <div className="flex flex-col text-center">
                  <span className="text-[15px] font-black text-indigo-900 leading-tight" data-testid="instruction">{instruction}</span>
                  <span className="text-[11px] font-bold text-indigo-400">
                    {mode === "keyboard" ? "Maintiens la flèche ← ou → du clavier" : faceVisible ? "Bouge seulement la tête" : "Visage non détecté"}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* FOOTER BAR */}
          <div className="h-[72px] flex items-center justify-between px-2 gap-3">
            <button
              onClick={() => (phase === "playing" ? finish(true) : window.history.back())}
              className="h-full px-8 bg-fuchsia-50 hover:bg-fuchsia-100 rounded-full border-2 border-fuchsia-100 text-fuchsia-600 flex items-center gap-2 font-black transition-colors shadow-sm"
            >
              <span className="w-6 h-6 rounded-full bg-fuchsia-500 text-white flex items-center justify-center text-xs">♥</span>
              J&apos;ai mal / Stop
            </button>

            {mode === "keyboard" && phase === "playing" ? (
              <div className="h-full flex items-center gap-3">
                {(["left", "right"] as const).map((side) => (
                  <button
                    key={side}
                    onPointerDown={() => holdKey(side, true)}
                    onPointerUp={() => holdKey(side, false)}
                    onPointerLeave={() => holdKey(side, false)}
                    className="h-full px-6 bg-white rounded-full shadow-sm border border-slate-100 font-black text-indigo-600 select-none"
                  >
                    {side === "left" ? "◀ Gauche" : "Droite ▶"}
                  </button>
                ))}
              </div>
            ) : (
              <div className="h-full px-8 bg-white rounded-full flex items-center gap-3 shadow-sm border border-slate-100">
                <span className="text-indigo-200">🌿</span>
                <RepDots total={reps} current={view.rep} done={view.rep} large />
                <span className="text-indigo-200">🪶</span>
              </div>
            )}

            <div className="h-full px-6 bg-white rounded-[2rem] flex items-center gap-6 shadow-sm border border-slate-100">
              <div className="flex flex-col items-center">
                <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wide">🎯 Réussites</span>
                <span className="text-lg font-black text-slate-800 leading-none mt-0.5" data-testid="successes">{view.successes}</span>
              </div>
              <div className="w-px h-8 bg-slate-100"></div>
              <div className="flex flex-col items-center">
                <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wide">✋ Maintien</span>
                <span className="text-lg font-black text-slate-800 leading-none mt-0.5">{Math.round(view.hold * 100)}%</span>
              </div>
            </div>
          </div>
        </div>

        {/* ── RIGHT SIDEBAR ── */}
        <aside className="w-[320px] bg-white rounded-[2.5rem] p-6 shadow-sm border border-slate-100 flex flex-col relative overflow-hidden">
          <div className="flex items-center gap-2 mb-2 text-indigo-600">
            <span className="text-xl">🎯</span>
            <h3 className="font-black text-xl">Objectif</h3>
          </div>
          <p className="text-sm font-bold text-slate-600 mb-6">Tourne doucement à {direction}</p>

          <div className="flex gap-3 mb-8">
            <div className="flex-1 bg-indigo-50/50 rounded-2xl p-3 flex flex-col items-center justify-center border border-indigo-50">
              <span className="text-indigo-500 font-black text-xl mb-1 flex items-center gap-1"><span className="text-sm">📐</span> {config.target_angle}°</span>
              <span className="text-[10px] font-bold text-slate-400">Angle cible</span>
            </div>
            <div className="flex-1 bg-indigo-50/50 rounded-2xl p-3 flex flex-col items-center justify-center border border-indigo-50">
              <span className="text-indigo-500 font-black text-xl mb-1 flex items-center gap-1"><span className="text-sm">⏱️</span> {config.hold_seconds} s</span>
              <span className="text-[10px] font-bold text-slate-400">Maintien</span>
            </div>
          </div>

          <div className="flex-1 flex items-center justify-center relative mb-8">
            <svg className="w-48 h-48 absolute -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="44" fill="none" stroke="#E2E8F0" strokeWidth="12" />
              <circle
                cx="50" cy="50" r="44" fill="none"
                stroke={view.tooFar ? "#F43F5E" : gaugePct >= 1 ? "#10B981" : "#6366F1"}
                strokeWidth="12" strokeDasharray="276" strokeDashoffset={276 - 276 * gaugePct} strokeLinecap="round"
              />
            </svg>
            <div className="flex flex-col items-center">
              <span className="text-4xl font-black text-slate-800" data-testid="angle">{currentAngle}°</span>
              <span className="text-xs font-bold text-slate-400">/ {config.target_angle}°</span>
            </div>
          </div>

          <div className={`rounded-2xl p-3 flex items-center gap-3 border ${view.tooFar ? "bg-rose-50 border-rose-200" : "bg-amber-50 border-amber-100"}`}>
            <div className="w-8 h-8 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center flex-shrink-0">🛡️</div>
            <div className="flex flex-col">
              <span className="text-xs font-black text-amber-900">Limite {config.safety_limit}°</span>
              <span className="text-[10px] font-bold text-amber-600/70">(fixée par ton kinésithérapeute)</span>
            </div>
          </div>
        </aside>
      </main>
    </div>
  );
}

function Overlay({ children, transparent }: { children: React.ReactNode; transparent?: boolean }) {
  return (
    <div className={`absolute inset-0 z-30 flex items-center justify-center p-6 ${transparent ? "" : "bg-slate-900/70"}`}>
      {children}
    </div>
  );
}

function RepDots({ total, current, done, large }: { total: number; current: number; done: number; large?: boolean }) {
  const size = large ? "w-5 h-5 text-[10px]" : "w-4 h-4 text-[8px]";
  return (
    <div className="flex items-center gap-1.5">
      {Array.from({ length: total }).map((_, i) =>
        i < done ? (
          <div key={i} className={`${size} rounded-full bg-emerald-400 text-white flex items-center justify-center`}>✓</div>
        ) : i === current ? (
          <div key={i} className={`${large ? "w-7 h-7 text-[12px]" : "w-5 h-5 text-[10px]"} rounded-full bg-indigo-500 text-white flex items-center justify-center font-bold shadow-md shadow-indigo-200`}>{i + 1}</div>
        ) : (
          <div key={i} className={`${size} rounded-full bg-slate-100 flex items-center justify-center text-slate-300`}>•</div>
        ),
      )}
    </div>
  );
}
