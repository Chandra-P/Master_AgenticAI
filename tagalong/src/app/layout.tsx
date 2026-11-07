import type {Metadata} from 'next';
import './globals.css';
import './coordination.css';
import '@/features/planning/decisions/home.css';
import '@/features/planning/decisions/decisions.css';
import '@/features/planning/place-cards.css';
import '@/features/planning/typing-suggestions.css';
import '@/features/planning/group-fit.css';
import './design-system.css';
import './visual-refresh.css';
import {PlanningProvider} from '@/features/planning/store';
import {Shell} from '@/components/shell';
export const metadata:Metadata={title:'Tagalong — Good company starts here.',description:'Describe an outing or trip. Tagalong helps your group move from idea to decision to itinerary to experience.'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body><PlanningProvider><Shell>{children}</Shell></PlanningProvider></body></html>;}
