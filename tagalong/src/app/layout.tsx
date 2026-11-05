import type {Metadata} from 'next';
import './globals.css';
import './coordination.css';
import {PlanningProvider} from '@/features/planning/store';
import {Shell} from '@/components/shell';
export const metadata:Metadata={title:'Tagalong — Good company starts here.',description:'Describe an outing or trip. Tagalong helps your group move from idea to decision to itinerary to experience.'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body><PlanningProvider><Shell>{children}</Shell></PlanningProvider></body></html>;}
