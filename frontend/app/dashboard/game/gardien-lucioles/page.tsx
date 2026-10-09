"use client";

import dynamic from "next/dynamic";

const LuciolesGame = dynamic(() => import("../../../../components/game/LuciolesGame"), {
  ssr: false,
  loading: () => (
    <div className="min-h-screen bg-[#EEF2FA] flex items-center justify-center font-outfit">
      <div className="text-center space-y-4">
        <div className="text-6xl animate-bounce">✨</div>
        <h2 className="text-2xl font-black text-[#312E81]">Chargement du jeu...</h2>
      </div>
    </div>
  ),
});

export default function GardienLuciolesPage() {
  return <LuciolesGame />;
}
