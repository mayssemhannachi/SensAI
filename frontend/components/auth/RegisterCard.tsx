"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { goToSpace, registerTherapist, type TherapistSpecialty } from "@/lib/api";

const inputClass =
  "w-full pl-3 pr-3 py-2 rounded-xl border border-[#E0E7FF] text-[12px] text-slate-700 placeholder-slate-400 bg-[#F0F5FF]/70 focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]/30 focus:border-[#8B5CF6] transition-all";

export default function RegisterCard() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [specialty, setSpecialty] = useState<TherapistSpecialty>("kinesitherapist");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!fullName.trim() || !email.trim() || !password) {
      setError("All fields are required.");
      return;
    }
    if (password.length < 6) {
      setError("Password must contain at least 6 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      const role = await registerTherapist(fullName.trim(), email.trim(), password, specialty);
      goToSpace(role, router.push);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed.");
      setLoading(false);
    }
  };

  return (
    <div className="relative w-full max-w-[440px] mx-auto lg:mx-0">
      <div className="absolute inset-0 -z-10 filter drop-shadow-[0_12px_40px_rgba(139,92,246,0.16)] pointer-events-none">
        <Image src="/Assets/connexion/login-card-bg.png" alt="Registration card background" fill className="object-fill select-none" priority />
      </div>

      <div className="p-6 sm:p-7 relative z-10">
        <div className="inline-flex items-center gap-1.5 bg-[#EDE9FE] text-[#8B5CF6] text-[10px] font-bold px-3 py-0.5 rounded-full mb-2 tracking-wide">
          Therapist Space
        </div>
        <h1 className="text-[24px] sm:text-[26px] leading-[1.15] font-extrabold text-[#1E293B] mb-1 font-outfit">
          Create your account<br />
          <span className="text-[#3B82F6]">Sens</span><span className="text-[#8B5CF6]">A</span><span className="text-[#EC4899]">I</span> Therapist
        </h1>
        <p className="text-[12px] text-slate-500 mb-3 leading-relaxed">
          Monitor your patients, personalize their games, and analyze their progress.
        </p>

        {error && (
          <div role="alert" className="mb-2.5 p-2.5 rounded-xl bg-[#FFE4E6] border border-[#FECDD3] text-[#E11D48] text-[11px] font-medium flex items-center gap-1.5">
            <span className="w-4 h-4 rounded-full bg-[#E11D48] text-white flex items-center justify-center font-bold text-[10px] flex-shrink-0">!</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-2">
          <div>
            <label className="block text-[11px] font-bold text-slate-700 mb-0.5" htmlFor="full_name">Full Name</label>
            <input id="full_name" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Dr. Sarah Johnson" className={inputClass} />
          </div>
          <div>
            <label className="block text-[11px] font-bold text-slate-700 mb-0.5" htmlFor="reg_email">Email address</label>
            <input id="reg_email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="your@email.com" className={inputClass} />
          </div>
          <div>
            <label className="block text-[11px] font-bold text-slate-700 mb-0.5" htmlFor="reg_specialty">Your Specialty</label>
            <select
              id="reg_specialty"
              value={specialty}
              onChange={(e) =>
                setSpecialty(e.target.value === "ergotherapist" ? "ergotherapist" : "kinesitherapist")
              }
              className={inputClass}
            >
              <option value="kinesitherapist">Physiotherapist / Kinesiotherapist</option>
              <option value="ergotherapist">Occupational Therapist</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-[11px] font-bold text-slate-700 mb-0.5" htmlFor="reg_password">Password</label>
              <input id="reg_password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" className={inputClass} />
            </div>
            <div>
              <label className="block text-[11px] font-bold text-slate-700 mb-0.5" htmlFor="reg_confirm">Confirm Password</label>
              <input id="reg_confirm" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="••••••••" className={inputClass} />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-[#6366F1] via-[#7C3AED] to-[#0EA5E9] hover:opacity-95 disabled:opacity-60 text-white font-bold py-2.5 rounded-full flex items-center justify-center gap-2 transition-all shadow-md text-[12.5px] mt-2"
          >
            {loading ? "Creating account…" : "Create my account"}
          </button>
        </form>

        <div className="mt-2.5 text-center text-[11px] text-slate-500 font-medium">
          Already have an account?{" "}
          <Link href="/login" className="text-[#2563EB] font-bold hover:underline ml-1">Sign In</Link>
        </div>
        <div className="mt-1 text-center text-[10.5px] text-slate-400">
          Patient or parent? Use the code provided by your therapist:{" "}
          <Link href="/activate" className="text-[#2563EB] font-bold hover:underline">Activate my account</Link>
        </div>
      </div>
    </div>
  );
}
