import Link from 'next/link';
import {ArrowRight} from 'lucide-react';
import type {Plan} from '@/services/types';
import type {DecisionSnapshot} from '@/services/decisions';
import {homePlanModel} from './home-plan-model';

export function NextStepCard({plan,snapshot,memberId}:{plan:Plan;snapshot:DecisionSnapshot;memberId:string}){
 const model=homePlanModel(plan,snapshot,memberId);
 return <article className="decision-next-card"><span className="coord-status">{model.status}</span><h3>{plan.title}</h3><p>{model.pending.length?model.pending.slice(0,2).join(' · '):'Review the confirmed decisions and plan outline.'}</p><strong>{model.participation}</strong>{model.waitingOn.length>0&&<p>Waiting on {model.waitingOn.join(', ')}</p>}<Link href={model.href}>{model.label}<ArrowRight size={16}/></Link></article>;
}
