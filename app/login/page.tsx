import Image from "next/image";
import Link from "next/link";
import Sticker from "@/components/ui/Sticker";
import LoginCard from "@/components/auth/LoginCard";

export default function LoginPage() {
  return (
    <div className="h-screen bg-[#FAF8FD] relative overflow-hidden flex flex-col font-outfit">

      {/* Decorative blobs */}
      <div className="absolute top-[-15%] left-[-10%] w-[45%] h-[55%] rounded-full bg-[#eee5fa] opacity-60 blur-[90px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-5%] w-[40%] h-[50%] rounded-full bg-[#fdebf3] opacity-60 blur-[90px] pointer-events-none" />

      {/* Stickers */}
      <Sticker name="kawaii_10" size={32} className="top-[16%] left-[3%] animate-float-slow opacity-90" />
      <Sticker name="cosmic_23" size={28} className="bottom-[28%] left-[2%] animate-float-gentle opacity-80" />
      <Sticker name="kawaii_5"  size={36} className="bottom-[16%] left-[5%] animate-float-slow opacity-90" />
      <Sticker name="kawaii_12" size={30} className="bottom-[20%] right-[3%] animate-float-gentle opacity-80" />
      <Sticker name="cosmic_9"  size={24} className="top-[28%] right-[44%] animate-float-slow opacity-60" />

      {/* Navbar */}
      <nav className="relative z-20 w-full px-8 sm:px-14 py-3 sm:py-4 flex items-center justify-between flex-shrink-0 bg-transparent">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-9 h-9 sm:w-10 sm:h-10 relative flex-shrink-0 group-hover:scale-105 transition-transform">
            <Image src="/Assets/Landing Page/sensai-mascot.png" alt="SensAI Logo" width={40} height={40} className="w-full h-full object-contain" priority />
          </div>
          <span className="font-outfit text-2xl font-black tracking-tight text-slate-900">
            Sens<span className="text-[#FF6B8B]">A</span><span className="text-[#7C3AED]">I</span>
          </span>
        </Link>

        {/* Right Nav Items matching inspo */}
        <div className="flex items-center gap-6">
          <div className="hidden sm:flex items-center gap-3 text-[13px] font-semibold text-[#7C3AED]">
            <span>Apprendre</span>
            <span className="w-1 h-1 rounded-full bg-[#3B82F6]/40" />
            <span>Explorer</span>
            <span className="w-1 h-1 rounded-full bg-[#EC4899]/40" />
            <span>Grandir</span>
          </div>

          {/* Theme mode button */}
          <button
            type="button"
            className="w-8 h-8 rounded-full bg-white/90 border border-slate-200/60 shadow-xs flex items-center justify-center text-slate-600 hover:text-[#7C3AED] hover:scale-105 transition-all"
            aria-label="Mode thématique"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="5" />
              <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
            </svg>
          </button>
        </div>
      </nav>

      {/* Main Container */}
      <main className="relative z-10 flex-1 flex items-center justify-center px-6 sm:px-12 xl:px-16 py-1 min-h-0">
        <div className="w-full max-w-[1280px] grid lg:grid-cols-12 gap-6 lg:gap-8 items-center my-auto">

          {/* LEFT: Login Card Component (5 cols on lg) */}
          <div className="lg:col-span-5 flex justify-center lg:justify-start w-full">
            <LoginCard />
          </div>

          {/* RIGHT: Illustration (7 cols on lg) */}
          <div className="hidden lg:flex lg:col-span-7 justify-center items-center">
            <Image
              src="/Assets/connexion/image.png"
              alt="Enfant utilisant SensAI"
              width={600}
              height={480}
              className="w-full max-w-[500px] xl:max-w-[540px] h-auto object-contain hover:scale-[1.01] transition-transform duration-300"
              priority
            />
          </div>

        </div>
      </main>

      {/* Seamless Footer with Integrated Wave */}
      <footer className="relative z-20 w-full flex-shrink-0 bg-[#0F172A] mt-6">
        {/* Wave SVG overlapping seamlessly */}
        <div className="w-full pointer-events-none absolute -top-9 sm:-top-11 left-0 right-0 overflow-hidden leading-none z-10">
          <svg viewBox="0 0 1440 70" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" className="w-full h-[40px] sm:h-[48px] block">
            <path d="M0,70 L0,35 C80,10 160,55 280,30 C390,8 460,48 580,26 C700,6 770,46 900,28 C1020,10 1090,48 1210,28 C1320,10 1390,46 1440,32 L1440,70 Z" fill="#0F172A" />
          </svg>
        </div>

        <div className="relative z-20 w-full px-8 sm:px-14 py-3 flex items-center justify-between text-[12px] text-slate-400">
          <div className="mx-auto flex items-center gap-3">
            <span>© 2026 SensAI</span>
            <span>·</span>
            <Link href="/confidentialite" className="hover:text-white transition-colors">Confidentialité</Link>
            <span>·</span>
            <Link href="/mentions-legales" className="hover:text-white transition-colors">Mentions légales</Link>
            <span>·</span>
            <Link href="/contact" className="hover:text-white transition-colors">Contact</Link>
          </div>

          {/* Color indicator dots on right */}
          <div className="hidden sm:flex items-center gap-1.5 absolute right-8 sm:right-14">
            <span className="w-2.5 h-2.5 rounded-full bg-[#38BDF8]" />
            <span className="w-2.5 h-2.5 rounded-full bg-[#3B82F6]" />
            <span className="w-2.5 h-2.5 rounded-full bg-[#EC4899]" />
            <span className="w-2.5 h-2.5 rounded-full bg-[#8B5CF6]" />
          </div>
        </div>
      </footer>
    </div>
  );
}
