import Link from 'next/link';
import Image from 'next/image';
import {safeActivityImage} from '@/services/place-links';
import {ArrowRight,Check} from 'lucide-react';
import type {Plan} from '@/services/types';
import type {DecisionSnapshot} from '@/services/decisions';
import {ConsensusMeter} from './consensus-meter';
import {homePlanModel} from './home-plan-model';

export function DecisionPlanCard({plan,snapshot,memberId,error}:{plan:Plan;snapshot?:DecisionSnapshot;memberId:string;error?:string}){
 const model=snapshot?homePlanModel(plan,snapshot,memberId):null;
 return <article className="decision-home-plan"><div className="plan-cover"><Image src={safeActivityImage(plan.image)||'/images/coast.jpg'} alt="" fill unoptimized referrerPolicy="no-referrer" sizes="(max-width:700px) 100vw, 33vw"/><span className="plan-cover-kind">{plan.kind==='trip'?'Trip':'Outing'}</span></div><div className="plan-card-heading"><h3><Link aria-label={'Open '+plan.title} href={'/plans/'+encodeURIComponent(plan.id)}>{plan.title}</Link></h3><p>{plan.members.length} participants</p></div>
 {snapshot&&model?<><ConsensusMeter score={snapshot.score} finalized={snapshot.finalized}/><div className="decision-home-counts">{[{title:'completed',items:model.completed},{title:'remaining',items:model.pending}].map(({title,items})=><div key={title}><strong>{items.length} {title}</strong><ul>{items.slice(0,2).map(item=><li key={item}>{title==='completed'&&<Check size={14} aria-hidden="true"/>}{item}</li>)}</ul>{items.length>2&&<small>+{items.length-2} more</small>}</div>)}</div><p>{model.waitingOn.length?'Waiting on '+model.waitingOn.join(', '):'No outstanding responses for the next step'}</p><Link className="btn btn-outline" href={model.href}>{model.label}<ArrowRight size={16}/></Link><small>{model.activity}</small></>:<><p role="status">{error||'Loading decision progress…'}</p><Link className="btn btn-outline" href={'/plans/'+encodeURIComponent(plan.id)+'?tab=Decisions'}>Review decisions <ArrowRight size={16}/></Link></>}
 </article>;
}
