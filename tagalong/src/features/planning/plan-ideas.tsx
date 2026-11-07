'use client';
import {useState} from 'react';
import type {Plan} from '@/services/types';
import type {IdeaSuggestion} from '@/services/idea-discovery';
import {IdeaDiscovery} from './idea-discovery';
import {useDecisionSnapshot} from './decisions/use-decision-snapshot';
import {OptionWorkbench} from './research/option-workbench';
import {Dialog} from '@/components/ui/dialog';

/** Keep the next planning question visible beside the group conversation. */
export function PlanIdeas({plan}:{plan:Plan}){
 const {snapshot,loading,error}=useDecisionSnapshot(plan);
 const [city,setCity]=useState(/to decide|somewhere/i.test(plan.location)?'':plan.location);
 const [start,setStart]=useState(plan.start),[end,setEnd]=useState(plan.end||plan.start);
 const [candidate,setCandidate]=useState<IdeaSuggestion|null>(null);
 const [picked,setPicked]=useState<{scope:string;ideas:IdeaSuggestion[]}>({scope:'',ideas:[]});
 const scope=[city,start,end].join('|');
 const target=snapshot?.decisions.find(decision=>decision.category==='activities'||decision.category==='meal');
 return <aside id={'plan-ideas-'+plan.id} className="plan-ideas-panel" aria-label="AI city planning guide">
  <h2>Let’s find your kind of good time.</h2><p>Tell Tagalong what interests your group. Pick a place or dated event, then propose it for everyone to review.</p>
  <label className="field">Explore city<input maxLength={150} value={city} onChange={event=>setCity(event.target.value)}/></label>
  <div className="field-row"><label className="field">Visit start date<input type="date" value={start} onChange={event=>{setStart(event.target.value);if(end<event.target.value)setEnd(event.target.value);}}/></label><label className="field">Visit end date<input type="date" min={start} value={end} onChange={event=>setEnd(event.target.value)}/></label></div>
  {error&&<p role="alert">{error}</p>}
  <IdeaDiscovery city={city} start={start} end={end} plan={plan} selected={picked.scope===scope?picked.ideas:[]} onSelect={setCandidate}/>
  <Dialog open={!!candidate} onOpenChange={open=>{if(!open)setCandidate(null);}} title="Propose this idea" description="Review the source and details, then add a voting option or suggest it in comments.">
   {candidate&&(loading||!snapshot?<p role="status">Load the current decisions before proposing this idea. Close and try again when decisions are available.</p>:<OptionWorkbench key={candidate.id} plan={plan} decisionId={target?.id} initialOption={{id:candidate.id,name:candidate.name,details:[candidate.day?'Event date: '+candidate.day:'',candidate.details].filter(Boolean).join('\n'),url:candidate.url,image:candidate.image,source_ids:[],provenance:candidate.provenance}} onDone={()=>{setPicked(previous=>({scope,ideas:[...(previous.scope===scope?previous.ideas:[]).filter(idea=>idea.id!==candidate.id),candidate]}));setCandidate(null);}}/>)}
  </Dialog>
 </aside>;
}
