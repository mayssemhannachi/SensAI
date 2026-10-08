"use client";

import { useCallback, useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  LayoutDashboard,
  Users,
  CalendarDays,
  BarChart3,
  Settings,
  Search,
  AlertTriangle,
  Edit,
  TrendingUp,
  Shield,
  Clock,
  Activity,
  Target,
  CheckCircle2,
  XCircle,
  LogOut,
  Plus,
  KeyRound,
  ExternalLink,
} from "lucide-react";
import {
  ANALYTICS_URL,
  assignGame,
  createActivationCode,
  createConsultation,
  createPatient,
  listConsultations,
  listGames,
  listPatientGames,
  listPatients,
  listSessions,
  updateGameConfig,
  type Game,
  type GameConfig,
  type GameSession,
  type Patient,
  type PatientGame,
} from "@/lib/api";
import {
  adherence,
  DIFFICULTY_LABELS,
  formatDate,
  formatDuration,
  gameMeta,
  sessionDate,
  sortByDateDesc,
  SPEED_LABELS,
  withDefaults,
} from "@/lib/games";
import { useRequireAuth } from "@/lib/useAuth";

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
  const x = (i: number) => (data.length > 1 ? (i / (data.length - 1)) * w : w / 2);
  const pts = data.map((v, i) => `${x(i)},${h - (v / max) * h}`).join(" ");

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
          cx={x(i)}
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
function BarChart({ data, color, labels, max = 5 }: { data: number[]; color: string; labels: string[]; max?: number }) {
  const top = Math.max(max, ...data, 1);
  return (
    <div className="flex items-end gap-2 h-24">
      {data.map((v, i) => (
        <div key={i} className="flex flex-col items-center justify-end gap-1 flex-1 h-full">
          <span className="text-[9px] font-black text-slate-500">{v}</span>
          <div
            className="w-full rounded-t-lg transition-all"
            style={{ height: `${Math.max(4, (v / top) * 64)}px`, backgroundColor: color, opacity: i === data.length - 1 ? 1 : 0.45 }}
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
  onClick,
}: {
  icon: React.ElementType;
  label: string;
  active?: boolean;
  onClick?: () => void;
}) {
  return (
    <div
      onClick={onClick}
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

// ── Petites briques UI ────────────────────────────────────────────────────────
function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 bg-slate-900/30 backdrop-blur-[2px] flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-3xl shadow-xl border border-slate-100 w-full max-w-lg p-6" onClick={(e) => e.stopPropagation()} role="dialog" aria-label={title}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-black text-slate-800 text-lg">{title}</h3>
          <button onClick={onClose} className="w-8 h-8 rounded-full hover:bg-slate-100 text-slate-400" aria-label="Fermer">✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

const fieldClass =
  "w-full px-3 py-2 rounded-xl border border-slate-200 bg-slate-50 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-purple-200 focus:bg-white";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-[11px] font-black text-slate-500 mb-1">{label}</span>
      {children}
    </label>
  );
}

function ConfigForm({
  initial,
  submitLabel,
  onSubmit,
}: {
  initial: GameConfig;
  submitLabel: string;
  onSubmit: (config: GameConfig) => Promise<void>;
}) {
  const start = withDefaults(initial);
  const [config, setConfig] = useState(start);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const set = (key: keyof typeof start, value: unknown) => setConfig((c) => ({ ...c, [key]: value }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (config.safety_limit < config.target_angle) {
      setError("La limite de sécurité doit être supérieure ou égale à l’angle cible.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSubmit(config);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Enregistrement impossible.");
      setSaving(false);
    }
  };

  return (
    <form onSubmit={submit} className="flex flex-col gap-3">
      <div className="grid grid-cols-3 gap-3">
        <Field label="📐 Angle cible (°)">
          <input type="number" min={5} max={90} value={config.target_angle} onChange={(e) => set("target_angle", Number(e.target.value))} className={fieldClass} />
        </Field>
        <Field label="⏱️ Maintien (s)">
          <input type="number" min={1} max={15} value={config.hold_seconds} onChange={(e) => set("hold_seconds", Number(e.target.value))} className={fieldClass} />
        </Field>
        <Field label="🔁 Répétitions">
          <input type="number" min={1} max={30} value={config.repetitions} onChange={(e) => set("repetitions", Number(e.target.value))} className={fieldClass} />
        </Field>
        <Field label="🪶 Vitesse">
          <select value={config.speed} onChange={(e) => set("speed", e.target.value)} className={fieldClass}>
            {Object.entries(SPEED_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </Field>
        <Field label="⭐ Difficulté">
          <select value={config.difficulty} onChange={(e) => set("difficulty", e.target.value)} className={fieldClass}>
            {Object.entries(DIFFICULTY_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </Field>
        <Field label="🛡️ Limite (°)">
          <input type="number" min={5} max={120} value={config.safety_limit} onChange={(e) => set("safety_limit", Number(e.target.value))} className={fieldClass} />
        </Field>
      </div>
      <label className="flex items-center gap-2 text-sm font-bold text-slate-600">
        <input type="checkbox" checked={config.active} onChange={(e) => set("active", e.target.checked)} className="w-4 h-4 accent-[#7C3AED]" />
        Visible dans l’espace du patient
      </label>
      {error && <p className="text-xs font-bold text-rose-600">{error}</p>}
      <button type="submit" disabled={saving} className="mt-1 py-2.5 rounded-full bg-[#7C3AED] hover:bg-[#6D28D9] disabled:opacity-60 text-white text-sm font-black">
        {saving ? "Enregistrement…" : submitLabel}
      </button>
    </form>
  );
}

function initials(first: string, last: string) {
  return `${first?.[0] ?? ""}${last?.[0] ?? ""}`.toUpperCase() || "?";
}

type SessionRow = GameSession & { game_name: string; game_slug: string };

// ── Main therapist dashboard ───────────────────────────────────────────────────
export default function TherapistDashboard() {
  const { me, error: authError, signOut } = useRequireAuth("therapist");
  const [patients, setPatients] = useState<Patient[]>([]);
  const [catalog, setCatalog] = useState<Game[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [patientGames, setPatientGames] = useState<PatientGame[]>([]);
  const [sessions, setSessions] = useState<SessionRow[]>([]);
  const [diagnosis, setDiagnosis] = useState<string>("");
  const [loadedId, setLoadedId] = useState<number | null>(null);
  const [pageError, setPageError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [activationCode, setActivationCode] = useState<string | null>(null);
  const [modal, setModal] = useState<
    | { kind: "new-patient" }
    | { kind: "add-game" }
    | { kind: "edit-game"; pg: PatientGame }
    | { kind: "diagnosis" }
    | null
  >(null);

  const notify = (message: string) => {
    setToast(message);
    setTimeout(() => setToast(null), 2500);
  };

  // Liste des patients + catalogue de jeux
  const applyPatients = useCallback((list: Patient[], games: Game[], selectId?: number) => {
    const sorted = [...list].sort((a, b) => a.last_name.localeCompare(b.last_name, "fr"));
    setPatients(sorted);
    setCatalog(games);
    setSelectedId((current) => selectId ?? current ?? sorted[0]?.id ?? null);
  }, []);

  const loadPatients = useCallback(async (selectId?: number) => {
    const [list, games] = await Promise.all([listPatients(), listGames()]);
    applyPatients(list, games, selectId);
  }, [applyPatients]);

  useEffect(() => {
    if (!me) return;
    Promise.all([listPatients(), listGames()])
      .then(([list, games]) => applyPatients(list, games))
      .catch((err) => setPageError(err instanceof Error ? err.message : "Erreur de chargement"));
  }, [me, applyPatients]);

  // Données du patient sélectionné
  const loadPatient = useCallback(async (patientId: number, games: Game[]) => {
    try {
      const assigned = await listPatientGames(patientId);
      const byId = new Map(games.map((g) => [g.id, g]));
      const enriched = assigned.map((pg) => ({
        ...pg,
        game_name: byId.get(pg.game_id)?.name ?? `Jeu ${pg.game_id}`,
        game_slug: byId.get(pg.game_id)?.slug ?? "",
      }));
      const perGame = await Promise.all(enriched.map((pg) => listSessions(pg.id)));
      const rows: SessionRow[] = perGame.flatMap((list, i) =>
        list.map((s) => ({ ...s, game_name: enriched[i].game_name!, game_slug: enriched[i].game_slug! })),
      );
      let latestDiagnosis = "";
      try {
        const consultations = await listConsultations(patientId);
        latestDiagnosis = consultations.find((c) => c.diagnosis)?.diagnosis ?? "";
      } catch {
        latestDiagnosis = "";
      }
      setPatientGames(enriched);
      setSessions(sortByDateDesc(rows) as SessionRow[]);
      setDiagnosis(latestDiagnosis);
      setLoadedId(patientId);
    } catch (err) {
      setPageError(err instanceof Error ? err.message : "Erreur de chargement");
    }
  }, []);

  useEffect(() => {
    // loadPatient ne met à jour l'état qu'après les appels réseau (asynchrone).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (selectedId != null) loadPatient(selectedId, catalog);
  }, [selectedId, catalog, loadPatient]);

  const selectPatient = (id: number) => {
    setActivationCode(null);
    setSelectedId(id);
  };
  const loadingPatient = selectedId !== null && selectedId !== loadedId;

  const patient = patients.find((p) => p.id === selectedId) ?? null;
  const filtered = patients.filter((p) => {
    const q = search.trim().toLowerCase();
    return !q || `${p.first_name} ${p.last_name} ${p.patient_code}`.toLowerCase().includes(q);
  });

  // Indicateurs du jeu « Le Hibou » (rotation cervicale)
  const hibou = patientGames.find((g) => g.game_slug === "le-hibou");
  const hibouConfig = withDefaults(hibou?.configuration);
  const hibouSessions = sessions.filter((s) => s.game_slug === "le-hibou");
  const latestHibou = hibouSessions[0];
  const rotLeft = hibouSessions.map((s) => Number(s.metrics.rotation_left ?? 0)).reverse().slice(-8);
  const rotRight = hibouSessions.map((s) => Number(s.metrics.rotation_right ?? 0)).reverse().slice(-8);
  const leftNow = Number(latestHibou?.metrics.rotation_left ?? 0);
  const rightNow = Number(latestHibou?.metrics.rotation_right ?? 0);
  const symmetry = leftNow && rightNow ? Math.round((Math.min(leftNow, rightNow) / Math.max(leftNow, rightNow)) * 100) : 0;
  const rated = sessions.filter((s) => s.metrics.pain_level != null).slice(0, 6).reverse();
  const painData = rated.map((s) => Number(s.metrics.pain_level));
  const effortData = rated.map((s) => Number(s.metrics.effort ?? 0));
  const ratedLabels = rated.map((s) => sessionDate(s).toLocaleDateString("fr-FR", { day: "numeric", month: "numeric" }));
  const latest = sessions[0];
  const latestPain = latest?.metrics.pain_level != null ? Number(latest.metrics.pain_level) : null;

  const handleActivationCode = async () => {
    if (!patient) return;
    try {
      const result = await createActivationCode(patient.id);
      setActivationCode(result.code);
    } catch (err) {
      notify(err instanceof Error ? err.message : "Erreur");
    }
  };

  const toggleGame = async (pg: PatientGame) => {
    const config = withDefaults(pg.configuration);
    await updateGameConfig(pg.id, { ...config, active: !config.active });
    if (patient) await loadPatient(patient.id, catalog);
    notify(config.active ? "Jeu masqué pour le patient" : "Jeu activé pour le patient");
  };

  if (authError || pageError) {
    return (
      <div className="min-h-screen bg-[#EEF2FA] font-outfit flex items-center justify-center p-6">
        <div className="bg-white rounded-3xl p-8 text-center max-w-md shadow-sm border border-slate-100">
          <div className="text-4xl mb-2">⚠️</div>
          <h2 className="font-black text-slate-800">Impossible de charger les données</h2>
          <p className="text-sm text-slate-500 mt-1">{authError || pageError}</p>
          <button onClick={() => window.location.reload()} className="mt-4 px-5 py-2 rounded-full bg-[#7C3AED] text-white text-sm font-bold">Réessayer</button>
        </div>
      </div>
    );
  }

  if (!me) {
    return (
      <div className="min-h-screen bg-[#EEF2FA] font-outfit flex items-center justify-center">
        <p className="font-black text-[#312E81] animate-pulse">Chargement de votre espace…</p>
      </div>
    );
  }

  const assignedIds = new Set(patientGames.map((g) => g.game_id));
  const availableGames = catalog.filter((g) => !assignedIds.has(g.id));

  return (
    <div className="min-h-screen bg-[#EEF2FA] font-outfit flex">
      {/* ── SIDEBAR ── */}
      <aside className="w-[200px] flex-shrink-0 bg-white border-r border-slate-100 flex flex-col py-6 px-3 gap-2">
        <Link href="/" className="flex items-center gap-2.5 px-3 mb-6">
          <div className="w-8 h-8 relative flex-shrink-0">
            <Image src="/assets_flat/sensai-mascot.png" alt="SensAI" width={32} height={32} className="w-full h-full object-contain" />
          </div>
          <span className="font-outfit text-lg font-black tracking-tight text-slate-900">
            Sens<span className="text-[#FF6B8B]">A</span>
            <span className="text-[#7C3AED]">I</span>
          </span>
        </Link>

        <NavItem icon={LayoutDashboard} label="Tableau de bord" active />
        <NavItem icon={Users} label="Nouveau patient" onClick={() => setModal({ kind: "new-patient" })} />
        <a href={ANALYTICS_URL} target="_blank" rel="noreferrer">
          <NavItem icon={BarChart3} label="Analyses" />
        </a>

        <div className="flex-1" />
        <NavItem icon={LogOut} label="Déconnexion" onClick={signOut} />
      </aside>

      {/* ── MAIN ── */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 flex-shrink-0 bg-white border-b border-slate-100 flex items-center justify-between px-6 gap-4">
          <div className="relative flex-1 max-w-md">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Rechercher un patient par nom ou code…"
              className="w-full pl-9 pr-4 py-2 text-sm rounded-full bg-slate-50 border border-slate-200 focus:outline-none focus:ring-2 focus:ring-purple-200 font-medium"
            />
          </div>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-indigo-100 border-2 border-indigo-200 flex items-center justify-center text-indigo-700 font-black text-xs">
              {(me.full_name || me.sub).slice(0, 2).toUpperCase()}
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-black text-slate-800 leading-none">{me.full_name || me.sub}</span>
              <span className="text-[10px] font-bold text-slate-400 leading-none mt-0.5">Kinésithérapeute</span>
            </div>
          </div>
        </header>

        <div className="flex-1 flex min-h-0">
          {/* ── LISTE DES PATIENTS ── */}
          <section className="w-[250px] flex-shrink-0 border-r border-slate-100 bg-white/60 p-4 flex flex-col gap-2 overflow-auto">
            <button
              onClick={() => setModal({ kind: "new-patient" })}
              className="w-full py-2 rounded-full bg-[#7C3AED] hover:bg-[#6D28D9] text-white text-sm font-black flex items-center justify-center gap-1.5"
            >
              <Plus size={15} /> Nouveau patient
            </button>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-wider mt-2">
              Mes patients ({filtered.length})
            </p>
            {filtered.length === 0 && (
              <p className="text-xs font-bold text-slate-400 py-4 text-center">
                {patients.length ? "Aucun résultat." : "Aucun patient : créez le premier."}
              </p>
            )}
            {filtered.map((p) => (
              <button
                key={p.id}
                onClick={() => selectPatient(p.id)}
                className={`flex items-center gap-3 p-2 rounded-2xl text-left transition-all ${
                  p.id === selectedId ? "bg-white shadow-sm border border-purple-200" : "hover:bg-white/80 border border-transparent"
                }`}
              >
                <div className="w-9 h-9 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-black text-xs flex-shrink-0">
                  {initials(p.first_name, p.last_name)}
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-black text-slate-700 truncate">{p.first_name} {p.last_name}</p>
                  <p className="text-[10px] font-bold text-slate-400 truncate">{p.patient_code.toUpperCase()} · {p.age} ans</p>
                </div>
              </button>
            ))}
          </section>

          {/* ── FICHE ── */}
          <main className="flex-1 overflow-auto p-6 flex flex-col gap-5">
            {!patient ? (
              <div className="bg-white rounded-3xl p-10 text-center shadow-sm border border-slate-100">
                <div className="text-4xl">👋</div>
                <h2 className="font-black text-slate-800 mt-2">Bienvenue {me.full_name || ""}</h2>
                <p className="text-sm text-slate-500 mt-1">Créez votre premier patient pour lui attribuer des jeux.</p>
                <button onClick={() => setModal({ kind: "new-patient" })} className="mt-4 px-5 py-2 rounded-full bg-[#7C3AED] text-white text-sm font-black">
                  + Nouveau patient
                </button>
              </div>
            ) : (
              <>
                {/* ── PATIENT HERO CARD ── */}
                <div className="bg-white rounded-3xl p-5 flex items-center gap-6 shadow-sm border border-slate-100 flex-wrap">
                  <div className="w-20 h-20 rounded-2xl bg-indigo-50 border border-indigo-100 flex-shrink-0 flex items-center justify-center text-2xl font-black text-indigo-600">
                    {initials(patient.first_name, patient.last_name)}
                  </div>
                  <div className="flex-1 min-w-[220px]">
                    <div className="flex items-baseline gap-2 mb-1">
                      <h1 className="text-2xl font-black text-slate-800">{patient.first_name} {patient.last_name}</h1>
                      <span className="text-slate-400 font-bold">{patient.age} ans</span>
                    </div>
                    <div className="flex items-center gap-2 mb-3">
                      <Shield size={13} className="text-slate-400" />
                      <span className="text-sm font-medium text-slate-500">{diagnosis || "Diagnostic non renseigné"}</span>
                      <button onClick={() => setModal({ kind: "diagnosis" })} className="text-[11px] font-bold text-[#7C3AED] hover:underline flex items-center gap-1">
                        <Edit size={11} /> {diagnosis ? "Modifier" : "Ajouter"}
                      </button>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-100 rounded-full px-3 py-1 w-fit">
                        <CheckCircle2 size={13} className="text-emerald-500" />
                        <span className="text-xs font-black text-emerald-700">{adherence(sessions)}% d&apos;adhérence (7 j)</span>
                      </div>
                      <span className="text-xs font-bold text-slate-400 bg-slate-50 border border-slate-100 rounded-full px-3 py-1">
                        Code patient {patient.patient_code.toUpperCase()}
                      </span>
                    </div>
                  </div>

                  {latestPain != null && (
                    <div className={`${latestPain >= 4 ? "bg-amber-50 border-amber-200" : "bg-slate-50 border-slate-100"} border-2 rounded-2xl p-4 flex flex-col items-center gap-1 flex-shrink-0`}>
                      <div className="flex items-center gap-1.5 text-amber-600 text-xs font-bold">
                        <AlertTriangle size={12} /> Douleur niveau {latestPain}/5
                      </div>
                      <span className="text-[11px] font-bold text-amber-500">le {formatDate(sessionDate(latest!))}</span>
                    </div>
                  )}

                  <div className="flex flex-col gap-2 flex-shrink-0">
                    <div className="bg-slate-50 border border-slate-100 rounded-2xl px-4 py-2.5">
                      <span className="text-[10px] font-bold text-slate-400 block">Dernière séance</span>
                      <span className="text-sm font-black text-slate-700">{latest ? formatDate(sessionDate(latest)) : "Aucune"}</span>
                      {latest && <span className="text-[11px] font-bold text-slate-400 block">{formatDuration(latest.duration_sec)}</span>}
                    </div>
                  </div>
                </div>

                {/* ── ACCÈS DU PATIENT ── */}
                <div className="bg-white rounded-3xl px-5 py-4 shadow-sm border border-slate-100 flex items-center gap-4 flex-wrap">
                  <KeyRound size={18} className="text-[#7C3AED]" />
                  <div className="flex-1 min-w-[220px]">
                    <p className="text-sm font-black text-slate-800">Accès du patient</p>
                    <p className="text-[11px] font-bold text-slate-400">
                      Générez un code à 6 caractères : le patient (ou son parent) l’utilise sur « Activer mon compte » pour créer ses identifiants.
                    </p>
                  </div>
                  {activationCode ? (
                    <span data-testid="activation-code" className="text-xl font-black tracking-[0.3em] text-[#7C3AED] bg-purple-50 border border-purple-100 rounded-2xl px-4 py-2">
                      {activationCode}
                    </span>
                  ) : (
                    <button onClick={handleActivationCode} className="px-4 py-2 rounded-full border-2 border-purple-200 text-[#7C3AED] text-sm font-black hover:bg-purple-50">
                      Générer un code d’activation
                    </button>
                  )}
                  <a href={ANALYTICS_URL} target="_blank" rel="noreferrer" className="px-4 py-2 rounded-full bg-slate-50 border border-slate-200 text-slate-600 text-sm font-black hover:bg-slate-100 flex items-center gap-1">
                    Analyses détaillées <ExternalLink size={13} />
                  </a>
                </div>

                {loadingPatient && <p className="text-xs font-bold text-slate-400 animate-pulse">Mise à jour…</p>}

                {/* ── MIDDLE ROW ── */}
                <div className="grid grid-cols-[1fr_340px] gap-5">
                  <div className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <Target size={18} className="text-[#7C3AED]" />
                        <h2 className="font-black text-slate-800">Amplitude de mouvement &amp; Symétrie</h2>
                      </div>
                      <span className="text-xs font-bold text-slate-400 bg-slate-50 px-3 py-1 rounded-full border border-slate-100">
                        Objectif : {hibouConfig.target_angle}°
                      </span>
                    </div>
                    <p className="text-xs font-bold text-slate-400 mb-5">Exercice : Le Hibou — Rotation cervicale</p>

                    {!latestHibou ? (
                      <div className="bg-slate-50 rounded-2xl p-6 text-center text-sm font-bold text-slate-400 border border-dashed border-slate-200">
                        {hibou ? "Aucune séance du Hibou pour l’instant." : "Le Hibou n’est pas encore attribué à ce patient."}
                      </div>
                    ) : (
                      <>
                        <div className="grid grid-cols-3 gap-4">
                          <div className="bg-slate-50 rounded-2xl p-4 flex flex-col gap-2 border border-slate-100">
                            <span className="text-xs font-black text-slate-500">← Rotation gauche</span>
                            <span className="text-3xl font-black text-slate-800">{Math.round(leftNow)}°</span>
                            <span className="text-[11px] font-bold text-slate-400">/ {hibouConfig.target_angle}° cible</span>
                            <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                              <div className="h-full bg-[#7C3AED] rounded-full" style={{ width: `${Math.min((leftNow / hibouConfig.target_angle) * 100, 100)}%` }} />
                            </div>
                          </div>
                          <div className="bg-slate-50 rounded-2xl p-4 flex flex-col items-center gap-2 border border-slate-100">
                            <span className="text-xs font-black text-slate-500">Indice de symétrie</span>
                            <div className="relative w-24 h-24">
                              <CircleGauge value={symmetry} max={100} color={symmetry >= 80 ? "#10B981" : "#F59E0B"} />
                              <div className="absolute inset-0 flex items-center justify-center">
                                <span className="text-xl font-black text-slate-800">{symmetry}%</span>
                              </div>
                            </div>
                            <div className={`text-[11px] font-bold flex items-center gap-1 ${symmetry >= 80 ? "text-emerald-600" : "text-amber-500"}`}>
                              {symmetry >= 80 ? <CheckCircle2 size={11} /> : <AlertTriangle size={11} />}
                              {symmetry >= 80 ? "Symétrique" : "Asymétrie"}
                            </div>
                          </div>
                          <div className="bg-slate-50 rounded-2xl p-4 flex flex-col gap-2 border border-slate-100">
                            <span className="text-xs font-black text-slate-500">Rotation droite →</span>
                            <span className="text-3xl font-black text-slate-800">{Math.round(rightNow)}°</span>
                            <span className="text-[11px] font-bold text-slate-400">/ {hibouConfig.target_angle}° cible</span>
                            <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                              <div className="h-full bg-[#06B6D4] rounded-full" style={{ width: `${Math.min((rightNow / hibouConfig.target_angle) * 100, 100)}%` }} />
                            </div>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3 mt-3">
                          <div className="bg-indigo-50/50 border border-indigo-100 rounded-2xl p-3 flex items-center gap-3">
                            <Clock size={18} className="text-indigo-400 flex-shrink-0" />
                            <div>
                              <p className="text-xs font-bold text-slate-400">Durée de maintien moyenne</p>
                              <p className="text-lg font-black text-slate-800">
                                {latestHibou.metrics.hold_seconds_avg != null ? `${Number(latestHibou.metrics.hold_seconds_avg).toFixed(1).replace(".", ",")} s` : "—"}
                              </p>
                            </div>
                          </div>
                          <div className="bg-cyan-50/50 border border-cyan-100 rounded-2xl p-3 flex items-center gap-3">
                            <Activity size={18} className="text-cyan-400 flex-shrink-0" />
                            <div>
                              <p className="text-xs font-bold text-slate-400">Fluidité du mouvement</p>
                              <p className="text-lg font-black text-slate-800">
                                {latestHibou.metrics.smoothness != null ? `${Math.round(Number(latestHibou.metrics.smoothness))} / 100` : "—"}
                              </p>
                            </div>
                          </div>
                        </div>
                      </>
                    )}
                  </div>

                  {/* Prescription & configuration */}
                  <div className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100 flex flex-col gap-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">🎮</span>
                        <h2 className="font-black text-slate-800 text-sm">Prescription &amp; Configuration</h2>
                      </div>
                      {availableGames.length > 0 && (
                        <button onClick={() => setModal({ kind: "add-game" })} className="flex items-center gap-1 text-[11px] font-bold text-[#7C3AED] hover:underline">
                          <Plus size={11} /> Ajouter un jeu
                        </button>
                      )}
                    </div>
                    {patientGames.length === 0 && (
                      <p className="text-xs font-bold text-slate-400 bg-slate-50 rounded-2xl p-4 text-center">
                        Aucun jeu attribué. Ajoutez-en un pour qu’il apparaisse dans l’espace du patient.
                      </p>
                    )}
                    {patientGames.map((g) => {
                      const meta = gameMeta(g.game_slug);
                      const config = withDefaults(g.configuration);
                      return (
                        <div key={g.id} className="p-2 bg-slate-50 rounded-2xl border border-slate-100">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl overflow-hidden bg-white border border-slate-100 flex-shrink-0">
                              <Image src={meta.image} width={40} height={40} alt={g.game_name || "Jeu"} className="w-full h-full object-cover" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-black text-slate-700 truncate">{g.game_name}</p>
                              <p className="text-[10px] font-bold text-slate-400 truncate">
                                {config.target_angle}° · {config.hold_seconds} s · {config.repetitions} rép. · {SPEED_LABELS[config.speed]}
                              </p>
                            </div>
                            <button
                              onClick={() => toggleGame(g)}
                              className={`text-[10px] font-black px-2 py-0.5 rounded-full border ${config.active ? "text-emerald-600 bg-emerald-50 border-emerald-100" : "text-slate-500 bg-white border-slate-200"}`}
                              title="Afficher / masquer pour le patient"
                            >
                              {config.active ? "Actif" : "Masqué"}
                            </button>
                            <button onClick={() => setModal({ kind: "edit-game", pg: g })} className="text-slate-400 hover:text-[#7C3AED]" aria-label={`Régler ${g.game_name}`}>
                              <Settings size={15} />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* ── BOTTOM ROW ── */}
                <div className="grid grid-cols-[1fr_420px] gap-5">
                  <div className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100">
                    <div className="flex items-center gap-2 mb-4">
                      <span className="text-lg">💜</span>
                      <h2 className="font-black text-slate-800">Douleur &amp; Effort</h2>
                      <span className="text-xs font-bold text-slate-400">(auto-évaluation après séance)</span>
                    </div>
                    {painData.length === 0 ? (
                      <p className="text-xs font-bold text-slate-400 bg-slate-50 rounded-2xl p-4 text-center">Pas encore d’auto-évaluation.</p>
                    ) : (
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-[11px] font-bold text-[#7C3AED] flex items-center gap-1 mb-2"><BarChart3 size={11} /> Douleur (0–5)</p>
                          <BarChart data={painData} color="#F472B6" labels={ratedLabels} />
                        </div>
                        <div>
                          <p className="text-[11px] font-bold text-cyan-600 flex items-center gap-1 mb-2"><TrendingUp size={11} /> Effort perçu (0–5)</p>
                          <BarChart data={effortData} color="#06B6D4" labels={ratedLabels} />
                        </div>
                      </div>
                    )}
                    {latestPain != null && latestPain >= 4 && (
                      <div className="mt-3 bg-amber-50 border border-amber-200 rounded-2xl p-3 flex gap-2">
                        <AlertTriangle size={14} className="text-amber-500 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="text-[11px] font-black text-amber-800">Douleur élevée signalée</p>
                          <p className="text-[10px] font-bold text-amber-600 mt-0.5">
                            Le patient a déclaré une douleur de {latestPain}/5 à la dernière séance. Pensez à vérifier l’amplitude et la limite de sécurité.
                          </p>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="bg-white rounded-3xl p-5 shadow-sm border border-slate-100 flex flex-col gap-4">
                    {rotLeft.length > 0 && (
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <TrendingUp size={15} className="text-[#7C3AED]" />
                            <h2 className="font-black text-slate-800 text-sm">Évolution de l’amplitude</h2>
                          </div>
                          <div className="flex items-center gap-3 text-[9px] font-bold text-slate-400">
                            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#7C3AED] inline-block" /> Gauche</span>
                            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#06B6D4] inline-block" /> Droite</span>
                            <span className="flex items-center gap-1"><span className="w-4 h-0.5 bg-slate-300 inline-block" /> Objectif</span>
                          </div>
                        </div>
                        <div className="relative">
                          <Sparkline data={rotLeft} color="#7C3AED" target={hibouConfig.target_angle} />
                          <div className="absolute inset-0">
                            <Sparkline data={rotRight} color="#06B6D4" target={hibouConfig.target_angle} />
                          </div>
                        </div>
                      </div>
                    )}

                    <div>
                      <p className="text-[11px] font-black text-slate-600 flex items-center gap-1 mb-2">
                        <CalendarDays size={11} /> Historique des séances ({sessions.length})
                      </p>
                      {sessions.length === 0 ? (
                        <p className="text-xs font-bold text-slate-400 bg-slate-50 rounded-2xl p-4 text-center">Aucune séance enregistrée.</p>
                      ) : (
                        <table className="w-full text-[10px]">
                          <thead>
                            <tr className="text-slate-400 font-bold border-b border-slate-100">
                              <th className="pb-1.5 text-left">Date</th>
                              <th className="pb-1.5 text-left">Jeu</th>
                              <th className="pb-1.5 text-left">Durée</th>
                              <th className="pb-1.5 text-left">Score</th>
                              <th className="pb-1.5 text-left">Statut</th>
                            </tr>
                          </thead>
                          <tbody>
                            {sessions.slice(0, 8).map((s) => {
                              const done = s.metrics.completed !== false;
                              return (
                                <tr key={s.id} className="border-b border-slate-50 hover:bg-slate-50/50">
                                  <td className="py-1.5 font-bold text-slate-700">{formatDate(sessionDate(s))}</td>
                                  <td className="py-1.5 font-bold text-slate-500">{s.game_name}</td>
                                  <td className="py-1.5 font-bold text-slate-500">{formatDuration(s.duration_sec)}</td>
                                  <td className="py-1.5 font-black text-slate-800">{s.metrics.score != null ? Math.round(Number(s.metrics.score)) : "—"}</td>
                                  <td className="py-1.5">
                                    <span className={`inline-flex items-center gap-0.5 font-black px-1.5 py-0.5 rounded-full ${done ? "bg-emerald-50 text-emerald-600" : "bg-amber-50 text-amber-600"}`}>
                                      {done ? <><CheckCircle2 size={9} /> Complet</> : <><XCircle size={9} /> Partiel</>}
                                    </span>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      )}
                    </div>
                  </div>
                </div>
              </>
            )}
          </main>
        </div>
      </div>

      {/* ── MODALES ── */}
      {modal?.kind === "new-patient" && (
        <NewPatientModal
          onClose={() => setModal(null)}
          onCreated={async (created) => {
            setModal(null);
            await loadPatients(created.id);
            notify("Patient créé");
          }}
        />
      )}
      {modal?.kind === "diagnosis" && patient && (
        <DiagnosisModal
          initial={diagnosis}
          onClose={() => setModal(null)}
          onSave={async (text) => {
            await createConsultation(patient.id, text);
            setDiagnosis(text);
            setModal(null);
            notify("Diagnostic enregistré");
          }}
        />
      )}
      {modal?.kind === "add-game" && patient && (
        <Modal title="Ajouter un jeu" onClose={() => setModal(null)}>
          <AddGameForm
            games={availableGames}
            onSubmit={async (gameId, config) => {
              await assignGame(patient.id, gameId, config);
              setModal(null);
              await loadPatient(patient.id, catalog);
              notify("Jeu attribué");
            }}
          />
        </Modal>
      )}
      {modal?.kind === "edit-game" && patient && (
        <Modal title={`Réglages — ${modal.pg.game_name}`} onClose={() => setModal(null)}>
          <ConfigForm
            initial={modal.pg.configuration}
            submitLabel="Enregistrer les réglages"
            onSubmit={async (config) => {
              await updateGameConfig(modal.pg.id, config);
              setModal(null);
              await loadPatient(patient.id, catalog);
              notify("Réglages enregistrés");
            }}
          />
        </Modal>
      )}

      {toast && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 text-white text-sm font-bold px-4 py-2.5 rounded-2xl shadow-lg">
          {toast}
        </div>
      )}
    </div>
  );
}

function NewPatientModal({ onClose, onCreated }: { onClose: () => void; onCreated: (p: Patient) => Promise<void> }) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [age, setAge] = useState(8);
  const [diagnosisText, setDiagnosisText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!firstName.trim() || !lastName.trim()) {
      setError("Le prénom et le nom sont obligatoires.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const created = await createPatient(firstName.trim(), lastName.trim(), age);
      if (diagnosisText.trim()) await createConsultation(created.id, diagnosisText.trim());
      await onCreated(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Création impossible.");
      setSaving(false);
    }
  };

  return (
    <Modal title="Nouveau patient" onClose={onClose}>
      <form onSubmit={submit} className="flex flex-col gap-3">
        <div className="grid grid-cols-[1fr_1fr_90px] gap-3">
          <Field label="Prénom"><input value={firstName} onChange={(e) => setFirstName(e.target.value)} className={fieldClass} placeholder="Salma" /></Field>
          <Field label="Nom"><input value={lastName} onChange={(e) => setLastName(e.target.value)} className={fieldClass} placeholder="Ben Ali" /></Field>
          <Field label="Âge"><input type="number" min={1} max={18} value={age} onChange={(e) => setAge(Number(e.target.value))} className={fieldClass} /></Field>
        </div>
        <Field label="Diagnostic (optionnel)">
          <input value={diagnosisText} onChange={(e) => setDiagnosisText(e.target.value)} className={fieldClass} placeholder="Ex. : torticolis post-traumatique" />
        </Field>
        {error && <p className="text-xs font-bold text-rose-600">{error}</p>}
        <button type="submit" disabled={saving} className="mt-1 py-2.5 rounded-full bg-[#7C3AED] hover:bg-[#6D28D9] disabled:opacity-60 text-white text-sm font-black">
          {saving ? "Création…" : "Créer le patient"}
        </button>
      </form>
    </Modal>
  );
}

function DiagnosisModal({ initial, onClose, onSave }: { initial: string; onClose: () => void; onSave: (text: string) => Promise<void> }) {
  const [text, setText] = useState(initial);
  const [error, setError] = useState<string | null>(null);
  return (
    <Modal title="Diagnostic" onClose={onClose}>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          if (!text.trim()) return setError("Le diagnostic ne peut pas être vide.");
          try {
            await onSave(text.trim());
          } catch (err) {
            setError(err instanceof Error ? err.message : "Enregistrement impossible.");
          }
        }}
        className="flex flex-col gap-3"
      >
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={3} className={fieldClass} placeholder="Diagnostic du patient…" />
        {error && <p className="text-xs font-bold text-rose-600">{error}</p>}
        <button type="submit" className="py-2.5 rounded-full bg-[#7C3AED] text-white text-sm font-black">Enregistrer</button>
      </form>
    </Modal>
  );
}

function AddGameForm({ games, onSubmit }: { games: Game[]; onSubmit: (gameId: number, config: GameConfig) => Promise<void> }) {
  const [gameId, setGameId] = useState<number>(games.find((g) => g.slug === "le-hibou")?.id ?? games[0]?.id);
  return (
    <div className="flex flex-col gap-3">
      <Field label="Jeu">
        <select value={gameId} onChange={(e) => setGameId(Number(e.target.value))} className={fieldClass}>
          {games.map((g) => (
            <option key={g.id} value={g.id}>
              {g.name}{gameMeta(g.slug).playable ? "" : " (bientôt jouable)"}
            </option>
          ))}
        </select>
      </Field>
      <ConfigForm initial={{}} submitLabel="Attribuer ce jeu" onSubmit={(config) => onSubmit(gameId, config)} />
    </div>
  );
}
