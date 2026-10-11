import Image from "next/image";
import { ArrowRight } from "lucide-react";
import Badge from "@/components/ui/Badge";
import Sticker from "@/components/ui/Sticker";

export default function ForTherapists() {
  return (
    <section id="therapeutes" className="pt-24 pb-20 px-6 bg-[#F8FAFC] relative overflow-hidden">
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

      <Sticker name="kawaii_10" size={56} className="top-20 left-4 opacity-50" />
      <Sticker name="cosmic_27" size={80} className="bottom-8 right-4 opacity-55" />
      <Sticker name="kawaii_12" size={48} className="top-1/3 right-3 opacity-40" />
      <div className="max-w-6xl mx-auto space-y-12">
        
        {/* Top Row: Information & Dashboard Mockup */}
        <div className="grid lg:grid-cols-12 gap-10 items-center">
          
          {/* Left Info */}
          <div className="lg:col-span-5 space-y-5">
            <Badge className="bg-[#F3E8FF] text-[#7E22CE]">
              For Therapists
            </Badge>

            <h2 className="font-outfit text-3xl sm:text-4xl font-extrabold text-slate-900 leading-tight">
              A new way to track and guide sessions
            </h2>

            <p className="text-slate-600 text-sm leading-relaxed">
              SensAI also provides a dedicated space for clinicians. Therapists can review detailed session metrics and observe each child&apos;s performance trajectory over time.
            </p>

            <div>
              <button className="bg-[#18212F] hover:bg-black text-white px-6 py-3 rounded-full text-xs font-bold flex items-center gap-2 transition-all shadow-sm">
                Explore the therapist space <ArrowRight size={14} />
              </button>
            </div>
          </div>

          {/* Right Mockup */}
          <div className="lg:col-span-7 flex justify-center relative z-10">
            <div className="relative w-full hover:scale-[1.01] transition-transform">
              <Image 
                src="/Assets/Landing Page/Therapy-Dashboard.png" 
                alt="SensAI Therapist Dashboard" 
                width={750} 
                height={500} 
                className="w-full h-auto object-contain drop-shadow-2xl"
              />
            </div>
          </div>

        </div>

        {/* Bottom Row: 4 Feature Cards */}
        <div className="pt-10">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 max-w-6xl mx-auto">
            {/* Feature 1 */}
            <div className="flex items-center gap-3 bg-white rounded-2xl p-4 shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
              <div className="w-10 h-10 shrink-0">
                <Image src="/Assets/Landing Page/therapist/performance.png" alt="Performance Tracking" width={40} height={40} className="w-full h-full object-contain" />
              </div>
              <div>
                <h4 className="font-outfit font-extrabold text-sm text-slate-900">Performance Tracking</h4>
                <p className="text-[11px] text-slate-500 leading-snug">Visualize activity outcomes</p>
              </div>
            </div>
            
            {/* Feature 2 */}
            <div className="flex items-center gap-3 bg-white rounded-2xl p-4 shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
              <div className="w-10 h-10 shrink-0">
                <Image src="/Assets/Landing Page/therapist/Historique.png" alt="Session History" width={40} height={40} className="w-full h-full object-contain" />
              </div>
              <div>
                <h4 className="font-outfit font-extrabold text-sm text-slate-900">Session History</h4>
                <p className="text-[11px] text-slate-500 leading-snug">Review past sessions and trends</p>
              </div>
            </div>

            {/* Feature 3 */}
            <div className="flex items-center gap-3 bg-white rounded-2xl p-4 shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
              <div className="w-10 h-10 shrink-0">
                <Image src="/Assets/Landing Page/therapist/suivi.png" alt="Interaction Metrics" width={40} height={40} className="w-full h-full object-contain" />
              </div>
              <div>
                <h4 className="font-outfit font-extrabold text-sm text-slate-900">Interaction Metrics</h4>
                <p className="text-[11px] text-slate-500 leading-snug">Monitor customized clinical indicators</p>
              </div>
            </div>

            {/* Feature 4 */}
            <div className="flex items-center gap-3 bg-white rounded-2xl p-4 shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
              <div className="w-10 h-10 shrink-0">
                <Image src="/Assets/Landing Page/therapist/profil.png" alt="Individual Profiles" width={40} height={40} className="w-full h-full object-contain" />
              </div>
              <div>
                <h4 className="font-outfit font-extrabold text-sm text-slate-900">Individual Profiles</h4>
                <p className="text-[11px] text-slate-500 leading-snug">Access personalized data for each child</p>
              </div>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}
