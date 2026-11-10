'use client';
import type {Plan,Tab} from '@/services/types';
import {Button} from '@/components/ui/button';
import {useDecisionSnapshot} from './decisions/use-decision-snapshot';
import {ConfirmedChoices} from './confirmed-choices';

export function ConfirmedOutcomes({plan,onTab}:{plan:Plan;onTab:(tab:Tab)=>void}){
 const {snapshot,loading,refreshing,error,reload}=useDecisionSnapshot(plan);
 return <section className="journey-outcomes" aria-label="Confirmed decision outcomes" aria-busy={loading||refreshing}>
  <h3>Confirmed choices</h3>{error?<><p role="status">{error}</p><Button variant="outline" onClick={()=>void reload()}>Reload confirmed choices</Button></>:!snapshot||refreshing?<p>{refreshing?'Refreshing current choices…':'Loading confirmed choices…'}</p>:<><p>{snapshot.finalized?'Final review completed.':'Working plan · final review still needed.'}</p><ConfirmedChoices snapshot={snapshot} onTab={onTab}/><h4>Before anyone books</h4><ul><li>Verify current prices, availability, accessibility and cancellation terms with the provider.</li><li>Review the selected options and dates together. A person must approve and complete any booking.</li></ul></>}
 </section>;
}
