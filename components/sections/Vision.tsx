import Image from "next/image";
import Badge from "@/components/ui/Badge";
import Sticker from "@/components/ui/Sticker";

export default function Vision() {
  return (
    <section className="pt-24 pb-20 px-6 bg-[#FAFAF9] relative overflow-hidden">
      {/* Cloud SVG divider at top */}
      <div className="absolute top-0 left-0 right-0 w-full overflow-hidden pointer-events-none rotate-180" style={{height: '90px'}}>
        <svg viewBox="0 0 1440 90" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" className="w-full h-full">
          <path
            d="M0,45 C70,5 130,80 220,42 C300,8 350,72 450,40 C530,10 580,75 680,42 C770,12 820,70 930,42 C1020,16 1070,74 1170,44 C1260,16 1320,72 1400,46 L1440,48 L1440,90 L0,90 Z"
            fill="#FFFFFF"
          />
          <path
            d="M0,62 C80,32 150,88 250,58 C340,30 390,82 490,56 C580,32 640,84 750,58 C850,34 910,82 1020,56 C1120,32 1180,84 1290,58 C1370,36 1420,78 1440,65 L1440,90 L0,90 Z"
            fill="#FFFFFF"
            opacity="0.7"
          />
        </svg>
      </div>

      <Sticker name="cosmic_35" size={80} className="top-12 -left-2 md:left-4 opacity-40" />
      <Sticker name="cosmic_11" size={70} className="-bottom-2 left-2 md:left-8 opacity-50" />
      <Sticker name="cosmic_23" size={64} className="bottom-24 right-4 opacity-55" />

      <div className="max-w-6xl mx-auto relative z-10">
        <div className="grid lg:grid-cols-12 gap-8 items-center">
          
          {/* Left Content */}
          <div className="lg:col-span-5 space-y-4">
            <Badge className="bg-[#FEF3C7] text-[#B45309]">
              Notre vision
            </Badge>

            <h2 className="font-outfit text-3xl sm:text-4xl font-extrabold text-slate-900 leading-tight">
              Et si chaque mouvement pouvait raconter une histoire ?
            </h2>

            <div className="space-y-3 text-sm text-slate-600 leading-relaxed">
              <p>
                SensAI est un prototype qui explore une nouvelle manière d'associer rééducation pédiatrique, interaction et intelligence artificielle.
              </p>
              <p>
                Notre vision est de continuer à développer une expérience capable de s'adapter davantage aux besoins de chaque enfant et de fournir aux professionnels des informations toujours plus utiles.
              </p>
            </div>
          </div>

          {/* Center Sticky Quote */}
          <div className="lg:col-span-3 flex justify-center">
            <div className="bg-[#FFFBEB] border border-[#FDE68A] rounded-2xl p-6 shadow-md rotate-[-2deg] hover:rotate-0 transition-transform max-w-[240px]">
              <p className="font-handwriting text-lg text-slate-700 leading-snug">
                "Nous ne remplaçons pas la rééducation."
              </p>
              <p className="font-handwriting text-xl text-purple-700 font-bold mt-2 leading-snug">
                "Nous repensons l'expérience autour d'elle."
              </p>
            </div>
          </div>

          {/* Right Photo */}
          <div className="lg:col-span-4 flex justify-center relative z-10">
            <div className="relative w-full max-w-[340px] hover:scale-[1.01] transition-transform">
              <Image 
                src="/Assets/Landing Page/enjoysection.png" 
                alt="Enfant célébrant ses progrès avec les bras levés" 
                width={380} 
                height={380} 
                className="w-full h-auto object-contain drop-shadow-2xl"
              />
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
