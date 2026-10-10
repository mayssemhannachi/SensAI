import Image from "next/image";
import Badge from "@/components/ui/Badge";
import Sticker from "@/components/ui/Sticker";

const reasons = [
  {
    icon: "/Assets/Landing Page/pourquoi/Ludique.png",
    title: "Ludique",
    desc: "Faire de l'interaction un élément central de l'expérience.",
  },
  {
    icon: "/Assets/Landing Page/pourquoi/Adapte.png",
    title: "Adapté",
    desc: "Concevoir l'expérience autour des besoins spécifiques de l'enfant.",
  },
  {
    icon: "/Assets/Landing Page/pourquoi/accessible.png",
    title: "Accessible",
    desc: "Utiliser une caméra plutôt qu'un matériel spécialisé supplémentaire.",
  },
  {
    icon: "/Assets/Landing Page/pourquoi/intelligent.png",
    title: "Intelligent",
    desc: "Exploiter la vision par ordinateur pour rendre l'interaction plus naturelle.",
  },
  {
    icon: "/Assets/Landing Page/pourquoi/cognitive.png",
    title: "Stimulation cognitive",
    desc: "Associer le mouvement à l'attention, la mémoire, la prise de décision et le repérage spatial.",
  },
  {
    icon: "/Assets/Landing Page/pourquoi/social.png",
    title: "Jeu partagé",
    desc: "Placer le lien social au cœur du jeu, avec des expériences à partager en duo, en famille ou entre pairs.",
  },
];

export default function WhySensAI() {
  return (
    <section className="pt-24 pb-20 px-6 bg-[#FEFAF6] relative overflow-hidden">
      {/* Cloud SVG divider at top */}
      <div className="absolute top-0 left-0 right-0 w-full overflow-hidden pointer-events-none rotate-180" style={{height: '90px'}}>
        <svg viewBox="0 0 1440 90" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" className="w-full h-full">
          <path
            d="M0,45 C70,5 130,80 220,42 C300,8 350,72 450,40 C530,10 580,75 680,42 C770,12 820,70 930,42 C1020,16 1070,74 1170,44 C1260,16 1320,72 1400,46 L1440,48 L1440,90 L0,90 Z"
            fill="#F8FAFC"
          />
          <path
            d="M0,62 C80,32 150,88 250,58 C340,30 390,82 490,56 C580,32 640,84 750,58 C850,34 910,82 1020,56 C1120,32 1180,84 1290,58 C1370,36 1420,78 1440,65 L1440,90 L0,90 Z"
            fill="#F8FAFC"
            opacity="0.7"
          />
        </svg>
      </div>

      <Sticker name="kawaii_8" size={80} className="top-20 left-4 opacity-55" />
      <Sticker name="cosmic_50" size={72} className="bottom-6 right-4 opacity-50" />
      <Sticker name="kawaii_9" size={48} className="top-1/2 right-6 opacity-40" />
      <div className="max-w-6xl mx-auto space-y-10">
        
        {/* Tag */}
        <div className="text-center">
          <Badge className="bg-[#FEF3C7] text-[#B45309]">
            Pourquoi SensAI ?
          </Badge>
        </div>

        {/* 6 Feature Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 relative z-10 pt-4">
          {reasons.map((r) => (
            <div key={r.title} className="flex flex-col items-center text-center group">
              <div className="w-40 h-24 sm:w-48 sm:h-28 mb-4 flex items-center justify-center hover:scale-105 transition-transform duration-300">
                <Image 
                  src={r.icon} 
                  alt={r.title} 
                  width={200} 
                  height={120} 
                  className="w-full h-full object-contain drop-shadow-sm"
                />
              </div>
              <h3 className="font-outfit font-extrabold text-slate-900 text-[15px] mb-2">{r.title}</h3>
              <p className="text-[12px] leading-relaxed text-slate-500 max-w-[220px] mx-auto">{r.desc}</p>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
