"use client";

// ──────────────────────────────────────────────────────────────────────────────
// Le Gardien des Lucioles — exercice d'abduction de l'épaule (jeu de Maram)
// Le jeu (Phaser + MediaPipe Pose) tourne dans /games/gardien-lucioles/ ; cette
// page l'encadre : elle lui passe les réglages du thérapeute, reçoit le résumé de
// la séance (postMessage), demande l'auto-évaluation puis enregistre la séance
// dans le backend (POST /me/sessions).
// ──────────────────────────────────────────────────────────────────────────────

import React, { useCallback, useEffect, useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { getMyGames, saveMySession, type PatientGame, type SessionMetrics } from "@/lib/api";
import { luciolesConfig } from "@/lib/games";
import { useRequireAuth } from "@/lib/useAuth";
import RatingRow from "./RatingRow";

type Phase = "loading" | "playing" | "rating" | "saving" | "done" | "error";
type Summary = { duration_sec: number; metrics: SessionMetrics };
type GameMessage =
  | { source: "gardien-lucioles"; type: "started"; input: string }
  | { source: "gardien-lucioles"; type: "progress"; reps: number; target: number }
  | ({ source: "gardien-lucioles"; type: "done" } & Summary);

export default function LuciolesGame() {
  const { me } = useRequireAuth("patient");
  const frameRef = useRef<HTMLIFrameElement>(null);
  const [phase, setPhase] = useState<Phase>("loading");
  const [error, setError] = useState<string | null>(null);
  const [assignment, setAssignment] = useState<PatientGame | null>(null);
  const [round, setRound] = useState(0); // recharge le jeu pour « Rejouer »
  const [progress, setProgress] = useState(0);
  const [started, setStarted] = useState(false);
  const [result, setResult] = useState<Summary | null>(null);
  const [pain, setPain] = useState<number | null>(null);
  const [effort, setEffort] = useState<number | null>(null);

  const config = luciolesConfig(assignment?.configuration);

  // ── Jeu assigné et réglages du thérapeute ───────────────────────────────────
  useEffect(() => {
    if (!me) return;
    const pgParam = Number(new URLSearchParams(window.location.search).get("pg"));
    getMyGames()
      .then((games) => {
        const found =
          games.find((g) => g.id === pgParam) ?? games.find((g) => g.game_slug === "gardien-lucioles");
        if (!found) {
          setError("Le Gardien des Lucioles ne t’a pas encore été attribué par ton thérapeute.");
          setPhase("error");
          return;
        }
        if (found.configuration?.active === false) {
          setError("Ce jeu est en pause : ton thérapeute l’a désactivé pour le moment.");
          setPhase("error");
          return;
        }
        setAssignment(found);
        setPhase("playing");
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Chargement impossible.");
        setPhase("error");
      });
  }, [me]);

  // ── Messages du jeu ─────────────────────────────────────────────────────────
  useEffect(() => {
    const onMessage = (event: MessageEvent<GameMessage>) => {
      if (event.origin !== window.location.origin || event.data?.source !== "gardien-lucioles") return;
      const data = event.data;
      if (data.type === "started") setStarted(true);
      if (data.type === "progress") setProgress(data.reps);
      if (data.type === "done") {
        setResult({ duration_sec: data.duration_sec, metrics: data.metrics });
        setPhase("rating");
      }
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, []);

  const stop = useCallback(() => {
    if (phase === "playing" && started) {
      frameRef.current?.contentWindow?.postMessage({ source: "sensai", type: "stop" }, window.location.origin);
    } else {
      window.history.back();
    }
  }, [phase, started]);

  const submit = async () => {
    if (!assignment || !result) return;
    setPhase("saving");
    try {
      await saveMySession(assignment.id, result.duration_sec, {
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
    setProgress(0);
    setStarted(false);
    setRound((r) => r + 1);
    setPhase("playing");
  };

  const params = new URLSearchParams({
    side: config.affected_arm,
    dir: config.direction,
    thr: String(config.target_angle),
    elb: String(config.elbow_min),
    rest: String(config.rest_tolerance),
    reps: String(config.repetitions),
    hold: String(config.hold_seconds),
  });
  const armLabel = config.affected_arm === "BI" ? "les deux bras" : config.affected_arm === "L" ? "bras gauche" : "bras droit";
  const exercise = ({ side: "Abduction de l’épaule", front: "Flexion de l’épaule", mid: "Flexion-adduction de l’épaule", any: "Élévation du bras" } as Record<string, string>)[config.direction] ?? "Élévation du bras";

  return (
    <div className="min-h-screen bg-[#F3F5FA] font-outfit p-4 flex flex-col gap-4 h-screen">
      {/* ── EN-TÊTE ── */}
      <header className="flex items-center justify-between bg-white/80 backdrop-blur-md px-4 py-2.5 rounded-[2rem] shadow-sm border border-white/50 gap-4">
        <div className="flex items-center gap-6 min-w-0">
          <Link href="/dashboard" className="flex items-center gap-2.5">
            <Image src="/assets_flat/sensai-mascot.png" alt="SensAI" width={36} height={36} className="w-9 h-9 object-contain" priority />
            <span className="text-xl font-black tracking-tight text-slate-900">
              Sens<span className="text-[#FF6B8B]">A</span><span className="text-[#7C3AED]">I</span>
            </span>
          </Link>
          <div className="w-px h-8 bg-slate-200" />
          <div className="flex items-center gap-3 min-w-0">
            <Image src="/Assets/dashboard/Chibi Sky Quest to the Star.png" width={40} height={40} alt="" className="w-10 h-10 object-cover rounded-2xl" />
            <div className="flex flex-col min-w-0">
              <h2 className="text-sm font-black text-slate-800 leading-tight truncate">Le Gardien des Lucioles</h2>
              <span className="text-[10px] font-bold text-slate-400">{exercise} · {armLabel}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap justify-end">
          <span className="px-3 py-1.5 bg-indigo-50 rounded-full border border-indigo-100 text-[11px] font-extrabold text-indigo-600">
            ✨ <span data-testid="lucioles-progress">{progress} / {config.repetitions}</span> lucioles
          </span>
          <span className="px-3 py-1.5 bg-amber-50 rounded-full border border-amber-100 text-[11px] font-extrabold text-amber-700">
            🎯 {config.target_angle}°
          </span>
          <button
            onClick={stop}
            className="px-4 py-2 bg-fuchsia-50 hover:bg-fuchsia-100 rounded-full border-2 border-fuchsia-100 text-fuchsia-600 text-xs font-black"
          >
            ♥ J&apos;ai mal / Stop
          </button>
        </div>
      </header>

      {/* ── JEU ── */}
      <main className="flex-1 min-h-0 rounded-[2rem] overflow-hidden relative shadow-sm border border-white bg-[#8fd8ff]">
        {assignment && (
          <iframe
            key={round}
            ref={frameRef}
            title="Le Gardien des Lucioles"
            src={`/games/gardien-lucioles/index.html?${params.toString()}`}
            allow="camera; autoplay"
            className="absolute inset-0 w-full h-full border-0"
          />
        )}

        {phase === "loading" && <Overlay><p className="text-white font-black text-xl animate-pulse">Chargement du jeu…</p></Overlay>}
        {phase === "error" && (
          <Overlay>
            <div className="bg-white rounded-3xl p-6 max-w-md text-center">
              <div className="text-4xl">✨</div>
              <p className="font-black text-slate-800 mt-2">{error}</p>
              <Link href="/dashboard" className="inline-block mt-4 px-5 py-2 rounded-full bg-[#7C3AED] text-white text-sm font-black">Retour à mon espace</Link>
            </div>
          </Overlay>
        )}
        {phase === "rating" && result && (
          <Overlay>
            <div className="bg-white rounded-3xl p-6 max-w-lg w-full text-center shadow-xl">
              <h3 className="text-xl font-black text-indigo-900">
                {result.metrics.completed ? "Bravo, toutes les lucioles sont rentrées ! 🎉" : "Séance arrêtée"}
              </h3>
              <p className="text-sm font-bold text-slate-500 mt-1">
                {result.metrics.repetitions} / {config.repetitions} lucioles · bras levé jusqu’à {String(result.metrics.abduction_max ?? 0)}° · score {result.metrics.score}
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
        {phase === "done" && (
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
      </main>
    </div>
  );
}

function Overlay({ children }: { children: React.ReactNode }) {
  return <div className="absolute inset-0 z-30 flex items-center justify-center p-6 bg-slate-900/70">{children}</div>;
}
