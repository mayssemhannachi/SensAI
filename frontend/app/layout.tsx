import type { Metadata } from 'next';
import { Outfit, Nunito, Caveat } from 'next/font/google';
import './globals.css';

const outfit = Outfit({ subsets: ['latin'], variable: '--font-outfit' });
const nunito = Nunito({ subsets: ['latin'], variable: '--font-nunito' });
const caveat = Caveat({ subsets: ['latin'], variable: '--font-caveat' });

export const metadata: Metadata = {
  title: 'SensAI — Rehabilitation becomes an adventure',
  description: 'SensAI explores how to enrich motor rehabilitation through cognitive stimulation and shared play for children with neuromotor challenges.',
  icons: {
    icon: '/assets_flat/sensai-mascot-nobg.png',
    apple: '/assets_flat/sensai-mascot-nobg.png',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${outfit.variable} ${nunito.variable} ${caveat.variable} scroll-smooth`}>
      <body className="font-nunito bg-[#FCFCFD] text-slate-800 antialiased selection:bg-purple-200 selection:text-purple-900">
        {children}
      </body>
    </html>
  );
}
