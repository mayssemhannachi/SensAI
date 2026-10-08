"use client";

import dynamic from "next/dynamic";
import Script from "next/script";

// We must dynamically import the game component with ssr: false
// because Phaser and MediaPipe rely heavily on browser APIs (window, canvas, camera)
const LeHibouGame = dynamic(() => import("../../../../components/game/LeHibouGame"), {
  ssr: false,
  loading: () => (
    <div className="min-h-screen bg-[#EEF2FA] flex items-center justify-center font-outfit">
      <div className="text-center space-y-4">
        <div className="text-6xl animate-bounce">🦉</div>
        <h2 className="text-2xl font-black text-[#312E81]">Chargement du jeu...</h2>
      </div>
    </div>
  ),
});

export default function LeHibouPage() {
  return (
    <>
      <Script src="https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js" strategy="afterInteractive" />
      <Script src="https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/face_mesh.js" strategy="afterInteractive" />
      <LeHibouGame />
    </>
  );
}
