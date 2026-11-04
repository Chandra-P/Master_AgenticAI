import {Suspense} from 'react';
import {Workspace} from '@/features/planning/workspace';
export default async function PlanPage({params}:{params:Promise<{id:string}>}){const {id}=await params;return <Suspense fallback={<p className="page-content">Getting the group together…</p>}><Workspace id={id}/></Suspense>;}
