import Image from "next/image";
import Link from "next/link";
import { Heart } from "lucide-react";

export default function Footer() {
  return (
    <footer className="relative bg-[#070C16] text-slate-400 pt-2 pb-8 px-6 overflow-hidden">
      {/* Footer content */}
      <div className="relative z-10 max-w-6xl mx-auto grid grid-cols-2 md:grid-cols-5 gap-6 mb-8 text-xs">
        
        {/* Brand & Logo */}
        <div className="col-span-2 space-y-3">
          <div className="w-32 h-auto">
            <Image 
              src="/Assets/Landing Page/logo-white.png" 
              alt="SensAI Logo White" 
              width={128} 
              height={36} 
              className="w-auto h-7 object-contain"
            />
          </div>
          <p className="text-slate-400 text-xs max-w-xs leading-relaxed">
            Rehabilitation becomes an adventure.
          </p>
        </div>

        {/* Col 1: Product */}
        <div className="space-y-3">
          <h5 className="font-bold text-slate-200 uppercase tracking-wider text-[11px]">Product</h5>
          <ul className="space-y-2">
            <li><Link href="#accueil" className="hover:text-white transition-colors">Home</Link></li>
            <li><Link href="#enfants" className="hover:text-white transition-colors">For Kids</Link></li>
            <li><Link href="#therapeutes" className="hover:text-white transition-colors">For Therapists</Link></li>
            <li><Link href="#comment-ca-marche" className="hover:text-white transition-colors">How It Works</Link></li>
          </ul>
        </div>

        {/* Col 2: Project */}
        <div className="space-y-3">
          <h5 className="font-bold text-slate-200 uppercase tracking-wider text-[11px]">Project</h5>
          <ul className="space-y-2">
            <li><Link href="#" className="hover:text-white transition-colors">Our Vision</Link></li>
            <li><Link href="#" className="hover:text-white transition-colors">Technology</Link></li>
            <li><Link href="#" className="hover:text-white transition-colors">Team</Link></li>
            <li><Link href="#" className="hover:text-white transition-colors">Contact</Link></li>
          </ul>
        </div>

        {/* Col 3: Follow us */}
        <div className="space-y-3">
          <h5 className="font-bold text-slate-200 uppercase tracking-wider text-[11px]">Follow Us</h5>
          <div className="pt-1">
            <Image 
              src="/Assets/Landing Page/footer-socials.png" 
              alt="Social Media" 
              width={100} 
              height={30} 
              className="w-auto h-6 object-contain cursor-pointer opacity-80 hover:opacity-100 transition-opacity"
            />
          </div>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="relative z-10 max-w-6xl mx-auto pt-4 border-t border-slate-700/40 flex flex-col sm:flex-row items-center justify-between gap-3 text-[11px] text-slate-500">
        <p>© 2026 SensAI. All rights reserved.</p>
        <p className="flex items-center gap-1">
          Made with <Heart size={12} className="text-[#FF5A78] fill-[#FF5A78]" /> for a more inclusive future
        </p>
      </div>
    </footer>
  );
}

