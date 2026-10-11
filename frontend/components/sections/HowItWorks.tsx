import Image from "next/image";
import Badge from "@/components/ui/Badge";
import Sticker from "@/components/ui/Sticker";

const steps = [
  { label: "The Child",             src: "/Assets/Landing Page/flow/child icon.png",       color: "text-yellow-600" },
  { label: "Movement",              src: "/Assets/Landing Page/flow/movement icon.png",    color: "text-orange-500" },
  { label: "Device Camera",         src: "/Assets/Landing Page/flow/camera icon copy.png", color: "text-cyan-600" },
  { label: "Computer Vision",       src: "/Assets/Landing Page/flow/vision icon.png",      color: "text-purple-600" },
  { label: "Interaction",           src: "/Assets/Landing Page/flow/interaction icon.png", color: "text-blue-600" },
  { label: "Session Data",          src: "/Assets/Landing Page/flow/data icon.png",        color: "text-emerald-600" },
];

export default function HowItWorks() {
  return (
    <section id="comment-ca-marche" className="relative overflow-hidden bg-[#FDFCFB] px-6 pt-24 pb-20">
      {/* Cloud SVG divider at top */}
      <div className="absolute top-0 left-0 right-0 w-full overflow-hidden pointer-events-none rotate-180" style={{height: '90px'}}>
        <svg viewBox="0 0 1440 90" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" className="w-full h-full">
          <path
            d="M0,45 C70,5 130,80 220,42 C300,8 350,72 450,40 C530,10 580,75 680,42 C770,12 820,70 930,42 C1020,16 1070,74 1170,44 C1260,16 1320,72 1400,46 L1440,48 L1440,90 L0,90 Z"
            fill="#EEF2FF"
          />
          <path
            d="M0,62 C80,32 150,88 250,58 C340,30 390,82 490,56 C580,32 640,84 750,58 C850,34 910,82 1020,56 C1120,32 1180,84 1290,58 C1370,36 1420,78 1440,65 L1440,90 L0,90 Z"
            fill="#EEF2FF"
            opacity="0.7"
          />
        </svg>
      </div>

      <Sticker name="cosmic_23" size={56} className="top-20 right-4 opacity-50" />
      <Sticker name="kawaii_2" size={56} className="bottom-10 left-4 opacity-45" />

      <div className="relative mx-auto max-w-6xl">
        {/* Header: stacked, left-aligned */}
        <div className="max-w-2xl space-y-3">
          <Badge className="bg-[#DBEAFE] text-[#2563EB]">How It Works</Badge>
          <h2 className="font-outfit text-3xl font-extrabold leading-tight text-slate-900 sm:text-4xl">
            An environment designed around the child
          </h2>
          <p className="text-sm leading-relaxed text-slate-600 sm:text-base">
            SensAI combines play, movement, and technology to create{" "}
            <span className="font-bold text-slate-800">
              a more interactive rehabilitation experience
            </span>.
          </p>
        </div>

        {/* Flow: icon + label = one unit */}
        <ol className="mt-10 grid grid-cols-2 gap-x-4 gap-y-8 sm:grid-cols-3 lg:flex lg:items-start lg:justify-between lg:gap-0">
          {steps.map((step, i) => (
            <li key={step.label} className="contents lg:flex lg:flex-1 lg:items-start">
              <div className="flex flex-col items-center gap-3 text-center lg:flex-1">
                <div className="h-24 w-24 sm:h-28 sm:w-28">
                  <Image
                    src={step.src}
                    alt=""
                    width={112}
                    height={112}
                    className="h-full w-full object-contain drop-shadow-md"
                  />
                </div>
                <span className={`max-w-[110px] text-xs font-bold leading-tight ${step.color}`}>
                  {step.label}
                </span>
              </div>

              {i < steps.length - 1 && (
                <span
                  aria-hidden
                  className="hidden shrink-0 text-xl font-bold text-blue-400 lg:mt-10 lg:block"
                >
                  →
                </span>
              )}
            </li>
          ))}
        </ol>

        {/* Slogan */}
        <p className="mt-10 flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-center font-handwriting text-2xl font-bold tracking-wide sm:text-3xl">
          <span className="text-pink-500">✨ The child plays.</span>
          <span className="text-teal-600">The system observes.</span>
          <span className="text-purple-600">The therapist guides. ✨</span>
        </p>
      </div>
    </section>
  );
}