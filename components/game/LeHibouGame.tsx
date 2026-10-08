"use client";

import React, { useEffect, useRef, useState } from "react";
import Image from "next/image";
import { Camera } from "lucide-react";

export default function LeHibouGame() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const gameRef = useRef<HTMLDivElement>(null);
  const [isReady, setIsReady] = useState(false);
  const [currentYaw, setCurrentYaw] = useState(0);

  // Start camera for AR background
  useEffect(() => {
    let stream: MediaStream | null = null;
    if (typeof navigator !== "undefined" && navigator.mediaDevices) {
      navigator.mediaDevices
        .getUserMedia({ video: true })
        .then((s) => {
          stream = s;
          if (videoRef.current) {
            videoRef.current.srcObject = s;
            setIsReady(true);
          }
        })
        .catch((err) => console.error("Camera error:", err));
    }
    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#F3F5FA] font-outfit p-4 flex flex-col gap-4 relative overflow-hidden h-screen">
      {/* Background decorations */}
      <div className="absolute top-0 left-0 w-full h-full pointer-events-none opacity-40 z-0">
         {/* You can put clouds or abstract blobs here */}
      </div>

      {/* ── HEADER BAR ── */}
      <header className="relative z-10 flex items-center justify-between bg-white/80 backdrop-blur-md px-4 py-2.5 rounded-[2rem] shadow-sm border border-white/50">
        
        {/* Logo & Game Title */}
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 relative flex-shrink-0">
              <Image src="/assets_flat/sensai-mascot.png" alt="SensAI Logo" width={36} height={36} className="w-full h-full object-contain" priority />
            </div>
            <span className="font-outfit text-xl font-black tracking-tight text-slate-900">
              Sens<span className="text-[#FF6B8B]">A</span><span className="text-[#7C3AED]">I</span>
            </span>
          </div>
          
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

        {/* Repetitions */}
        <div className="flex flex-col items-center">
          <span className="text-[10px] font-bold text-slate-700 mb-1">Répétition <span className="font-black">3 / 6</span></span>
          <div className="flex items-center gap-1.5">
            <div className="w-4 h-4 rounded-full bg-emerald-400 text-white flex items-center justify-center text-[8px]">✓</div>
            <div className="w-4 h-4 rounded-full bg-emerald-400 text-white flex items-center justify-center text-[8px]">✓</div>
            <div className="w-5 h-5 rounded-full bg-indigo-500 text-white flex items-center justify-center text-[10px] font-bold shadow-md shadow-indigo-200">3</div>
            <div className="w-4 h-4 rounded-full bg-slate-100 flex items-center justify-center text-[8px] text-slate-300">🔒</div>
            <div className="w-4 h-4 rounded-full bg-slate-100 flex items-center justify-center text-[8px] text-slate-300">🔒</div>
            <div className="w-4 h-4 rounded-full bg-slate-100 flex items-center justify-center text-[8px] text-slate-300">🔒</div>
          </div>
        </div>

        {/* Badges & Camera */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-50/50 rounded-full border border-blue-100 text-[10px] font-bold text-blue-600">
            🪶 Mouvement lent
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-50/50 rounded-full border border-indigo-100 text-[10px] font-bold text-indigo-600">
            🛡️ Zone sûre
          </div>
          <div className="flex items-center gap-1.5 px-4 py-2 bg-emerald-50 rounded-full border border-emerald-100 text-[11px] font-extrabold text-emerald-600 ml-2">
            <Camera size={14} /> {isReady ? "Caméra active" : "Caméra en pause"}
          </div>
        </div>
      </header>

      {/* ── MAIN CONTENT ── */}
      <main className="relative z-10 flex-1 flex gap-4 min-h-0">
        
        {/* Left Side: Game & Footer Controls */}
        <div className="flex-1 flex flex-col gap-4 min-w-0">
          
          {/* GAME CANVAS */}
          <div className="flex-1 rounded-[2rem] overflow-hidden relative shadow-sm border border-white bg-slate-900 flex items-center justify-center">
             
             {/* Live Camera Feed */}
             <video 
               ref={videoRef} 
               className="absolute top-0 left-0 w-full h-full object-cover transform scale-x-[-1]" 
               playsInline 
               autoPlay 
               muted 
             />

             {!isReady && (
               <div className="absolute inset-0 bg-slate-900/80 flex items-center justify-center">
                 <span className="text-white font-bold animate-pulse">Autorisation de la caméra requise...</span>
               </div>
             )}

             {/* The Phaser canvas will go here on top of the video */}
             <div ref={gameRef} className="absolute inset-0 z-10 pointer-events-none flex items-center justify-center">
                {/* Placeholder owl for AR effect preview */}
                {isReady && (
                   <Image src="/Assets/dashboard/Magical Owl Valley Adventure.png" width={400} height={400} alt="Owl" className="drop-shadow-2xl opacity-70 mix-blend-screen" />
                )}
             </div>
             
             {/* Instruction Overlay */}
             <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-white/95 backdrop-blur-sm px-10 py-3 rounded-full shadow-lg border border-white/50 flex items-center gap-4">
                <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">🦉</div>
                <div className="flex flex-col text-center">
                  <span className="text-[15px] font-black text-indigo-900 leading-tight">Regarde la souris... doucement !</span>
                  <span className="text-[11px] font-bold text-indigo-400">Puis reviens au centre</span>
                </div>
             </div>
          </div>

          {/* FOOTER BAR */}
          <div className="h-[72px] flex items-center justify-between px-2">
             
             {/* Stop Button */}
             <button onClick={() => window.history.back()} className="h-full px-8 bg-fuchsia-50 hover:bg-fuchsia-100 rounded-full border-2 border-fuchsia-100 text-fuchsia-600 flex items-center gap-2 font-black transition-colors shadow-sm">
                <span className="w-6 h-6 rounded-full bg-fuchsia-500 text-white flex items-center justify-center text-xs">♥</span>
                J'ai mal / Stop
             </button>

             {/* Bottom progress (duplicate of top conceptually, based on inspo) */}
             <div className="h-full px-8 bg-white rounded-full flex items-center gap-3 shadow-sm border border-slate-100">
                <span className="text-indigo-200">🌿</span>
                <div className="w-5 h-5 rounded-full bg-emerald-400 text-white flex items-center justify-center text-[10px]">✓</div>
                <div className="w-5 h-5 rounded-full bg-emerald-400 text-white flex items-center justify-center text-[10px]">✓</div>
                <div className="w-7 h-7 rounded-full bg-indigo-500 text-white flex items-center justify-center text-[12px] font-bold shadow-md shadow-indigo-200">3</div>
                <div className="w-5 h-5 rounded-full bg-slate-100 flex items-center justify-center text-[10px] text-slate-300">🔒</div>
                <div className="w-5 h-5 rounded-full bg-slate-100 flex items-center justify-center text-[10px] text-slate-300">🔒</div>
                <div className="w-5 h-5 rounded-full bg-slate-100 flex items-center justify-center text-[10px] text-slate-300">🔒</div>
                <span className="text-indigo-200">🪶</span>
             </div>

             {/* Stats */}
             <div className="h-full px-6 bg-white rounded-[2rem] flex items-center gap-6 shadow-sm border border-slate-100">
                <div className="flex flex-col items-center">
                  <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wide flex items-center gap-1"><span className="text-indigo-400">🎯</span> Précision</span>
                  <span className="text-lg font-black text-slate-800 leading-none mt-0.5">92%</span>
                  <div className="flex gap-0.5 mt-1 text-yellow-400 text-[8px]">★★☆</div>
                </div>
                <div className="w-px h-8 bg-slate-100"></div>
                <div className="flex flex-col items-center">
                  <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wide flex items-center gap-1"><span className="text-blue-400">✋</span> Contrôle</span>
                  <span className="text-lg font-black text-slate-800 leading-none mt-0.5">4/5</span>
                  <div className="flex gap-0.5 mt-1 text-indigo-400 text-[8px]">★★★★☆</div>
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
          <p className="text-sm font-bold text-slate-600 mb-6">Tourne doucement à droite</p>

          <div className="flex gap-3 mb-8">
            <div className="flex-1 bg-indigo-50/50 rounded-2xl p-3 flex flex-col items-center justify-center border border-indigo-50">
              <span className="text-indigo-500 font-black text-xl mb-1 flex items-center gap-1"><span className="text-sm">📐</span> 30°</span>
              <span className="text-[10px] font-bold text-slate-400">Angle cible</span>
            </div>
            <div className="flex-1 bg-indigo-50/50 rounded-2xl p-3 flex flex-col items-center justify-center border border-indigo-50">
              <span className="text-indigo-500 font-black text-xl mb-1 flex items-center gap-1"><span className="text-sm">⏱️</span> 3 s</span>
              <span className="text-[10px] font-bold text-slate-400">Maintien</span>
            </div>
          </div>

          {/* Circular Gauge Placeholder */}
          <div className="flex-1 flex items-center justify-center relative mb-8">
             {/* Background Track */}
             <div className="w-48 h-48 rounded-full border-[12px] border-slate-50 absolute"></div>
             {/* Progress Track (approximate with conic gradient or svg in real code) */}
             <svg className="w-48 h-48 absolute -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="44" fill="none" stroke="#E2E8F0" strokeWidth="12" />
                <circle cx="50" cy="50" r="44" fill="none" stroke="#6366F1" strokeWidth="12" strokeDasharray="276" strokeDashoffset="100" strokeLinecap="round" />
             </svg>
             {/* Number */}
             <div className="flex flex-col items-center">
               <span className="text-4xl font-black text-slate-800">22°</span>
               <span className="text-xs font-bold text-slate-400">/ 30°</span>
             </div>
             {/* Refresh icon decoration */}
             <div className="absolute top-4 right-4 text-indigo-400">↻</div>
          </div>

          {/* Warning Footer */}
          <div className="bg-amber-50 rounded-2xl p-3 flex items-center gap-3 border border-amber-100">
            <div className="w-8 h-8 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center flex-shrink-0">
              🛡️
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-black text-amber-900">Limite 35°</span>
              <span className="text-[10px] font-bold text-amber-600/70">(kinésithérapeute)</span>
            </div>
          </div>

        </aside>
      </main>
    </div>
  );
}
