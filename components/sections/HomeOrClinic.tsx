import Image from "next/image";
import Badge from "@/components/ui/Badge";
import Sticker from "@/components/ui/Sticker";

export default function HomeOrClinic() {
  return (
    <section className="pt-24 pb-20 px-6 bg-white relative overflow-hidden">
      {/* Cloud SVG divider at top */}
      <div className="absolute top-0 left-0 right-0 w-full overflow-hidden pointer-events-none rotate-180" style={{height: '90px'}}>
        <svg viewBox="0 0 1440 90" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" className="w-full h-full">
          <path
            d="M0,45 C70,5 130,80 220,42 C300,8 350,72 450,40 C530,10 580,75 680,42 C770,12 820,70 930,42 C1020,16 1070,74 1170,44 C1260,16 1320,72 1400,46 L1440,48 L1440,90 L0,90 Z"
            fill="#FEFAF6"
          />
          <path
            d="M0,62 C80,32 150,88 250,58 C340,30 390,82 490,56 C580,32 640,84 750,58 C850,34 910,82 1020,56 C1120,32 1180,84 1290,58 C1370,36 1420,78 1440,65 L1440,90 L0,90 Z"
            fill="#FEFAF6"
            opacity="0.7"
          />
        </svg>
      </div>

      <Sticker name="kawaii_12" size={64} className="bottom-12 left-8 opacity-50" />
      <Sticker name="cosmic_28" size={72} className="top-16 right-6 opacity-45" />

      <div className="max-w-6xl mx-auto relative z-10">
        <div className="grid lg:grid-cols-12 gap-10 items-center">
          
          {/* Left */}
          <div className="lg:col-span-6 space-y-4">
            <Badge className="bg-[#E0F2FE] text-[#0369A1]">
              À la maison / En cabinet
            </Badge>

            <h2 className="font-outfit text-3xl sm:text-4xl font-extrabold text-slate-900 leading-tight">
              Une technologie qui s'intègre dans le quotidien
            </h2>

            <div className="space-y-3 text-sm text-slate-600 leading-relaxed">
              <p>
                SensAI est pensé pour fonctionner avec un équipement courant : un écran et une caméra.
              </p>
              <p>
                L'objectif est de rendre l'expérience simple à utiliser, aussi bien dans un environnement professionnel que dans un contexte à domicile, selon les besoins et l'encadrement approprié.
              </p>
            </div>
          </div>

          {/* Right */}
          <div className="lg:col-span-6 flex justify-center">
            <div className="w-full max-w-lg hover:scale-[1.01] transition-transform">
              <Image 
                src="/Assets/Landing Page/hardware-setup.png" 
                alt="Installation matériel : Caméra + Écran = SensAI" 
                width={600} 
                height={350} 
                className="w-full h-auto object-contain mx-auto"
              />
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
