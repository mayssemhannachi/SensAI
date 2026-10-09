import Image from "next/image";
import Link from "next/link";
import { Settings, User, Bell } from "lucide-react";

export default function DashboardNav() {
  return (
    <header className="absolute top-0 left-0 right-0 z-50 bg-[#FAF8FD]">
      <div className="max-w-6xl mx-auto px-6 h-20 flex items-center justify-between">
        {/* Logo */}
        <Link href="/dashboard" className="flex items-center gap-2.5 group">
          <div className="w-10 h-10 relative flex-shrink-0 group-hover:scale-105 transition-transform">
            <Image 
              src="/Assets/Landing Page/sensai-mascot.png" 
              alt="SensAI Logo" 
              width={40} 
              height={40} 
              className="w-full h-full object-contain"
              priority
            />
          </div>
          <span className="font-outfit text-2xl font-black tracking-tight text-slate-900">
            Sens<span className="text-[#FF6B8B]">A</span><span className="text-[#7C3AED]">I</span>
          </span>
        </Link>

        {/* Right Actions */}
        <div className="flex items-center gap-4">
          <button className="p-2 text-slate-400 hover:text-slate-600 transition-colors bg-white rounded-full shadow-sm">
            <Bell size={20} />
          </button>
          <button className="p-2 text-slate-400 hover:text-slate-600 transition-colors bg-white rounded-full shadow-sm">
            <Settings size={20} />
          </button>
          <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-[#6366F1] to-[#FF6B8B] flex items-center justify-center text-white font-bold shadow-sm">
            L
          </div>
        </div>
      </div>
    </header>
  );
}
