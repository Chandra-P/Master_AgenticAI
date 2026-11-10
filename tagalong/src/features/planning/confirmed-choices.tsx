'use client';
import type {DecisionSnapshot} from '@/services/decisions';
import type {Tab} from '@/services/types';
import {Button} from '@/components/ui/button';
import {publicWebUrl} from '@/services/place-links';

export function ConfirmedChoices({snapshot,onTab,compact=false}:{snapshot:DecisionSnapshot|null;onTab:(tab:Tab)=>void;compact?:boolean}){
 if(!snapshot)return null;
 const confirmed=snapshot.decisions.filter(decision=>decision.status==='confirmed'&&decision.confirmation?.decisionVersion===decision.version).flatMap(decision=>{
  const option=decision.options.find(item=>item.id===decision.selectedOptionId);
  return option?[{id:decision.id,title:decision.title,option}]:[];
 });
 if(!confirmed.length)return null;
 return <section className={'confirmed-choices'+(compact?' compact':'')} aria-label="Confirmed group choices">
  <div className="confirmed-choices-heading"><div><span className="eyebrow">SHARED GROUP STATE</span><h3>{snapshot.finalized?'Finalized choices':'Choices the group agreed on'}</h3></div><span className="confirmed-choices-count">{confirmed.length} confirmed</span></div>
  <ul>{confirmed.map(choice=><li key={choice.id}><h4>{choice.option.label}</h4><strong>{choice.title}</strong>{!compact&&<><span className="confirmed-choice-not-booked">Not booked</span>{publicWebUrl(choice.option.url)&&<a href={publicWebUrl(choice.option.url)} target="_blank" rel="noopener noreferrer">Option website</a>}{choice.option.estimatedCostPerPerson!=null&&<span>Estimated USD {choice.option.estimatedCostPerPerson} per person · unverified</span>}{choice.option.notes&&<p>{choice.option.notes}</p>}{choice.option.provenance&&<details><summary>Source evidence</summary><p>Unverified source retrieved {new Date(choice.option.provenance.retrievedAt).toLocaleString()}</p><p>{choice.option.provenance.excerpt}</p></details>}</>}</li>)}</ul>
  {!compact&&<p>These choices are separate from bookings. Verify details with providers before committing.</p>}
  <Button variant="outline" size="sm" onClick={()=>onTab('Decisions')}>Review decisions</Button>
 </section>;
}
