"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  LayoutDashboard,
  Users,
  CalendarDays,
  BarChart3,
  Settings,
  Bell,
  ChevronDown,
  Search,
  ChevronRight,
  AlertTriangle,
  Edit,
  TrendingUp,
  Shield,
  Clock,
  Activity,
  Target,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { PATIENTS, Patient, getPatientByCode } from "@/lib/data";

// ── Mini sparkline chart using SVG ─────────────────────────────────────────────
function Sparkline({
  data,
  color,
  target,
}: {
  data: number[];
  color: string;
  target?: number;
}) {
  const max = Math.max(...data, target ?? 0) + 10;
  const w = 220;
  const h = 80;
  const pts = data
    .map((v, i) => `${(i / (data.length - 1)) * w},${h - (v / max) * h}`)
    .join(" ");

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-20">
      {target && (
        <line
          x1="0"
          y1={h - (target / max) * h}
          x2={w}
          y2={h - (target / max) * h}
          stroke="#94A3B8"
          strokeDasharray="4,4"
          strokeWidth="1.5"
        />
      )}
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={pts}
      />
      {data.map((v, i) => (
        <circle
          key={i}
          cx={(i / (data.length - 1)) * w}
          cy={h - (v / max) * h}
          r="4"
          fill={color}
          stroke="white"
          strokeWidth="2"
        />
      ))}
    </svg>
  );
}

// ── Circular progress gauge ─────────────────────────────────────────────────────
function CircleGauge({ value, max, color }: { value: number; max: number; color: string }) {
  const r = 44;
  const circ = 2 * Math.PI * r;
  const pct = Math.min(value / max, 1);
  const offset = circ - pct * circ;
  return (
    <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
      <circle cx="50" cy="50" r={r} fill="none" stroke="#E2E8F0" strokeWidth="12" />
      <circle
        cx="50"
        cy="50"
        r={r}
        fill="none"
        stroke={color}
        strokeWidth="12"
        strokeDasharray={circ}
        strokeDashoffset={offset}
        strokeLinecap="round"
      />
    </svg>
  );
}

// ── Bar chart ──────────────────────────────────────────────────────────────────
function BarChart({ data, color, labels }: { data: number[]; color: string; labels: string[] }) {
  const max = Math.max(...data) + 1;
  return (
    <div className="flex items-end gap-2 h-20">
      {data.map((v, i) => (
        <div key={i} className="flex flex-col items-center gap-1 flex-1">
          <div
            className="w-full rounded-t-lg transition-all"
            style={{ height: `${(v / max) * 100}%`, backgroundColor: color, opacity: i === data.length - 1 ? 1 : 0.4 }}
          />
          <span className="text-[8px] text-slate-400 font-bold">{labels[i]}</span>
        </div>
      ))}
    </div>
  );
}

// ── Sidebar nav item ───────────────────────────────────────────────────────────
function NavItem({
  icon: Icon,
  label,
  active,
}: {
  icon: React.ElementType;
  label: string;
  active?: boolean;
}) {
  return (
    <div
      className={`flex items-center gap-3 px-4 py-2.5 rounded-2xl cursor-pointer transition-all text-sm font-bold ${
        active
          ? "bg-[#7C3AED] text-white shadow-md shadow-purple-200"
          : "text-slate-500 hover:bg-slate-100 hover:text-slate-700"
      }`}
    >
      <Icon size={18} />
      <span>{label}</span>
    </div>
  );
}

