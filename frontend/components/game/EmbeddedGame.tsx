"use client";

// ──────────────────────────────────────────────────────────────────────────────
// Cadre commun des jeux « embarqués » (jeux autonomes de l'équipe, en HTML) :
// la page passe au jeu les réglages du thérapeute (paramètres d'URL), reçoit le
// résumé de la séance (postMessage), demande l'auto-évaluation puis enregistre la
// séance dans le backend (POST /me/sessions).
// Utilisé par Le Gardien des Lucioles et La Danse des Lucioles (jeux de Maram).
// ──────────────────────────────────────────────────────────────────────────────

import React, { useCallback, useEffect, useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { getMyGames, saveMySession, type PatientGame, type SessionMetrics } from "@/lib/api";
import type { GameConfig } from "@/lib/api";
import { useRequireAuth } from "@/lib/useAuth";
import RatingRow from "./RatingRow";

type Phase = "loading" | "playing" | "rating" | "saving" | "done" | "error";
type Summary = { duration_sec: number; metrics: SessionMetrics };
type GameMessage =
  | { source: string; type: "started"; input: string }
  | { source: string; type: "progress"; reps: number; target: number }
  | ({ source: string; type: "done" } & Summary);

export type EmbeddedGameSpec<C> = {
  slug: string; // identifiant du jeu (backend) et dossier public/games/<slug>/
  title: string;
  image: string;
  unit: string; // « lucioles », « danses »…
  config: (raw?: GameConfig) => C;
  params: (config: C) => Record<string, string>;
  target: (config: C) => number;
  subtitle: (config: C) => string;
  badge?: (config: C) => string | null;
  doneTitle: string;
  doneLine: (metrics: SessionMetrics, config: C) => string;
};

export default function EmbeddedGame<C>({ spec }: { spec: EmbeddedGameSpec<C> }) {
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

  const config = spec.config(assignment?.configuration);

  // ── Jeu assigné et réglages du thérapeute ───────────────────────────────────
  useEffect(() => {
    if (!me) return;
    const pgParam = Number(new URLSearchParams(window.location.search).get("pg"));
    getMyGames()
      .then((games) => {
        const found =
          games.find((g) => g.id === pgParam) ?? games.find((g) => g.game_slug === spec.slug);
        if (!found) {
          setError(`${spec.title} ne t’a pas encore été attribué par ton thérapeute.`);
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
  }, [me, spec.slug, spec.title]);

  // ── Messages du jeu ─────────────────────────────────────────────────────────
  useEffect(() => {
    const onMessage = (event: MessageEvent<GameMessage>) => {
      if (event.origin !== window.location.origin || event.data?.source !== spec.slug) return;
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
  }, [spec.slug]);

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

  const params = new URLSearchParams(spec.params(config));
  const target = spec.target(config);
  const badge = spec.badge?.(config);
  const isCastle = spec.slug === "gardien-chateau";
  const isLucioles = spec.slug === "danse-lucioles";

  return (
    <div className={`min-h-screen font-outfit flex flex-col h-screen ${isCastle ? "bg-[#EEF2FA] p-4 gap-3" : isLucioles ? "bg-[#e9e9ff] p-4 gap-3" : "bg-[#F3F5FA] p-4 gap-4"}`}>
      {/* ── EN-TÊTE ── */}
      <header className={`flex items-center justify-between bg-white/90 backdrop-blur-md px-6 py-2.5 rounded-full shadow-sm border border-white/80 gap-4 ${isLucioles ? "mx-[5vw] gap-2 px-5 py-2 max-md:flex-wrap" : isCastle ? "mx-[4vw]" : ""}`}>
        <div className={`flex items-center min-w-0 ${isLucioles ? "gap-4" : isCastle ? "gap-3" : "gap-6"}`}>
          <Link href="/dashboard" className="flex items-center shrink-0 gap-2">
            <Image
              src="/assets_flat/sensai-mascot.png"
              alt="SensAI"
              width={38}
              height={38}
              className="w-9 h-9 object-contain"
              priority
            />
            <span className="text-xl font-black tracking-tight text-slate-900">
              Sens<span className="text-[#FF6B8B]">A</span><span className="text-[#7C3AED]">I</span>
            </span>
          </Link>
          <div className="w-px h-6 bg-slate-200 mx-1" />
          <div className="flex items-center min-w-0 gap-2.5">
            <Image src={spec.image} width={38} height={38} alt="" className="w-9 h-9 shrink-0 rounded-2xl object-contain bg-indigo-50/60 shadow-sm" />
            <div className="flex flex-col min-w-0">
              <h2 className="text-sm font-extrabold text-slate-800 leading-tight truncate">{spec.title}</h2>
              <span className="text-xs font-semibold text-slate-400 truncate">{spec.subtitle(config)}</span>
            </div>
          </div>
        </div>
        <div className={`flex items-center justify-end shrink-0 gap-2.5 ${isLucioles ? "gap-1.5 flex-nowrap max-md:flex-wrap" : ""}`}>
          <span className={`px-4 py-1.5 text-xs bg-[#EEF2FF] rounded-full border border-indigo-100 font-extrabold text-[#4F46E5] flex items-center gap-1.5 shadow-sm ${spec.slug === "danse-lucioles" ? "hidden" : ""}`}>
            ⭐ <span data-testid={isCastle ? "castle-progress" : "lucioles-progress"}>{progress} / {target}</span> {spec.unit}
          </span>
          {badge && (
            <span className={`px-4 py-1.5 text-xs bg-[#FFF7ED] rounded-full border border-orange-100 font-extrabold text-[#C2410C] flex items-center gap-1.5 shadow-sm ${spec.slug === "danse-lucioles" ? "hidden" : ""}`}>
              {badge}
            </span>
          )}
          <button
            onClick={stop}
            className="px-4 py-1.5 text-xs bg-[#FDF2F8] hover:bg-pink-100 rounded-full border border-pink-100 text-[#DB2777] font-black whitespace-nowrap flex items-center gap-1.5 shadow-sm transition-colors"
          >
            💖 J&apos;ai mal / Stop
          </button>
        </div>
      </header>

      {/* ── JEU ── */}
      <main className={`flex-1 min-h-0 rounded-[2.5rem] overflow-hidden relative shadow-sm border border-white/80 ${isLucioles ? "mx-[5vw] bg-[#e9e9ff]" : isCastle ? "mx-[4vw] bg-[#EEF2FA]" : "bg-[#8fd8ff]"}`}>
        {assignment && (
          <iframe
            key={round}
            ref={frameRef}
            title={spec.title}
            src={`/games/${spec.slug}/index.html?${params.toString()}`}
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
                {result.metrics.completed ? spec.doneTitle : "Séance arrêtée"}
              </h3>
              <p className="text-sm font-bold text-slate-500 mt-1">
                {spec.doneLine(result.metrics, config)}
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
