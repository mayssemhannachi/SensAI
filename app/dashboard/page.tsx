"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { 
  Copy, Eye, Calendar, Gamepad2, BarChart2,
  ChevronDown, Check
} from "lucide-react";

const exercises = [
  {
    title: "Le Hibou",
    image: "/Assets/dashboard/Magical Owl Valley Adventure.png", // Placeholder image until you add the owl graphic
    category: "Rééducation cervicale",
    limb: "Tête / Cou",
    level: 1,
    active: true,
    href: "/dashboard/game/le-hibou",
  },
  {
    title: "Color Touch",
    image: "/Assets/dashboard/ex-color-touch.png",
    category: "Jeu de couleur",
    limb: "Main droite",
    level: 2,
    active: true,
  },
  {
    title: "Reaction Speed",
    image: "/Assets/dashboard/ex-reaction-speed.png",
    category: "Jeu de rapidité",
    limb: "Main gauche",
    level: 3,
    active: true,
  },
  {
    title: "Sequence Memory",
    image: "/Assets/dashboard/ex-sequence-memory.png",
    category: "Jeu de mémoire",
    limb: "Œil / Vision",
    level: 2,
    active: true,
  },
  {
    title: "Tremor Trace",
    image: "/Assets/dashboard/ex-tremor-trace.png",
    category: "Jeu de précision",
    limb: "Main gauche",
    level: 1,
    active: true,
  },
  {
    title: "Target Tracking",
    image: "/Assets/dashboard/ex-target-tracking.png",
    category: "Jeu de suivi",
    limb: "Tête / Cou",
    level: 1,
    active: true,
  },
  {
    title: "Balance Builder",
    image: "/Assets/dashboard/ex-balance-builder.png",
    category: "Jeu d'équilibre",
    limb: "Jambe gauche",
    lockedAt: 4,
    active: false,
  },
  {
    title: "Puzzle Motion",
    image: "/Assets/dashboard/ex-puzzle-motion.png",
    category: "Jeu de coordination",
    limb: "Corps entier",
    lockedAt: 5,
    active: false,
  },
];

