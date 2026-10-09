"use client";

// Déconnexion commune au site et à l'espace thérapeute (dashboard) :
// efface la session du site puis renvoie vers la page de connexion unique.

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { logout } from "@/lib/api";

export default function LogoutPage() {
  const router = useRouter();

  useEffect(() => {
    logout();
    const reason = new URLSearchParams(window.location.search).get("reason");
    router.replace(reason ? `/login?reason=${encodeURIComponent(reason)}` : "/login");
  }, [router]);

  return (
    <div className="min-h-screen bg-[#EEF2FA] flex items-center justify-center font-outfit">
      <p className="text-slate-500 font-bold">Déconnexion…</p>
    </div>
  );
}
