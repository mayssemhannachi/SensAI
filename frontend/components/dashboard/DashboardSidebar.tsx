import Image from "next/image";
import Link from "next/link";
import { Home, Gamepad2, BarChart2, User } from "lucide-react";

export default function DashboardSidebar() {
  return (
    <aside className="w-48 lg:w-52 fixed top-0 left-0 bottom-0 bg-[#FAF9FE] flex flex-col justify-between pt-5 pb-5 border-r border-slate-100/80 z-50 select-none">
      {/* Top: Logo + Navigation */}
      <div>
        {/* Brand Logo */}
        <div className="px-4 mb-5">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-7 h-7 relative flex-shrink-0 group-hover:scale-105 transition-transform">
              <Image 
                src="/Assets/Landing Page/sensai-mascot.png" 
                alt="SensAI Logo" 
                width={28} 
                height={28} 
                className="w-full h-full object-contain"
                priority
              />
            </div>
            <span className="font-outfit text-lg font-black tracking-tight text-[#1E1B4B]">
              Sens<span className="text-[#FF6B8B]">A</span><span className="text-[#7C3AED]">I</span>
            </span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="px-2.5 space-y-1">
          <Link 
            href="/dashboard" 
            className="flex items-center gap-2.5 px-3.5 py-2 rounded-xl bg-[#ECE7FE] text-[#6366F1] font-bold text-xs shadow-sm transition-all"
          >
            <Home size={16} className="text-[#6366F1]" />
            <span>Home</span>
          </Link>
          <Link 
            href="#" 
            className="flex items-center gap-2.5 px-3.5 py-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-white/80 transition-colors font-semibold text-xs"
          >
            <Gamepad2 size={16} className="text-slate-500" />
            <span>My Exercises</span>
          </Link>
          <Link 
            href="#" 
            className="flex items-center gap-2.5 px-3.5 py-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-white/80 transition-colors font-semibold text-xs"
          >
            <BarChart2 size={16} className="text-slate-500" />
            <span>My Progress</span>
          </Link>
          <Link 
            href="#" 
            className="flex items-center gap-2.5 px-3.5 py-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-white/80 transition-colors font-semibold text-xs"
          >
            <User size={16} className="text-slate-500" />
            <span>Profile</span>
          </Link>
        </nav>
      </div>

      {/* Playful Doodles on Sidebar + Bottom Cloud Box */}
      <div className="relative px-3 pointer-events-none">
        {/* Yellow Star Doodle */}
        <div className="absolute -top-16 left-4 text-[#FBBF24]">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
          </svg>
        </div>

        {/* Cyan Squiggle */}
        <div className="absolute -top-16 right-5 text-[#38BDF8]">
          <svg width="18" height="10" viewBox="0 0 30 20" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <path d="M2 14 Q 8 2, 14 10 T 26 6" />
          </svg>
        </div>

        {/* Pink Lightning Doodle */}
        <div className="absolute -top-8 left-7 text-[#F472B6]">
          <svg width="13" height="18" viewBox="0 0 24 32" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M13 2 L3 16 H12 L11 30 L21 16 H12 Z" />
          </svg>
        </div>

        {/* Bottom Motivational Cloud Box */}
        <div className="bg-gradient-to-tr from-[#E8F1FC]/90 via-[#F3F6FD]/90 to-[#FFFFFF]/90 rounded-2xl p-2.5 border border-white/80 shadow-sm relative overflow-hidden text-center">
          {/* Tiny top left star */}
          <div className="absolute top-1.5 left-1.5 text-[#FBBF24]">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
          </div>
          
          <p className="text-[10px] font-bold text-slate-600 leading-tight">
            You're making<br />
            progress<br />
            every single step!
          </p>
          <div className="mt-0.5 text-[#FF6B8B] text-xs font-bold">
            ♡
          </div>
        </div>
      </div>
    </aside>
  );
}
