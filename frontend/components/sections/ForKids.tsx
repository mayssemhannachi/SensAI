import Image from "next/image";
import Badge from "@/components/ui/Badge";
import Sticker from "@/components/ui/Sticker";

const objectives = [
  {
    icon: "/Assets/Landing Page/kids/explorer.png",
    label: "Explore",
    desc: "Discover new playful environments.",
  },
  {
    icon: "/Assets/Landing Page/kids/interagir.png",
    label: "Interact",
    desc: "Use movement directly to control the experience.",
  },
  {
    icon: "/Assets/Landing Page/kids/progresser.png",
    label: "Progress",
    desc: "Complete challenges and build confidence.",
  },
];

export default function ForKids() {
  return (
    <section id="enfants" className="pt-24 pb-20 px-6 bg-gradient-to-b from-[#FAFCFF] to-white relative overflow-hidden">
      {/* Cloud SVG divider at top */}
      <div className="absolute top-0 left-0 right-0 w-full overflow-hidden pointer-events-none rotate-180" style={{height: '90px'}}>
        <svg viewBox="0 0 1440 90" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" className="w-full h-full">
          <path
            d="M0,45 C70,5 130,80 220,42 C300,8 350,72 450,40 C530,10 580,75 680,42 C770,12 820,70 930,42 C1020,16 1070,74 1170,44 C1260,16 1320,72 1400,46 L1440,48 L1440,90 L0,90 Z"
            fill="#FAF5FF"
          />
          <path
            d="M0,62 C80,32 150,88 250,58 C340,30 390,82 490,56 C580,32 640,84 750,58 C850,34 910,82 1020,56 C1120,32 1180,84 1290,58 C1370,36 1420,78 1440,65 L1440,90 L0,90 Z"
            fill="#FAF5FF"
            opacity="0.7"
          />
        </svg>
      </div>

      <Sticker name="kawaii_10" size={80} className="top-24 right-10 opacity-70" />
      <Sticker name="cosmic_35" size={112} className="bottom-10 right-5 opacity-65" />
      
      <div className="max-w-6xl mx-auto relative z-10">
        <div className="grid lg:grid-cols-12 gap-10 items-center">
          
          {/* Left Content */}
          <div className="lg:col-span-6 space-y-8">
            <div className="space-y-6">
              <Badge className="bg-[#DCFCE7] text-[#15803D]">
                For Kids
              </Badge>

              <h2 className="font-outfit text-3xl sm:text-4xl font-extrabold text-slate-900 leading-tight">
                An experience built around exploration and movement.
              </h2>

              <div className="space-y-3 text-sm text-slate-600 leading-relaxed max-w-lg">
                <p>SensAI doesn&apos;t start with spreadsheets or charts.</p>
                <p className="font-semibold text-slate-800">It starts with an adventure.</p>
                <p>
                  A colorful interface, intuitive interactions, and personalized goals that encourage children to explore, move, and actively engage.
                </p>
              </div>
              <div className="max-w-lg rounded-2xl border border-purple-100 bg-white/80 p-5">
                <h3 className="font-outfit font-extrabold text-slate-900">For children facing neuromotor challenges</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">
                  Cerebral palsy, developmental coordination disorder (DCD), and acquired brain injuries are among the addressed conditions. Activity selection and parameter tuning should always be supervised by the child&apos;s healthcare professional.
                </p>
              </div>
            </div>

            {/* Individual Cards Grid */}
            <div className="grid grid-cols-3 gap-6 pt-2">
              {objectives.map((obj) => (
                <div key={obj.label} className="flex flex-col items-center text-center group">
                  <div className="w-20 h-20 sm:w-24 sm:h-24 mb-4 rounded-full bg-white shadow-sm border border-slate-100 flex items-center justify-center p-4 hover:shadow-md hover:scale-105 transition-all duration-300">
                    <Image 
                      src={obj.icon} 
                      alt={obj.label} 
                      width={64} 
                      height={64} 
                      className="w-full h-full object-contain drop-shadow-sm"
                    />
                  </div>
                  <h3 className="font-outfit font-bold text-slate-900 text-sm mb-1">{obj.label}</h3>
                  <p className="text-[11px] leading-snug text-slate-500">{obj.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Right Visual */}
          <div className="lg:col-span-6 flex justify-center relative z-10">
            <div className="relative w-full max-w-lg hover:scale-[1.01] transition-transform">
              <Image 
                src="/Assets/Landing Page/kids-illustrationpic.png" 
                alt="Magical adventure world for children" 
                width={600} 
                height={450} 
                loading="eager"
                className="w-full h-auto object-contain drop-shadow-2xl"
              />
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
