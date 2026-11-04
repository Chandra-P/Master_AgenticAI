import type {Metadata} from 'next';
import './globals.css';
import {PlanningProvider} from '@/features/planning/store';
import {Shell} from '@/components/shell';
export const metadata:Metadata={title:'Tagalong — Good plans. Great company.',description:'Less back-and-forth. More being there, together. An interactive group planning demo.'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body><PlanningProvider><Shell>{children}</Shell></PlanningProvider></body></html>;}
