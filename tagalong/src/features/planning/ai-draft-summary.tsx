import type {PlanDraft} from '@/services/coordination';
import {Button} from '@/components/ui/button';
import {hasIdeaCity} from '@/services/idea-discovery';

export function AIDraftSummary({draft,location,start,end,onAnswer}:{draft:PlanDraft;location:string;start:string;end:string;onAnswer:()=>void}){
 const missingCity=!hasIdeaCity(location);
 const missingDates=!start||!end;
 return <aside className="ai-draft-summary" aria-label="What AI prepared">
  <span className="eyebrow">YOUR IDEA, ORGANIZED BY AI</span><h3>Here’s the starting point I drafted.</h3>
  <div className="ai-draft-facts"><p><strong>Where</strong>{missingCity?'Let’s choose a city':location}</p><p><strong>When</strong>{missingDates?'Dates still needed':start+(end!==start?' to '+end:'')}</p><p><strong>Who</strong>{draft.participant_count?draft.participant_count+' intended participants':'Invite your people after creating the plan'}</p></div>
  <p>I organized your idea into working details, {draft.suggested_tasks.length} suggested {draft.suggested_tasks.length===1?'task':'tasks'} and {draft.suggested_itinerary.length} draft {draft.suggested_itinerary.length===1?'activity':'activities'}. These are proposals for your group to review.</p>
  {missingCity||missingDates?<div className="ai-follow-up" role="status"><strong>{missingCity?'First, which city should I explore?':'Next, what dates should I search?'}</strong><p>{missingCity?'Add a city below so I can find relevant places.':'Add your working dates below so events match your visit. You can change them later.'}</p><Button type="button" variant="outline" onClick={onAnswer}>{missingCity?'Add the city':'Add working dates'}</Button></div>:<p className="ai-follow-up"><strong>Your working details are ready.</strong> Next, let me find a shortlist. You can adjust the details and interests below.</p>}
 </aside>;
}
