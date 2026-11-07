'use client';
import type {Plan,Tab} from '@/services/types';
import {publicWebUrl} from '@/services/place-links';
import {Button} from '@/components/ui/button';
import {useDecisionSnapshot} from './decisions/use-decision-snapshot';

export function ConfirmedOutcomes({plan,onTab}:{plan:Plan;onTab:(tab:Tab)=>void}){
 const {snapshot,loading,refreshing,error,reload}=useDecisionSnapshot(plan);
 const confirmed=snapshot?.decisions.filter(d=>d.status==='confirmed'&&d.confirmation?.decisionVersion===d.version)||[];
 return <section className="journey-outcomes" aria-label="Confirmed decision outcomes" aria-busy={loading||refreshing}>
  <h3>Confirmed choices</h3><p>Group decisions are separate from reservations. Nothing here is booked.</p>
  {error?<><p role="status">{error}</p><Button variant="outline" onClick={()=>void reload()}>Reload confirmed choices</Button></>:!snapshot||refreshing?<p>{refreshing?'Refreshing current choices…':'Loading confirmed choices…'}</p>:<>
   <p>{snapshot.finalized?'Final review completed.':'Working plan · final review still needed.'}</p>
   {confirmed.length?<div className="journey-outcome-list">{confirmed.map(decision=>{
    const selected=decision.options.find(option=>option.id===decision.selectedOptionId);
    if(!selected)return null;
    const url=publicWebUrl(selected.url);
    return <article key={decision.id}><small>{decision.title}</small><h4>{selected.label}</h4>{url&&<a href={url} target="_blank" rel="noopener noreferrer">Option website</a>}{selected.estimatedCostPerPerson!=null&&<p>Estimated USD {selected.estimatedCostPerPerson} per person · unverified</p>}{selected.notes&&<p className="journey-option-notes">{selected.notes}</p>}<span className="booking-status">Not booked</span>{selected.provenance&&<details><summary>Source evidence</summary><p>Unverified source retrieved {new Date(selected.provenance.retrievedAt).toLocaleString()}</p><p>{selected.provenance.excerpt}</p></details>}</article>;
   })}</div>:<p>No current confirmed choices yet. Review options with the group, then ask the owner to confirm.</p>}
   <h4>Before anyone books</h4><ul><li>Verify current prices, availability, accessibility and cancellation terms with the provider.</li><li>Review the selected options and dates together. A person must approve and complete any booking.</li></ul>
   <Button variant="outline" onClick={()=>onTab('Decisions')}>Review group decisions</Button>
  </>}
 </section>;
}
