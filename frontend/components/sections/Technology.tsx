import Image from "next/image";
import { ArrowRight } from "lucide-react";
import Badge from "@/components/ui/Badge";
import Sticker from "@/components/ui/Sticker";

const features = [
  {
    icon: "/Assets/Landing Page/technologies/capture-pic.png",
    label: "Capture",
    desc: "The camera captures movement in real time.",
    bg: "bg-blue-50",
  },
  {
    icon: "/Assets/Landing Page/technologies/detection.png",
    label: "Detection",
    desc: "AI analyzes and identifies key gestures.",
    bg: "bg-purple-50",
  },
  {
    icon: "/Assets/Landing Page/technologies/interaction-pic.png",
    label: "Interaction",
    desc: "Movements become interactive gameplay actions.",
    bg: "bg-sky-50",
  },
  {
    icon: "/Assets/Landing Page/technologies/analyze.png",
    label: "Analysis",
    desc: "Every session generates actionable insights.",
    bg: "bg-teal-50",
  },
];

export default function Technology() {
  return (
    <section className="pt-24 pb-20 px-6 bg-[#FAF5FF] relative overflow-hidden">
      {/* Cloud SVG divider at top */}
      <div className="absolute top-0 left-0 right-0 w-full overflow-hidden pointer-events-none rotate-180" style={{height: '90px'}}>
        <svg viewBox="0 0 1440 90" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" className="w-full h-full">
          <path
            d="M0,45 C70,5 130,80 220,42 C300,8 350,72 450,40 C530,10 580,75 680,42 C770,12 820,70 930,42 C1020,16 1070,74 1170,44 C1260,16 1320,72 1400,46 L1440,48 L1440,90 L0,90 Z"
            fill="#FDFCFB"
          />
          <path
            d="M0,62 C80,32 150,88 250,58 C340,30 390,82 490,56 C580,32 640,84 750,58 C850,34 910,82 1020,56 C1120,32 1180,84 1290,58 C1370,36 1420,78 1440,65 L1440,90 L0,90 Z"
            fill="#FDFCFB"
            opacity="0.7"
          />
        </svg>
      </div>

      <Sticker name="cosmic_21" size={64} className="top-20 right-4 opacity-55" />
      <Sticker name="cosmic_34" size={80} className="bottom-0 left-4 opacity-50" />

      <div className="max-w-6xl mx-auto">
        <div className="grid lg:grid-cols-12 gap-8 items-center">

          {/* Left Column: Description */}
          <div className="lg:col-span-4 space-y-5">
            <Badge className="bg-[#F3E8FF] text-[#7E22CE]">
              The Technology
            </Badge>
            <h2 className="font-outfit text-3xl sm:text-4xl font-extrabold text-slate-900 leading-tight">
              Your movement becomes the controller.
            </h2>
            <p className="text-slate-600 text-sm leading-relaxed">
              No controllers needed. <br />
              SensAI uses the camera to detect specific movements and translate the child&apos;s gestures into responsive interactions.
            </p>
            <div className="pt-2">
              <button className="bg-[#18212F] hover:bg-black text-white px-6 py-3 rounded-full text-xs font-bold flex items-center gap-2 transition-all shadow-sm">
                Explore our technology <ArrowRight size={14} />
              </button>
            </div>
          </div>

          {/* Center Column: Feature Image */}
          <div className="lg:col-span-4 flex justify-center relative z-10">
            <div className="relative w-full max-w-sm hover:scale-[1.01] transition-transform">
              <Image
                src="/Assets/Landing Page/mouvement-features-setup.png"
                alt="Child in front of the screen with pose tracking"
                width={420}
                height={520}
                loading="eager"
                className="w-full h-auto object-contain drop-shadow-xl"
              />
            </div>
          </div>

          {/* Right Column: 4 Feature Cards */}
          <div className="lg:col-span-4 flex flex-col gap-3">
            {features.map((f) => (
              <div
                key={f.label}
                className={`flex items-center gap-4 ${f.bg} rounded-2xl px-4 py-3 shadow-sm hover:shadow-md transition-shadow`}
              >

                <div className="w-12 h-12 shrink-0">
                  <Image
                    src={f.icon}
                    alt={f.label}
                    width={48}
                    height={48}
                    className="w-full h-full object-contain"
                  />
                </div>
                <div>
                  <p className="font-outfit font-extrabold text-sm text-slate-900">{f.label}</p>
                  <p className="text-xs text-slate-500 leading-snug">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>

        </div>
      </div>
    </section>
  );
}

