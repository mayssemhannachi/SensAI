import type { Metadata } from 'next';
import { Outfit, Nunito, Caveat } from 'next/font/google';
import './globals.css';

const outfit = Outfit({ subsets: ['latin'], variable: '--font-outfit' });
const nunito = Nunito({ subsets: ['latin'], variable: '--font-nunito' });
const caveat = Caveat({ subsets: ['latin'], variable: '--font-caveat' });

export const metadata: Metadata = {
  title: 'SensAI — La rééducation devient une aventure',
  description: 'SensAI explore comment enrichir la rééducation motrice par la stimulation cognitive et le jeu partagé pour les enfants présentant des troubles neuromoteurs.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" className={`${outfit.variable} ${nunito.variable} ${caveat.variable} scroll-smooth`}>
      <body className="font-nunito bg-[#FCFCFD] text-slate-800 antialiased selection:bg-purple-200 selection:text-purple-900">
        {children}
      </body>
    </html>
  );
}
