"use client";

// L'espace thérapeute est le dashboard d'analyse SensAI (Streamlit).
// Cette page y redirige le thérapeute connecté avec sa session.

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, getMe, getToken, logout, therapistSpaceUrl } from "@/lib/api";

export default function TherapistRedirect() {
  const router = useRouter();
  const [message, setMessage] = useState("Ouverture de votre espace thérapeute…");

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    getMe()
      .then((me) => {
        if (me.role !== "therapist") {
          router.replace("/dashboard");
          return;
        }
        window.location.href = therapistSpaceUrl();
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) {
          logout();
          router.replace("/login");
        } else {
          setMessage(err instanceof Error ? err.message : "Erreur de connexion.");
        }
      });
  }, [router]);

  return (
    <div className="min-h-screen bg-[#EEF2FA] font-outfit flex items-center justify-center">
      <div className="text-center">
        <div className="text-5xl animate-bounce">🦉</div>
        <p className="mt-3 font-black text-[#312E81]">{message}</p>
      </div>
    </div>
  );
}
