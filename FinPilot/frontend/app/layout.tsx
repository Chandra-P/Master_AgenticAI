import type { Metadata } from 'next';
import './globals.css';
import './modern.css';
export const metadata:Metadata={title:'FinPilot — Your financial intelligence team',description:'A clearer financial picture. Evidence-backed decisions, deterministic calculations, and goals that stay in view.'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>;}
