"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { goToSpace, login } from "@/lib/api";

export default function LoginCard() {
  const router = useRouter();
  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!email.trim() || !password) {
      setError("Renseignez votre adresse e-mail et votre mot de passe.");
      return;
    }
    setLoading(true);
    try {
      const role = await login(email.trim(), password);
      goToSpace(role, router.push);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Connexion impossible.");
      setLoading(false);
    }
  };

  return (
    <div className="relative w-full max-w-[440px] mx-auto lg:mx-0">
      {/* Background shape from Assets */}
      <div className="absolute inset-0 -z-10 filter drop-shadow-[0_12px_40px_rgba(139,92,246,0.16)] pointer-events-none">
        <Image
          src="/Assets/connexion/login-card-bg.png"
          alt="Fond de la carte de connexion"
          fill
          className="object-fill select-none"
          priority
        />
      </div>

      {/* Card Content */}
      <div className="p-6 sm:p-7 relative z-10">
        {/* Badge */}
        <div className="inline-flex items-center gap-1.5 bg-[#EDE9FE] text-[#8B5CF6] text-[10px] font-bold px-3 py-0.5 rounded-full mb-2 tracking-wide">
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          Connexion
        </div>

        {/* Heading */}
        <h1 className="text-[24px] sm:text-[26px] leading-[1.15] font-extrabold text-[#1E293B] mb-1 font-outfit">
          Bienvenue dans<br />
          l'aventure <span className="text-[#3B82F6]">Sens</span><span className="text-[#8B5CF6]">A</span><span className="text-[#EC4899]">I</span> !
        </h1>
        <p className="text-[12px] text-slate-500 mb-3 leading-relaxed">
          Connectez-vous à votre espace SensAI et poursuivez l'aventure.
        </p>

        {/* Form */}
        {error && (
          <div role="alert" className="mb-2.5 p-2.5 rounded-xl bg-[#FFE4E6] border border-[#FECDD3] text-[#E11D48] text-[11px] font-medium flex items-center gap-1.5">
            <span className="w-4 h-4 rounded-full bg-[#E11D48] text-white flex items-center justify-center font-bold text-[10px] flex-shrink-0">!</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-2.5">
          {/* Email */}
          <div>
            <label className="block text-[11px] font-bold text-slate-700 mb-0.5" htmlFor="email">
              Adresse e-mail
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="4" width="20" height="16" rx="2" />
                  <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
                </svg>
              </span>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="votre@email.com"
                className="w-full pl-8 pr-3 py-2 rounded-xl border border-[#E0E7FF] text-[12px] text-slate-700 placeholder-slate-400 bg-[#F0F5FF]/70 focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]/30 focus:border-[#8B5CF6] transition-all"
              />
            </div>
          </div>

          {/* Password */}
          <div>
            <label className="block text-[11px] font-bold text-slate-700 mb-0.5" htmlFor="password">
              Mot de passe
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </span>
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-8 pr-9 py-2 rounded-xl border border-[#E0E7FF] text-[12px] text-slate-700 placeholder-slate-400 bg-[#F0F5FF]/70 focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]/30 focus:border-[#8B5CF6] transition-all"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-[#8B5CF6] transition-colors"
              >
                {showPassword
                  ? <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" y1="2" x2="22" y2="22"/></svg>
                  : <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                }
              </button>
            </div>
            <div className="flex justify-end mt-1">
              <Link href="/forgot-password" className="hidden items-center gap-1 text-[11px] text-[#2563EB] font-semibold hover:underline">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
                Mot de passe oublié ?
              </Link>
            </div>
          </div>

          {/* Gradient Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-[#6366F1] via-[#7C3AED] to-[#0EA5E9] hover:opacity-95 disabled:opacity-60 text-white font-bold py-2.5 rounded-full flex items-center justify-center gap-2 transition-all shadow-md text-[12.5px] mt-1.5"
          >
            {loading ? "Connexion…" : "Se connecter"}
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        </form>

        {/* Divider */}
        <div className="relative my-3 flex items-center justify-center">
          <div className="w-full border-t border-slate-200/80" />
          <span className="absolute bg-white px-2.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            ou
          </span>
        </div>

        {/* Première connexion */}
        <div className="rounded-xl bg-[#F0F7FF]/80 border border-[#E0F2FE] p-2.5 sm:p-3 flex items-center gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#E0F2FE] flex items-center justify-center text-[#0EA5E9]">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="8.5" cy="7" r="4" />
              <line x1="20" y1="8" x2="20" y2="14" />
              <line x1="23" y1="11" x2="17" y2="11" />
            </svg>
          </div>
          <div>
            <p className="text-[12px] font-bold text-slate-800 leading-tight">Première connexion ?</p>
            <p className="text-[10px] text-slate-500 mt-0.5 mb-0.5">Activez votre compte avec votre code patient.</p>
            <Link href="/activate" className="text-[11px] font-bold text-[#2563EB] flex items-center gap-1 hover:underline">
              Activer mon compte
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </Link>
          </div>
        </div>

        <div className="mt-2.5 text-center text-[11px] text-slate-500 font-medium">
          Vous êtes thérapeute ?{" "}
          <Link href="/register" className="text-[#7C3AED] font-bold hover:underline ml-1">
            Créer un compte
          </Link>
        </div>
      </div>
    </div>
  );
}
