import Image from "next/image";
import Link from "next/link";
import { ArrowRight, ArrowDown } from "lucide-react";
import Sticker from "@/components/ui/Sticker";

export default function Hero() {
  return (
    <section id="accueil" className="relative min-h-screen flex flex-col justify-center pt-28 pb-28 px-6 overflow-hidden bg-gradient-to-b from-[#FFFDF9] via-[#FAF7FF] to-[#F3EEFF]">
      {/* Stickers */}
      <Sticker name="cosmic_24" size={64} className="top-28 right-2 sm:right-6 opacity-70 z-0 drop-shadow-md" />
      <Sticker name="kawaii_7" size={80} className="bottom-24 right-2 sm:right-6 opacity-60 z-0 drop-shadow-md" />
      <Sticker name="cosmic_19" size={56} className="bottom-20 left-2 sm:left-6 opacity-55 hover:rotate-12 transition-transform z-0 drop-shadow-sm" />

      {/* Cloud SVG divider */}
      <div className="absolute bottom-0 left-0 right-0 w-full overflow-hidden pointer-events-none" style={{height: '100px'}}>
        <svg
          viewBox="0 0 1440 100"
          xmlns="http://www.w3.org/2000/svg"
          preserveAspectRatio="none"
          className="w-full h-full"
        >
          <path
            d="M0,55 C60,10 110,85 200,48 C280,14 330,78 430,45 C510,16 560,80 660,46 C750,14 800,76 910,48 C1000,22 1050,80 1150,50 C1240,22 1300,80 1380,52 L1440,55 L1440,100 L0,100 Z"
            fill="#EEF2FF"
          />
          <path
            d="M0,70 C80,40 140,95 240,65 C330,38 380,88 480,62 C570,38 630,90 740,65 C840,40 900,90 1010,64 C1110,38 1170,90 1280,64 C1360,42 1410,85 1440,72 L1440,100 L0,100 Z"
            fill="#EEF2FF"
            opacity="0.6"
          />
        </svg>
      </div>

      <div className="max-w-6xl mx-auto grid lg:grid-cols-12 gap-10 items-center w-full">
        
        {/* Left Text Column */}
        <div className="lg:col-span-6 space-y-6 relative z-10">
          <h1 className="font-outfit text-4xl sm:text-5xl lg:text-[54px] font-extrabold text-slate-900 leading-[1.12] tracking-tight">
            Rehabilitation becomes <br />
            <span className="relative inline-block mt-1">
              an{" "}
              <span className="inline-flex font-black">
                <span className="text-[#EC4899]">a</span>
                <span className="text-[#8B5CF6]">d</span>
                <span className="text-[#3B82F6]">v</span>
                <span className="text-[#06B6D4]">e</span>
                <span className="text-[#10B981]">n</span>
                <span className="text-[#F59E0B]">t</span>
                <span className="text-[#F97316]">u</span>
                <span className="text-[#8B5CF6]">r</span>
                <span className="text-[#EC4899]">e</span>
                <span className="text-[#EC4899]">.</span>
              </span>
            </span>
          </h1>

          <div className="space-y-4 text-base sm:text-lg text-slate-600 leading-relaxed max-w-xl">
            <p>
              SensAI explores how to enrich motor rehabilitation through cognitive stimulation and shared play for children with neuromotor challenges.
            </p>
            <p className="text-sm sm:text-base text-slate-500">
              Children interact naturally with activities using their camera, while SensAI transforms their movements into playful interactions and actionable session data.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-4 pt-2">
            <Link 
              href="#enfants" 
              className="bg-[#18212F] hover:bg-black text-white px-7 py-3.5 rounded-full text-sm font-bold flex items-center gap-2.5 transition-all shadow-md hover:translate-y-[-1px]"
            >
              Start the adventure <ArrowRight size={16} />
            </Link>
            <Link 
              href="#comment-ca-marche" 
              className="bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 px-6 py-3.5 rounded-full text-sm font-bold flex items-center gap-2 transition-all shadow-xs"
            >
              Discover SensAI <ArrowDown size={15} className="text-slate-400" />
            </Link>
          </div>
        </div>

        {/* Right Visual */}
        <div className="lg:col-span-6 relative flex justify-center">
          <div className="relative w-full max-w-xl hover:scale-[1.01] transition-transform duration-300">
            <Image 
              src="/Assets/Landing Page/hero-composite.png" 
              alt="Child performing rehabilitation exercises with SensAI" 
              width={700} 
              height={550} 
              className="w-full h-auto object-contain drop-shadow-xl"
              priority
            />
          </div>
        </div>
      </div>
    </section>
  );
}
