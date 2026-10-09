import Image from "next/image";
import Link from "next/link";

export default function Navbar() {
  return (
    <header className="absolute top-0 left-0 right-0 z-50 bg-transparent transition-all">
      <div className="max-w-6xl mx-auto px-6 h-20 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
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

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-7 text-sm font-semibold text-slate-600">
          <Link href="#accueil" className="text-slate-900 border-b-2 border-slate-900 pb-0.5 font-bold">
            Accueil
          </Link>
          <Link href="#enfants" className="hover:text-purple-600 transition-colors">
            Pour les enfants
          </Link>
          <Link href="#therapeutes" className="hover:text-purple-600 transition-colors">
            Pour les thérapeutes
          </Link>
          <Link href="#comment-ca-marche" className="hover:text-purple-600 transition-colors">
            Comment ça marche ?
          </Link>
          <Link href="#a-propos" className="hover:text-purple-600 transition-colors">
            À propos
          </Link>
        </nav>

        {/* Sign In Button */}
        <div className="flex items-center">
          <Link href="/login" className="bg-[#18212F] hover:bg-slate-900 text-white px-5 py-2.5 rounded-full text-xs font-bold tracking-wide transition-all shadow-xs hover:shadow-md">
            Se connecter
          </Link>
        </div>
      </div>
    </header>
  );
}
