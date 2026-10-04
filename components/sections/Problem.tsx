import Image from "next/image";
import Badge from "@/components/ui/Badge";
import Sticker from "@/components/ui/Sticker";

export default function Problem() {
  return (
    <section className="pt-0 pb-20 px-6 bg-[#EEF2FF] relative overflow-hidden">
      <Sticker name="kawaii_13" size={56} className="bottom-6 left-8 opacity-45" />
      <Sticker name="cosmic_28" size={56} className="bottom-8 right-8 opacity-50" />
      <div className="max-w-6xl mx-auto relative z-10">
        <div className="grid lg:grid-cols-12 gap-12 items-center">

          {/* Left: title + description */}
          <div className="lg:col-span-5 space-y-5">
            <Badge className="bg-[#DBEAFE] text-[#1D4ED8]">
              Le problème
            </Badge>
            <h2 className="font-outfit text-3xl sm:text-4xl font-extrabold text-slate-900 leading-tight">
              Et si la rééducation ressemblait moins à un exercice ?
            </h2>
            <p className="text-slate-600 text-sm sm:text-base leading-relaxed">
              Les séances de rééducation peuvent parfois devenir répétitives pour les enfants.
            </p>
            <p className="text-slate-700 text-sm sm:text-base leading-relaxed">
              SensAI cherche à créer une expérience{" "}
              <span className="font-bold text-slate-900 underline decoration-purple-400 decoration-2 underline-offset-4">
                différente
              </span>{" "}
              — plus engageante, plus naturelle, et plus observable.
            </p>
          </div>

          {/* Right: 3 cards with large floating illustrations */}
          <div className="lg:col-span-7 grid sm:grid-cols-3 gap-5">

            {/* Card 1: Plus engageante */}
            <div className="relative flex flex-col items-center group">
              <div className="relative z-10 w-24 h-24 mb-[-24px]">
                <Image
                  src="/Assets/Landing Page/icon-child bg.png"
                  alt="Plus engageante"
                  width={96}
                  height={96}
                  className="w-full h-full object-contain drop-shadow-lg group-hover:scale-110 transition-transform duration-300"
                />
              </div>
              <div className="w-full bg-[#FFF4EE] border border-[#FFE2D2] rounded-[24px] pt-10 pb-6 px-5 text-center shadow-sm group-hover:shadow-md transition-shadow duration-300">
                <h3 className="font-outfit font-extrabold text-base text-slate-900 mb-2">Plus engageante</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Transformer les exercices en interactions ludiques.
                </p>
              </div>
            </div>

            {/* Card 2: Plus naturelle */}
            <div className="relative flex flex-col items-center group sm:mt-8">
              <div className="relative z-10 w-24 h-24 mb-[-24px]">
                <Image
                  src="/Assets/Landing Page/icon-hand bg.png"
                  alt="Plus naturelle"
                  width={96}
                  height={96}
                  className="w-full h-full object-contain drop-shadow-lg group-hover:scale-110 transition-transform duration-300"
                />
              </div>
              <div className="w-full bg-[#E9FAF8] border border-[#CEF5F0] rounded-[24px] pt-10 pb-6 px-5 text-center shadow-sm group-hover:shadow-md transition-shadow duration-300">
                <h3 className="font-outfit font-extrabold text-base text-slate-900 mb-2">Plus naturelle</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Utiliser les mouvements comme moyen d'interaction.
                </p>
              </div>
            </div>

            {/* Card 3: Plus observable */}
            <div className="relative flex flex-col items-center group">
              <div className="relative z-10 w-24 h-24 mb-[-24px]">
                <Image
                  src="/Assets/Landing Page/icon-trend bg.png"
                  alt="Plus observable"
                  width={96}
                  height={96}
                  className="w-full h-full object-contain drop-shadow-lg group-hover:scale-110 transition-transform duration-300"
                />
              </div>
              <div className="w-full bg-[#F4F1FD] border border-[#E7E0FB] rounded-[24px] pt-10 pb-6 px-5 text-center shadow-sm group-hover:shadow-md transition-shadow duration-300">
                <h3 className="font-outfit font-extrabold text-base text-slate-900 mb-2">Plus observable</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Données de session pour suivre les performances.
                </p>
              </div>
            </div>

          </div>
        </div>


      </div>
    </section>
  );
}