export default function DashboardPage() {
  const [copied, setCopied] = useState(false);
  const [showCode, setShowCode] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText("7F3A-89K2");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className="min-h-screen bg-[#EEF2FA] font-outfit relative overflow-hidden"
      style={{ minWidth: 760 }}
    >
      {/* ── BACKGROUND STICKERS ── */}
      <div className="absolute top-[28%] left-[2%] pointer-events-none -rotate-12 z-10" style={{ mixBlendMode: 'multiply' }}>
        <Image src="/Assets/dashboard/Playful Pink Lightning Bolt.png" width={48} height={48} alt="Lightning" />
      </div>
      <div className="absolute bottom-[3%] left-[1.5%] pointer-events-none z-10 -rotate-3" style={{ mixBlendMode: 'multiply', filter: 'contrast(1.2) brightness(1.1)' }}>
        <Image src="/Assets/dashboard/Tu fais des progrès, adorable sticker.png" width={160} height={160} alt="Tu fais des progrès" />
      </div>
      <div className="absolute top-[5%] right-[1%] pointer-events-none -rotate-12 z-10 opacity-70" style={{ mixBlendMode: 'multiply' }}>
        <Image src="/Assets/dashboard/Pastel Blue Looping Brushstroke.png" width={130} height={130} alt="Brushstroke" />
      </div>
      <div className="absolute bottom-[8%] right-[2%] pointer-events-none rotate-12 z-10" style={{ mixBlendMode: 'multiply' }}>
        <Image src="/Assets/dashboard/Playful Purple Checkmark Doodle.png" width={65} height={65} alt="Checkmark" />
      </div>

      <div className="max-w-[1100px] mx-auto px-6 py-5 flex flex-col gap-4 relative z-20">

        {/* ── TOP BAR ──────────────────────────────────────────── */}
        <div className="flex justify-end items-center gap-3 relative z-30">
          {/* Patient Code pill */}
          <div className="relative">
            <div className="flex items-center bg-white rounded-full shadow-sm border border-slate-100 pl-1 pr-2 py-1 gap-2">
              <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-transparent">
                <Image src="/Assets/dashboard/Glossy Purple Medical Shield Badge.png" alt="Shield" width={28} height={28} className="object-contain" />
              </div>
              <div className="leading-none">
                <p className="text-[8.5px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">
                  Mon code patient
                </p>
                <p className="text-[12px] font-extrabold text-slate-800 tracking-widest">
                  {showCode ? "7F3A-89K2" : "•••• 7F3A"}
                </p>
              </div>
              <div className="flex items-center gap-1 border-l border-slate-100 pl-2 ml-1">
                <div className="relative group flex items-center">
                  <button
                    onClick={() => setShowCode(!showCode)}
                    className="flex items-center gap-1 text-[11px] text-[#7C3AED] font-bold hover:bg-purple-50 px-2 py-0.5 rounded-full transition-colors"
                  >
                    <Eye size={11} /> {showCode ? "Masquer" : "Afficher"}
                  </button>
                  
                  {/* Speech-bubble tooltip on hover */}
                  <div className="absolute top-[calc(100%+8px)] left-1/2 -translate-x-1/2 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 bg-white rounded-xl shadow-lg border border-slate-100 px-3 py-1.5 flex items-center gap-2 whitespace-nowrap pointer-events-none z-50">
                    <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-2.5 h-2.5 bg-white border-t border-l border-slate-100 rotate-45" />
                    <div className="w-3.5 h-3.5 rounded-full bg-[#6366F1] text-white text-[8px] font-bold flex items-center justify-center flex-shrink-0">
                      i
                    </div>
                    <span className="text-[10px] text-slate-600 font-medium">
                      À donner à votre nouveau thérapeute en cas de changement
                    </span>
                  </div>
                </div>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1 text-[11px] text-slate-500 font-bold hover:bg-slate-50 px-2 py-0.5 rounded-full transition-colors"
                >
                  {copied ? (
                    <Check size={11} className="text-emerald-500" />
                  ) : (
                    <Copy size={11} />
                  )}{" "}
                  {copied ? "Copié !" : "Copier"}
                </button>
              </div>
            </div>
          </div>

          {/* User profile */}
          <div className="flex items-center gap-2 cursor-pointer group">
            <div
              className="w-10 h-10 rounded-full overflow-hidden border-2 border-white shadow-sm relative flex-shrink-0"
            >
              <Image
                src="/Assets/dashboard/Playful Character Face Sticker Sheet.png"
                alt="Salma Avatar"
                fill
                className="object-cover scale-[2.5] origin-top-left"
              />
            </div>
            <span className="font-bold text-[13px] text-slate-800">Salma</span>
            <ChevronDown size={13} className="text-slate-400" />
          </div>
        </div>

        {/* ── HERO ROW ─────────────────────────────────────────── */}
        <div className="flex gap-4 items-center -mt-10">

          {/* Level / Hero Banner */}
          <div
            className="relative flex items-center gap-4 px-6"
            style={{
              backgroundImage: "url('/Assets/dashboard/level%20card.png')",
              backgroundSize: "100% 100%",
              backgroundRepeat: "no-repeat",
              backgroundPosition: "center",
              aspectRatio: "1536 / 1024",
              flex: "0 0 56%",
            }}
          >
            {/* Spacer for the mascot baked into the image */}
            <div className="relative flex-shrink-0 z-10" style={{ width: 175, height: 170 }}></div>

            {/* Text */}
            <div className="flex flex-col gap-2 z-10 flex-1 min-w-0">
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-[#fce7f3] text-[#ec4899] text-[10px] font-extrabold border border-pink-100 w-fit">
                ★ Niveau actuel
              </span>
              <div>
                <h2 className="text-[26px] font-black text-slate-900 leading-tight">Niveau 3</h2>
                <p className="text-[13px] font-bold text-slate-700">Les super-héros du mouvement</p>
              </div>
              <div>
                <div className="flex justify-between text-[10.5px] font-bold text-slate-600 mb-1">
                  <span>⭐ Progression vers le niveau suivant</span>
                  <span className="text-slate-900 font-black">4 / 6</span>
                </div>
                <div className="h-3 bg-white/80 rounded-full shadow-inner border border-white overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: "67%",
                      background: "linear-gradient(to right, #38bdf8, #818cf8, #6366f1)",
                    }}
                  />
                </div>
              </div>
              <button className="mt-1 flex items-center gap-2 text-white text-[12px] font-bold px-5 py-2.5 rounded-full shadow hover:shadow-md hover:scale-[1.02] active:scale-[0.98] transition-all w-fit" style={{ background: "linear-gradient(to right, #7c3aed, #6366f1, #38bdf8)" }}>
                <Gamepad2 size={14} />
                Commencer un exercice →
              </button>
            </div>
          </div>

          {/* Last Session Card */}
          <div
            className="bg-white rounded-3xl shadow-sm border border-slate-100 flex flex-col p-5 relative overflow-hidden"
            style={{ flex: "1 1 0" }}
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <h3 className="flex items-center gap-2 text-[16px] font-black text-slate-900 leading-tight">
                <div className="w-7 h-7 rounded-xl bg-[#EDE9FE] flex items-center justify-center flex-shrink-0">
                  <Calendar size={14} className="text-[#6366F1]" />
                </div>
                Dernière séance
              </h3>
              <div className="flex flex-col items-end text-[11px] font-extrabold text-[#6366F1] -rotate-2 leading-tight text-right ml-1 flex-shrink-0">
                <span className="flex items-center gap-1">
                  <Image src="/Assets/dashboard/Cheerful Sparkle Star Sticker.png" width={14} height={14} alt="Sparkle" />
                  Super !
                </span>
                <span className="flex items-center gap-1">
                  Tu as bien joué !
                  <Image src="/Assets/dashboard/Vibrant Hand-Drawn Pink Heart.png" width={12} height={12} alt="Heart" />
                </span>
              </div>
            </div>

            {/* Date */}
            <div className="flex items-center gap-2 bg-slate-50 border border-slate-100 rounded-xl px-3 py-2 text-[11px] font-bold text-slate-600 mb-4">
              <Calendar size={12} className="text-slate-400 flex-shrink-0" />
              28 septembre 2026 &nbsp;•&nbsp; 16:24
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-3 flex-1">
              <div className="bg-[#FAF8FE] border border-purple-50 rounded-2xl p-3 flex flex-col gap-1">
                <div className="flex items-center gap-1 text-[10px] font-bold text-slate-500">
                  <Image src="/Assets/dashboard/Glossy Golden Star Sticker.png" width={15} height={15} alt="Star" /> Score
                </div>
                <div className="text-[30px] font-black text-slate-900 leading-none">420</div>
                <div className="text-[10px] text-slate-400 font-bold">/ 500</div>
              </div>
              <div className="bg-[#FAF8FE] border border-purple-50 rounded-2xl p-3 flex flex-col gap-1">
                <div className="flex items-center gap-1 text-[10px] font-bold text-slate-500">
                  <Image src="/Assets/dashboard/Glossy Neon Target Burst Icon.png" width={15} height={15} alt="Target" /> Taux de réussite
                </div>
                <div className="text-[30px] font-black text-slate-900 leading-none">92%</div>
              </div>
            </div>

            {/* Cheering mascot */}
            <div className="absolute bottom-2 right-2 w-14 h-14">
              <Image
                src="/Assets/dashboard/mascot-cheering.png"
                alt="Cheering mascot"
                fill
                className="object-contain"
              />
            </div>
          </div>
        </div>

        {/* ── EXERCISES SECTION ────────────────────────────────── */}
        <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-5">
          {/* Section header */}
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="flex items-center gap-2 text-[17px] font-black text-slate-900">
                <div className="w-7 h-7 rounded-lg bg-[#EDE9FE] flex items-center justify-center flex-shrink-0">
                  <Gamepad2 size={15} className="text-[#7C3AED]" />
                </div>
                Mes exercices
              </h2>
              <p className="text-[11.5px] text-slate-500 font-semibold mt-0.5">
                Voici les exercices qui t'ont été attribués par ton thérapeute.
              </p>
            </div>
            <Link
              href="#"
              className="text-[12px] font-bold text-[#7C3AED] hover:text-purple-800 flex items-center gap-0.5 group transition-colors"
            >
              Voir tous <span className="group-hover:translate-x-0.5 transition-transform">→</span>
            </Link>
          </div>

          {/* Cards row */}
          <div className="flex gap-3 overflow-x-auto pb-2 hide-scrollbar">
            {exercises.map((ex, i) => {
              const CardWrapper = ex.active && ex.href ? Link : "div";
              return (
                <CardWrapper
                  href={ex.href || "#"}
                  key={i}
                className={`flex-shrink-0 rounded-2xl border p-3 flex flex-col transition-all group snap-start ${
                  ex.active
                    ? "bg-white border-slate-100 shadow-sm hover:shadow-md hover:border-purple-200 cursor-pointer"
                    : "bg-[#F8FAFC] border-slate-100 opacity-80"
                }`}
                style={{ width: 160 }}
              >
                {/* Thumbnail */}
                <div
                  className="relative w-full rounded-xl overflow-hidden mb-3 bg-slate-100"
                  style={{ aspectRatio: "1/1" }}
                >
                  <Image
                    src={ex.image}
                    alt={ex.title}
                    fill
                    sizes="160px"
                    className={`object-cover transition-transform duration-300 ${
                      ex.active ? "group-hover:scale-105" : "grayscale opacity-60"
                    }`}
                  />
                  {ex.active ? (
                    <span className="absolute top-1.5 left-1.5 bg-[#10B981] text-white text-[8.5px] font-black px-2 py-0.5 rounded-full">
                      Actif
                    </span>
                  ) : (
                    <span className="absolute top-1.5 left-1.5 bg-[#64748B] text-white text-[8.5px] font-black px-1.5 py-0.5 rounded-full flex items-center gap-1 shadow-sm">
                      <Image src="/Assets/dashboard/Glossy Lavender Padlock Icon.png" width={10} height={10} alt="Lock" /> Verrouillé
                    </span>
                  )}
                </div>

                {/* Title */}
                <h4
                  className={`text-[13px] font-black mb-1.5 truncate ${
                    ex.active ? "text-slate-800" : "text-slate-500"
                  }`}
                >
                  {ex.title}
                </h4>

                {/* Meta */}
                <div className="space-y-1 mb-3 flex-1">
                  <div className="flex items-center gap-1.5 text-[10.5px] text-slate-500 font-bold truncate">
                    <Calendar size={11} className="text-slate-400 flex-shrink-0" />
                    <span className="truncate">{ex.category}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-[10.5px] text-slate-500 font-bold truncate">
                    <Image src="/Assets/dashboard/Glossy Neon Target Burst Icon.png" width={11} height={11} alt="Limb" />
                    <span className="truncate">{ex.limb}</span>
                  </div>
                </div>

                {/* Footer */}
                {ex.active ? (
                  <div className="flex items-center justify-between border-t border-slate-100 pt-2">
                    <div className="flex items-center gap-1 text-[11px] font-extrabold text-[#7C3AED]">
                      <BarChart2 size={13} /> Niveau {ex.level}
                    </div>
                    <button className="w-6 h-6 rounded-full bg-[#EDE9FE] text-[#7C3AED] group-hover:bg-[#7C3AED] group-hover:text-white transition-colors flex items-center justify-center text-[12px] font-bold flex-shrink-0">
                      →
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center justify-center gap-1 border-t border-slate-100 pt-2 text-[10px] font-bold text-slate-400">
                    <Image src="/Assets/dashboard/Glossy Lavender Padlock Icon.png" width={12} height={12} alt="Lock" className="opacity-70 grayscale" /> Débloqué au niveau {ex.lockedAt}
                  </div>
                )}
              </CardWrapper>
            )})}
          </div>
        </div>
      </div>

      <style dangerouslySetInnerHTML={{ __html: `
        .hide-scrollbar::-webkit-scrollbar { display: none; }
        .hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
      `}} />
    </div>
  );
}