// ── Main therapist dashboard ───────────────────────────────────────────────────
export default function TherapistDashboard() {
  const [searchCode, setSearchCode] = useState("7F3A-89K2");
  const [activePatient, setActivePatient] = useState<Patient>(
    getPatientByCode("7F3A-89K2")!
  );

  const latest = activePatient.sessions[0];
  const rotLeft = activePatient.sessions.map((s) => s.rotationLeft).reverse();
  const rotRight = activePatient.sessions.map((s) => s.rotationRight).reverse();
  const painData = activePatient.sessions.map((s) => s.painLevel).reverse();
  const effortData = activePatient.sessions.map((s) => s.effort).reverse();
  const sessionLabels = activePatient.sessions.map((s) => s.date.split(" ")[0]).reverse();
  const symmetry = Math.round(
    (Math.min(latest.rotationLeft, latest.rotationRight) /
      Math.max(latest.rotationLeft, latest.rotationRight)) *
      100
  );

  const handleSearch = () => {
    const found = getPatientByCode(searchCode.trim());
    if (found) setActivePatient(found);
  };

  return (
    <div className="min-h-screen bg-[#EEF2FA] font-outfit flex">
      {/* ── SIDEBAR ── */}
      <aside className="w-[200px] flex-shrink-0 bg-white border-r border-slate-100 flex flex-col py-6 px-3 gap-2">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 px-3 mb-6">
          <div className="w-8 h-8 relative flex-shrink-0">
            <Image
              src="/assets_flat/sensai-mascot.png"
              alt="SensAI"
              width={32}
              height={32}
              className="w-full h-full object-contain"
            />
          </div>
          <span className="font-outfit text-lg font-black tracking-tight text-slate-900">
            Sens<span className="text-[#FF6B8B]">A</span>
            <span className="text-[#7C3AED]">I</span>
          </span>
        </Link>

        <NavItem icon={LayoutDashboard} label="Tableau de bord" active />
        <NavItem icon={Users} label="Patients" />
        <NavItem icon={CalendarDays} label="Séances" />
        <NavItem icon={BarChart3} label="Rapports" />

        <div className="flex-1" />
        <NavItem icon={Settings} label="Paramètres" />
      </aside>

      {/* ── MAIN ── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="h-16 flex-shrink-0 bg-white border-b border-slate-100 flex items-center justify-between px-6 gap-4">
          {/* Search */}
          <div className="flex items-center gap-2 flex-1 max-w-md">
            <div className="relative flex-1">
              <Search
                size={14}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              />
              <input
                value={searchCode}
                onChange={(e) => setSearchCode(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="Rechercher un patient par code..."
                className="w-full pl-9 pr-4 py-2 text-sm rounded-full bg-slate-50 border border-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-200 font-medium"
              />
            </div>
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-[#7C3AED] text-white text-sm font-bold rounded-full hover:bg-[#6D28D9] transition-colors"
            >
              {searchCode || "7F3A-89K2"}
            </button>
          </div>

          {/* Right side */}
          <div className="flex items-center gap-4">
            <button className="relative w-9 h-9 bg-slate-50 rounded-full flex items-center justify-center border border-slate-200 hover:bg-slate-100 transition-colors">
              <Bell size={16} className="text-slate-500" />
              <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-[#FF6B8B] rounded-full border-2 border-white" />
            </button>
            <div className="flex items-center gap-3 cursor-pointer group">
              <div className="w-9 h-9 rounded-full bg-indigo-100 overflow-hidden border-2 border-indigo-200">
                <Image
                  src="/Assets/dashboard/Playful Character Face Sticker Sheet.png"
                  width={36}
                  height={36}
                  alt="Dr. Martin"
                  className="w-full h-full object-cover object-top scale-150"
                />
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-black text-slate-800 leading-none">Dr. Martin</span>
                <span className="text-[10px] font-bold text-slate-400 leading-none mt-0.5">Kinésithérapeute</span>
              </div>
              <ChevronDown size={14} className="text-slate-400" />
            </div>
          </div>
        </header>

        {/* Content area */}
        <main className="flex-1 overflow-auto p-6 flex flex-col gap-5">
          
          {/* ── PATIENT HERO CARD ── */}
          <div className="bg-white rounded-3xl p-5 flex items-center gap-6 shadow-sm border border-slate-100">
            <div className="w-20 h-20 rounded-2xl overflow-hidden bg-indigo-50 border border-indigo-100 flex-shrink-0">
              <Image
                src={activePatient.avatar}
                width={80}
                height={80}
                alt={activePatient.name}
                className="w-full h-full object-cover object-top scale-[2] translate-y-2"
              />
            </div>
            <div className="flex-1">
              <div className="flex items-baseline gap-2 mb-1">
                <h1 className="text-2xl font-black text-slate-800">{activePatient.name}</h1>
                <span className="text-slate-400 font-bold">♀ {activePatient.age} ans</span>
              </div>
              <div className="flex items-center gap-2 mb-3">
                <Shield size={13} className="text-slate-400" />
                <span className="text-sm font-medium text-slate-500">{activePatient.diagnosis}</span>
              </div>
              <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-100 rounded-full px-3 py-1 w-fit">
                <CheckCircle2 size={13} className="text-emerald-500" />
                <span className="text-xs font-black text-emerald-700">{activePatient.adherence}% d'adhérence</span>
              </div>
            </div>

            {/* Pain badge */}
            <div className="bg-amber-50 border-2 border-amber-200 rounded-2xl p-4 flex flex-col items-center gap-1 flex-shrink-0">
              <div className="flex items-center gap-1.5 text-amber-600 text-xs font-bold">
                <AlertTriangle size={12} />
                Douleur niveau {latest.painLevel}/5
              </div>
              <span className="text-[11px] font-bold text-amber-500">le {latest.date}</span>
            </div>

            {/* Last session badge */}
            <div className="bg-slate-50 border border-slate-100 rounded-2xl p-4 flex items-center gap-4 flex-shrink-0 hover:bg-slate-100 cursor-pointer transition-colors">
              <div className="flex flex-col">
                <span className="text-[10px] font-bold text-slate-400 mb-1">Dernière séance</span>
                <span className="text-sm font-black text-slate-700">{latest.date}</span>
                <span className="text-[11px] font-bold text-slate-400">{latest.duration}</span>
              </div>
              <ChevronRight size={16} className="text-slate-300" />
            </div>
          </div>

          {/* ── MIDDLE ROW ── */}
          <div className="grid grid-cols-[1fr_320px] gap-5">
            
            {/* LEFT: amplitude & symmetry */}
            <div className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <Target size={18} className="text-[#7C3AED]" />
                  <h2 className="font-black text-slate-800">Amplitude de mouvement &amp; Symétrie</h2>
                </div>
                <span className="text-xs font-bold text-slate-400 bg-slate-50 px-3 py-1 rounded-full border border-slate-100">
                  Objectif : {activePatient.targetAngle}°
                </span>
              </div>
              <p className="text-xs font-bold text-slate-400 mb-5">Exercice : Le Hibou — Rotation cervicale</p>

              <div className="grid grid-cols-3 gap-4">
                {/* Left rotation */}
                <div className="bg-slate-50 rounded-2xl p-4 flex flex-col gap-2 border border-slate-100">
                  <span className="text-xs font-black text-slate-500 flex items-center gap-1">← Rotation gauche</span>
                  <span className="text-3xl font-black text-slate-800">{latest.rotationLeft}°</span>
                  <span className="text-[11px] font-bold text-slate-400">/ {activePatient.targetAngle}° cible</span>
                  <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#7C3AED] rounded-full"
                      style={{ width: `${Math.min((latest.rotationLeft / activePatient.targetAngle) * 100, 100)}%` }}
                    />
                  </div>
                  <span className="text-[10px] text-slate-400 font-bold">Objectif {activePatient.targetAngle}°</span>
                </div>

                {/* Symmetry */}
                <div className="bg-slate-50 rounded-2xl p-4 flex flex-col items-center gap-2 border border-slate-100">
                  <span className="text-xs font-black text-slate-500">Indice de symétrie</span>
                  <div className="relative w-24 h-24">
                    <CircleGauge value={symmetry} max={100} color={symmetry >= 80 ? "#10B981" : "#F59E0B"} />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-xl font-black text-slate-800 rotate-90">{symmetry}%</span>
                    </div>
                  </div>
                  <div className={`text-[11px] font-bold flex items-center gap-1 ${symmetry >= 80 ? "text-emerald-600" : "text-amber-500"}`}>
                    {symmetry >= 80 ? <CheckCircle2 size={11} /> : <AlertTriangle size={11} />}
                    {symmetry >= 80 ? "Symétrique" : "Asymétrie légère"}
                  </div>
                </div>

                {/* Right rotation */}
                <div className="bg-slate-50 rounded-2xl p-4 flex flex-col gap-2 border border-slate-100">
                  <span className="text-xs font-black text-slate-500 flex items-center gap-1">Rotation droite →</span>
                  <span className="text-3xl font-black text-slate-800">{latest.rotationRight}°</span>
                  <span className="text-[11px] font-bold text-slate-400">/ {activePatient.targetAngle}° cible</span>
                  <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#06B6D4] rounded-full"
                      style={{ width: `${Math.min((latest.rotationRight / activePatient.targetAngle) * 100, 100)}%` }}
                    />
                  </div>
                  <span className="text-[10px] text-slate-400 font-bold">Objectif {activePatient.targetAngle}°</span>
                </div>
              </div>

              {/* Extra metrics */}
              <div className="grid grid-cols-2 gap-3 mt-3">
                <div className="bg-indigo-50/50 border border-indigo-100 rounded-2xl p-3 flex items-center gap-3">
                  <Clock size={18} className="text-indigo-400 flex-shrink-0" />
                  <div>
                    <p className="text-xs font-bold text-slate-400">Durée de maintien moyenne</p>
                    <p className="text-lg font-black text-slate-800">3,2 s</p>
                    <p className="text-[10px] font-bold text-slate-400">(à l'angle maximal)</p>
                  </div>
                </div>
                <div className="bg-cyan-50/50 border border-cyan-100 rounded-2xl p-3 flex items-center gap-3">
                  <Activity size={18} className="text-cyan-400 flex-shrink-0" />
                  <div>
                    <p className="text-xs font-bold text-slate-400">Fluidité du mouvement</p>
                    <p className="text-lg font-black text-slate-800">89 / 100</p>
                    <p className="text-[10px] font-bold text-slate-400">(faible tremblement)</p>
                  </div>
                </div>
              </div>
            </div>

            {/* RIGHT: prescription */}
            <div className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100 flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🎮</span>
                  <h2 className="font-black text-slate-800 text-sm">Prescription &amp; Configuration</h2>
                </div>
                <button className="flex items-center gap-1 text-[11px] font-bold text-[#7C3AED] hover:underline">
                  <Edit size={11} /> Modifier
                </button>
              </div>

              {/* Active games */}
              <div className="flex flex-col gap-2">
                {activePatient.activeGames.map((g, i) => (
                  <div key={i} className="flex items-center gap-3 p-2 bg-slate-50 rounded-2xl border border-slate-100">
                    <div className="w-10 h-10 rounded-xl overflow-hidden bg-white border border-slate-100 flex-shrink-0">
                      <Image src={g.image} width={40} height={40} alt={g.title} className="w-full h-full object-cover" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-black text-slate-700 truncate">{g.title}</p>
                      <p className="text-[10px] font-bold text-slate-400 truncate">{g.category}</p>
                    </div>
                    <span className="text-[10px] font-black text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">
                      {g.status}
                    </span>
                  </div>
                ))}
              </div>

              <div>
                <p className="text-[10px] font-black text-slate-500 uppercase tracking-wider mb-2">Paramètres actuels</p>
                <div className="grid grid-cols-2 gap-2 text-center">
                  {[
                    { icon: "📐", label: "Angle cible", value: `${activePatient.targetAngle}°` },
                    { icon: "⏱️", label: "Maintien", value: `${activePatient.targetHold} s` },
                    { icon: "🪶", label: "Vitesse", value: activePatient.speedLimit },
                    { icon: "⭐", label: "Difficulté", value: activePatient.difficulty },
                  ].map((item, i) => (
                    <div key={i} className="bg-indigo-50/40 rounded-xl p-2 border border-indigo-50">
                      <span className="text-sm">{item.icon}</span>
                      <p className="text-[9px] font-bold text-slate-400 mt-0.5">{item.label}</p>
                      <p className="text-xs font-black text-slate-700">{item.value}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* ── BOTTOM ROW ── */}
          <div className="grid grid-cols-[1fr_380px] gap-5">
            
            {/* Pain & effort */}
            <div className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-lg">💜</span>
                <h2 className="font-black text-slate-800">Douleur &amp; Effort</h2>
                <span className="text-xs font-bold text-slate-400">(auto-évaluation)</span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-[11px] font-bold text-[#7C3AED] flex items-center gap-1 mb-2">
                    <BarChart3 size={11} /> Douleur après séance
                  </p>
                  <BarChart data={painData} color="#F472B6" labels={sessionLabels} />
                </div>
                <div>
                  <p className="text-[11px] font-bold text-cyan-600 flex items-center gap-1 mb-2">
                    <TrendingUp size={11} /> Effort perçu (RPE)
                  </p>
                  <BarChart data={effortData} color="#06B6D4" labels={sessionLabels} />
                </div>
              </div>

              {/* Correlation alert */}
              {latest.painLevel >= 4 && (
                <div className="mt-3 bg-amber-50 border border-amber-200 rounded-2xl p-3 flex gap-2">
                  <AlertTriangle size={14} className="text-amber-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-[11px] font-black text-amber-800">Corrélation détectée</p>
                    <p className="text-[10px] font-bold text-amber-600 mt-0.5">
                      La hausse de la douleur ({latest.painLevel}/5) aujourd'hui est liée à une augmentation de l'amplitude ({latest.rotationRight}°) lors de la séance.
                    </p>
                    <button className="mt-1.5 text-[10px] font-black text-[#7C3AED] flex items-center gap-1 hover:underline">
                      <Edit size={10} /> Vérifier la prescription
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Progress chart + session history */}
            <div className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100 flex flex-col gap-4">
              {/* Progress chart */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <TrendingUp size={15} className="text-[#7C3AED]" />
                    <h2 className="font-black text-slate-800 text-sm">Évolution des progrès</h2>
                  </div>
                  <div className="flex items-center gap-3 text-[9px] font-bold text-slate-400">
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#7C3AED] inline-block" /> Rotation gauche</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#06B6D4] inline-block" /> Rotation droite</span>
                    <span className="flex items-center gap-1"><span className="w-4 h-0.5 bg-slate-300 inline-block border-dashed" /> Objectif ({activePatient.targetAngle}°)</span>
                  </div>
                </div>
                <div className="relative">
                  <Sparkline data={rotLeft} color="#7C3AED" target={activePatient.targetAngle} />
                  <div className="absolute inset-0">
                    <Sparkline data={rotRight} color="#06B6D4" target={activePatient.targetAngle} />
                  </div>
                </div>
              </div>

              {/* Sessions table */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-[11px] font-black text-slate-600 flex items-center gap-1">
                    <CalendarDays size={11} /> Historique des séances
                  </p>
                  <button className="text-[10px] font-bold text-[#7C3AED] hover:underline flex items-center gap-0.5">
                    Voir tout <ChevronRight size={10} />
                  </button>
                </div>
                <table className="w-full text-[10px]">
                  <thead>
                    <tr className="text-slate-400 font-bold border-b border-slate-100">
                      <th className="pb-1.5 text-left">Date</th>
                      <th className="pb-1.5 text-left">Durée</th>
                      <th className="pb-1.5 text-left">Jeux</th>
                      <th className="pb-1.5 text-left">Score</th>
                      <th className="pb-1.5 text-left">Statut</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activePatient.sessions.map((s, i) => (
                      <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/50">
                        <td className="py-1.5 font-bold text-slate-700">{s.date}</td>
                        <td className="py-1.5 font-bold text-slate-500">{s.duration}</td>
                        <td className="py-1.5 font-bold text-slate-500">{s.gamesCompleted}</td>
                        <td className="py-1.5 font-black text-slate-800">{s.score}</td>
                        <td className="py-1.5">
                          <span className={`font-black px-1.5 py-0.5 rounded-full ${s.status === "Complet" ? "bg-emerald-50 text-emerald-600" : "bg-amber-50 text-amber-600"}`}>
                            {s.status === "Complet" ? <span className="flex items-center gap-0.5"><CheckCircle2 size={9} /> Complet</span> : <span className="flex items-center gap-0.5"><XCircle size={9} /> Partiel</span>}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
