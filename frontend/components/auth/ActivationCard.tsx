"use client";

import { useState, useRef } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { activateAccount, ApiError } from "@/lib/api";

export default function ActivationCard() {
  const [code, setCode] = useState(["", "", "", "", "", ""]);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [activeAlert, setActiveAlert] = useState<"error" | "expired" | "used" | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setActiveAlert(null);
    setFormError(null);
    const fullCode = code.join("").trim();
    if (fullCode.length !== 6) {
      setFormError("Saisissez les 6 caractères du code d'activation.");
      return;
    }
    if (!email.trim() || !password) {
      setFormError("Renseignez une adresse e-mail et un mot de passe.");
      return;
    }
    if (password.length < 6) {
      setFormError("Le mot de passe doit contenir au moins 6 caractères.");
      return;
    }
    if (password !== confirmPassword) {
      setFormError("Les mots de passe ne correspondent pas.");
      return;
    }
    setLoading(true);
    try {
      await activateAccount(fullCode, email.trim(), password);
      router.push("/dashboard");
    } catch (err) {
      setLoading(false);
      if (err instanceof ApiError) {
        if (err.status === 404) return setActiveAlert("error");
        if (err.status === 410) return setActiveAlert("expired");
        if (err.status === 409 && err.detail.toLowerCase().includes("email")) {
          return setFormError("Cette adresse e-mail est déjà utilisée.");
        }
        if (err.status === 409) return setActiveAlert("used");
        if (err.status === 422) return setFormError("Vérifiez l’adresse e-mail saisie.");
      }
      setFormError(err instanceof Error ? err.message : "Activation impossible.");
    }
  };

  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const handleCodeChange = (index: number, raw: string) => {
    let value = raw.toUpperCase().replace(/[^A-Z0-9]/g, "");
    // Saisie d'un caractère dans une case déjà remplie : on garde le dernier.
    if (value.length === 2 && code[index]) value = value.slice(-1);
    if (value.length > 1) {
      // Collage du code complet
      const pasted = value.slice(0, 6 - index).split("");
      const newCode = [...code];
      pasted.forEach((char, i) => {
        newCode[index + i] = char;
      });
      setCode(newCode);
      inputRefs.current[Math.min(index + pasted.length, 5)]?.focus();
      return;
    }

    const newCode = [...code];
    newCode[index] = value;
    setCode(newCode);

    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const passwordsMatch = password.length > 0 && password === confirmPassword;

  return (
    <div className="relative w-full max-w-[440px] mx-auto lg:mx-0">
      {/* Background shape from Assets */}
      <div className="absolute inset-0 -z-10 filter drop-shadow-[0_12px_40px_rgba(139,92,246,0.16)] pointer-events-none">
        <Image
          src="/Assets/connexion/login-card-bg.png"
          alt="Fond de la carte d'activation"
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
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
          Activation
        </div>

        {/* Heading */}
        <h1 className="text-[23px] sm:text-[26px] leading-[1.15] font-extrabold text-[#1E293B] mb-1 font-outfit">
          Activez votre espace<br />
          <span className="text-[#3B82F6]">Sens</span><span className="text-[#8B5CF6]">A</span><span className="text-[#EC4899]">I</span> !
        </h1>
        <p className="text-[12px] text-slate-500 mb-3 leading-relaxed">
          Entrez le code fourni par votre thérapeute pour créer vos identifiants.
        </p>

        {/* Optional Alert Banners */}
        {activeAlert === "error" && (
          <div className="mb-2.5 p-2.5 rounded-xl bg-[#FFE4E6] border border-[#FECDD3] text-[#E11D48] text-[11px] font-medium flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-4 h-4 rounded-full bg-[#E11D48] text-white flex items-center justify-center font-bold text-[10px] flex-shrink-0">!</span>
              <span>Code non reconnu. Vérifiez le code saisi.</span>
            </div>
            <button onClick={() => setActiveAlert(null)} className="text-[#E11D48] hover:opacity-75">✕</button>
          </div>
        )}

        {activeAlert === "expired" && (
          <div className="mb-2.5 p-2.5 rounded-xl bg-[#FEF3C7] border border-[#FDE68A] text-[#D97706] text-[11px] font-medium flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-4 h-4 rounded-full bg-[#D97706] text-white flex items-center justify-center font-bold text-[10px] flex-shrink-0">!</span>
              <span>Ce code a expiré. Contactez votre thérapeute.</span>
            </div>
            <button onClick={() => setActiveAlert(null)} className="text-[#D97706] hover:opacity-75">✕</button>
          </div>
        )}

        {activeAlert === "used" && (
          <div className="mb-2.5 p-2.5 rounded-xl bg-[#EEF2FF] border border-[#C7D2FE] text-[#4F46E5] text-[11px] font-medium flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-4 h-4 rounded-full bg-[#4F46E5] text-white flex items-center justify-center font-bold text-[10px] flex-shrink-0">i</span>
              <span>Ce code a déjà été utilisé. <Link href="/login" className="font-bold underline">Se connecter</Link></span>
            </div>
            <button onClick={() => setActiveAlert(null)} className="text-[#4F46E5] hover:opacity-75">✕</button>
          </div>
        )}

        {formError && (
          <div role="alert" className="mb-2.5 p-2.5 rounded-xl bg-[#FFE4E6] border border-[#FECDD3] text-[#E11D48] text-[11px] font-medium flex items-center gap-1.5">
            <span className="w-4 h-4 rounded-full bg-[#E11D48] text-white flex items-center justify-center font-bold text-[10px] flex-shrink-0">!</span>
            <span>{formError}</span>
          </div>
        )}

        {/* Activation Code Section */}
        <div className="mb-3">
          <label className="block text-[11px] font-bold text-slate-700 mb-1.5">
            Code d'activation
          </label>
          <div className="grid grid-cols-6 gap-1.5">
            {code.map((digit, idx) => (
              <input
                key={idx}
                ref={(el) => { inputRefs.current[idx] = el; }}
                type="text"
                maxLength={6}
                aria-label={`Caractère ${idx + 1} du code`}
                value={digit}
                onChange={(e) => handleCodeChange(idx, e.target.value)}
                onKeyDown={(e) => handleKeyDown(idx, e)}
                placeholder="*"
                className="w-full h-9 text-center font-bold text-[15px] text-slate-800 rounded-xl border border-[#E0E7FF] bg-[#F0F5FF]/70 focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]/30 focus:border-[#8B5CF6] transition-all placeholder-slate-300 uppercase"
              />
            ))}
          </div>
          <p className="mt-1 flex items-center gap-1 text-[10.5px] text-slate-400">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="16" x2="12" y2="12" />
              <line x1="12" y1="8" x2="12.01" y2="8" />
            </svg>
            Code à 6 caractères remis par votre thérapeute.
          </p>
        </div>

        {/* Credentials Form */}
        <form onSubmit={handleSubmit} className="space-y-2">
          <label className="block text-[11px] font-bold text-slate-700 -mb-0.5">
            Créer vos identifiants
          </label>

          {/* Email */}
          <div>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="4" width="20" height="16" rx="2" />
                  <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
                </svg>
              </span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Adresse e-mail"
                className="w-full pl-8 pr-3 py-2 rounded-xl border border-[#E0E7FF] text-[12px] text-slate-700 placeholder-slate-400 bg-[#F0F5FF]/70 focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]/30 focus:border-[#8B5CF6] transition-all"
              />
            </div>
          </div>

          {/* Password */}
          <div>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </span>
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Mot de passe"
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
          </div>

          {/* Confirm Password */}
          <div>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </span>
              <input
                type={showConfirmPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirmez votre mot de passe"
                className="w-full pl-8 pr-9 py-2 rounded-xl border border-[#E0E7FF] text-[12px] text-slate-700 placeholder-slate-400 bg-[#F0F5FF]/70 focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]/30 focus:border-[#8B5CF6] transition-all"
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-[#8B5CF6] transition-colors"
              >
                {showConfirmPassword
                  ? <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" y1="2" x2="22" y2="22"/></svg>
                  : <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                }
              </button>
            </div>
            {passwordsMatch && (
              <p className="mt-0.5 flex items-center gap-1 text-[10.5px] text-[#10B981] font-semibold">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 6L9 17l-5-5" />
                </svg>
                Les mots de passe correspondent
              </p>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-[#6366F1] via-[#7C3AED] to-[#0EA5E9] hover:opacity-95 disabled:opacity-60 text-white font-bold py-2.5 rounded-full flex items-center justify-center gap-2 transition-all shadow-md text-[12.5px] mt-2"
          >
            {loading ? "Activation…" : "Activer mon compte"}
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        </form>

        {/* Back to Login Link */}
        <div className="mt-2.5 text-center text-[11px] text-slate-500 font-medium">
          Déjà un compte ?{" "}
          <Link href="/login" className="text-[#2563EB] font-bold hover:underline ml-1">
            Se connecter
          </Link>
        </div>
      </div>
    </div>
  );
}
