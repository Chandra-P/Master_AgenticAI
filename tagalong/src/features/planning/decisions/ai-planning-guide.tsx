'use client';
import {useState} from 'react';
import type {Plan,Tab} from '@/services/types';
import type {DecisionSnapshot} from '@/services/decisions';
import {Button} from '@/components/ui/button';
import {usePlanning} from '../store';
import {FindOptionsButton} from '../research/option-workbench';

export function AIPlanningGuide({plan,snapshot,onTab}:{plan:Plan;snapshot:DecisionSnapshot;onTab:(tab:Tab)=>void}){
 const {mode,sendMessage,busy}=usePlanning();const [asking,setAsking]=useState(false),[error,setError]=useState('');
 const open=snapshot.decisions.filter(decision=>decision.required&&decision.status!=='confirmed');
 const next=open[0];
 async function help(){
  if(asking||busy)return;
  if(mode!=='connected'){onTab('Chat');return;}
  setAsking(true);setError('');
  try{await sendMessage(plan.id,'@Tagalong help us take the next step. Use our current plan, decisions and saved documents. Briefly summarize what is agreed, identify the most important unresolved choice and suggest at most three next actions. Ask only for missing information. Cite saved sources where used. Working dates and budgets are proposals, not agreement. Do not invent external search results, votes or bookings.');onTab('Chat');}
  catch(cause){setError(cause instanceof Error?cause.message:'AI guidance is unavailable. Your decisions and options are still available below.');}
  finally{setAsking(false);}
 }
 return <section className="ai-planning-guide" aria-label="AI planning guide">
  <div><span className="eyebrow">LET TAGALONG DO THE LEGWORK</span><h2>{snapshot.finalized?'Your group has a plan.':next?'Let’s move '+next.title.toLowerCase()+' forward.':'Ready for the final review.'}</h2><p>{snapshot.finalized?'AI can help identify preparation tasks. Review real reservations separately.':'You don’t have to build everything by hand. Ask AI to summarize your group’s needs and recommend what to do next, or find sourced options to compare.'}</p></div>
  <ol className="guided-flow-steps" aria-label="How planning works"><li>AI suggests options</li><li>Everyone responds</li><li>The owner confirms</li></ol>
  <div className="journey-buttons"><Button type="button" disabled={asking||busy} onClick={()=>void help()}>{asking?'AI is reviewing your plan…':mode==='connected'?'Ask AI for the next step':'Try the demo chat'}</Button>{next&&(['lodging','activities','meal','place'].includes(next.category)?<FindOptionsButton plan={plan} decisionId={next.id} label="Find options for us"/>:<Button type="button" variant="outline" onClick={()=>onTab('Chat')}>Explore city ideas</Button>)}</div>
  <small>{mode==='connected'?'The AI request is shared in this plan’s Chat and uses your saved context. It does not vote or finalize.':'Local demo chat is simulated; sign in for connected AI and sources.'}</small>{error&&<p role="alert">{error}</p>}
 </section>;
}
