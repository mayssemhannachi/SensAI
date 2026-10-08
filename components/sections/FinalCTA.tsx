import Link from "next/link";
import Image from "next/image";
import { ArrowDown } from "lucide-react";

export default function FinalCTA() {
  return (
    <>
      {/* SVG Cloud divider — fill exactly matches the section background */}
      <div className="w-full relative z-20 -mb-[1px] pointer-events-none bg-[#FAFAF9]">
        <svg viewBox="0 0 1440 100" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" className="w-full h-[80px] sm:h-[100px] block">
          <path
            d="M0,100 L0,50 C60,20 120,75 200,45 C270,18 330,70 420,42 C500,16 560,68 660,40 C750,14 810,65 910,40 C1000,17 1060,66 1160,42 C1250,18 1320,68 1400,45 L1440,48 L1440,100 Z"
            fill="#070C16"
          />
          <path
            d="M0,100 L0,68 C80,42 150,85 250,60 C340,38 400,78 500,55 C590,34 650,80 760,58 C860,38 920,78 1030,56 C1130,36 1190,76 1300,56 C1380,40 1420,70 1440,62 L1440,100 Z"
            fill="#070C16"
            opacity="0.85"
          />
        </svg>
      </div>

      <section className="relative pb-6 px-6 bg-[#070C16] text-white overflow-hidden">
        
        {/* Twinkling stars */}
        <div className="absolute top-12 left-1/6 text-yellow-300 text-lg opacity-80">✦</div>
        <div className="absolute top-20 right-1/4 text-yellow-200 text-sm opacity-60">★</div>
        <div className="absolute bottom-12 left-1/4 text-blue-300 text-xs opacity-70">✦</div>
        <div className="absolute bottom-8 right-1/6 text-pink-300 text-sm opacity-60">★</div>

        <div className="max-w-4xl mx-auto text-center space-y-6 relative z-10 pt-4 pb-8">
          <h2 className="font-outfit text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
            Prêt à entrer dans l'aventure ?
          </h2>
          <p className="text-slate-300 text-sm sm:text-base max-w-lg mx-auto">
            Découvrez comment SensAI transforme le mouvement en interaction.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-4 relative z-20">
            <Link href="/login" className="bg-[#FF5A78] hover:bg-[#F43F5E] text-white px-7 py-3 rounded-full text-xs sm:text-sm font-bold transition-all shadow-lg hover:shadow-pink-500/20">
              Commencer l'expérience
            </Link>
            <button className="bg-transparent hover:bg-white/10 border border-slate-700 text-slate-200 px-6 py-3 rounded-full text-xs sm:text-sm font-bold flex items-center gap-2 transition-all">
              Découvrir SensAI <ArrowDown size={14} />
            </button>
          </div>
        </div>

        {/* Mascot bottom right */}
        <div className="absolute bottom-0 right-[5%] sm:right-[10%] lg:right-[15%] w-28 sm:w-36 h-auto z-10">
          <Image 
            src="/Assets/Landing Page/sensai-mascot.png" 
            alt="SensAI Mascot" 
            width={150} 
            height={150} 
            className="w-full h-auto object-contain"
          />
        </div>
      </section>
    </>
  );
}
