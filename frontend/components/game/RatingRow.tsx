"use client";

// Auto-évaluation de fin de séance (douleur, effort) commune aux jeux SensAI.

export default function RatingRow({
  label, value, onChange, faces, testId,
}: { label: string; value: number | null; onChange: (v: number) => void; faces: string[]; testId: string }) {
  return (
    <div className="mt-4">
      <p className="text-sm font-black text-slate-700 mb-2">{label}</p>
      <div className="flex justify-center gap-2">
        {faces.map((face, i) => (
          <button
            key={i}
            onClick={() => onChange(i)}
            data-testid={`${testId}-${i}`}
            className={`w-11 h-11 rounded-2xl text-2xl border-2 transition-all ${value === i ? "border-[#7C3AED] bg-purple-50 scale-110" : "border-slate-100 bg-white"}`}
            aria-label={`${label} ${i} out of 5`}
          >
            {face}
          </button>
        ))}
      </div>
    </div>
  );
}
