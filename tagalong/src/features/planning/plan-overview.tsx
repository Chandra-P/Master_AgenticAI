'use client';
import type {Plan,Tab} from '@/services/types';
import {Button} from '@/components/ui/button';
import {PlanningBoard} from './board';
import {useDecisionSnapshot} from './decisions/use-decision-snapshot';

export function PlanOverview({plan,onTab}:{plan:Plan;onTab:(tab:Tab)=>void}){
 const {snapshot,error}=useDecisionSnapshot(plan);
 const remaining=snapshot?.decisions.filter(d=>d.status!=='confirmed')||[];
 return <section className="tab-content journey-overview" aria-label="Plan overview">
  <div className="section-heading"><div><div className="eyebrow">YOUR NEXT GOOD MEMORY</div><h2>The plan at a glance.</h2><p className="muted">Working details, shared needs and the next decisions to make.</p></div></div>
  <div className="journey-actions"><div><h3>What needs your attention?</h3>{snapshot?<p>{remaining.length?`${remaining.length} decisions still need confirmation. Start with ${remaining[0].title.toLowerCase()}.`:snapshot.finalized?'Your reviewed plan is finalized. Verify arrangements before booking.':'Decisions are confirmed. The owner can review and finalize the plan.'}</p>:<p>{error||'Loading current decisions…'}</p>}<Button onClick={()=>onTab('Decisions')}>Review decisions</Button></div><div><h3>Keep the group moving</h3><p>Share planning notes and reference files, discuss needs, or review the itinerary.</p><div className="journey-buttons"><Button variant="outline" onClick={()=>onTab('Documents')}>Notes and files</Button><Button variant="outline" onClick={()=>onTab('Chat')}>Talk with the group</Button><Button variant="outline" onClick={()=>onTab('Itinerary')}>Review itinerary</Button></div></div></div>
  <PlanningBoard plan={plan} onTab={onTab}/>
 </section>;
}
