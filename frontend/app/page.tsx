import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import Hero from "@/components/sections/Hero";
import Problem from "@/components/sections/Problem";
import HowItWorks from "@/components/sections/HowItWorks";
import Technology from "@/components/sections/Technology";
import ForKids from "@/components/sections/ForKids";
import ForTherapists from "@/components/sections/ForTherapists";
import WhySensAI from "@/components/sections/WhySensAI";
import HomeOrClinic from "@/components/sections/HomeOrClinic";
import Vision from "@/components/sections/Vision";
import FinalCTA from "@/components/sections/FinalCTA";

export default function Home() {
  return (
    <main className="min-h-screen bg-[#FDFCFB] text-slate-800 antialiased overflow-x-hidden selection:bg-purple-200 selection:text-purple-900">
      <Navbar />
      <Hero />
      <Problem />
      <HowItWorks />
      <Technology />
      <ForKids />
      <ForTherapists />
      <WhySensAI />
      <HomeOrClinic />
      <Vision />
      <FinalCTA />
      <Footer />
    </main>
  );
}
