'use client';
import {useEffect,useRef,useState} from 'react';
import {useRouter} from 'next/navigation';
import type {Plan} from '@/services/types';
import {ConnectedService,getAuth} from '@/services/connected';
import {DemoPlanService,type DemoStory} from '@/services/demo-plan';
import {publicWebUrl} from '@/services/place-links';
import {Button} from '@/components/ui/button';
import {Dialog} from '@/components/ui/dialog';
import {usePlanning} from '../store';
import {StoryPhoto} from './source-photo';
import './demo-plan-story.css';

export function CreateDemoPlanButton(){
 const {mode,user,workspaceRole}=usePlanning();
 return <CreateDemoPlanAction key={[mode,user?.id,workspaceRole].join('|')}/>;
}
function CreateDemoPlanAction(){
 const {mode,config,user,workspaceRole,reload}=usePlanning();const router=useRouter();
 const [busy,setBusy]=useState(false),[error,setError]=useState('');
 const current=mode+'|'+(user?.id||'')+'|'+workspaceRole;const identity=useRef(current);const mounted=useRef(true);
 useEffect(()=>{identity.current=current;mounted.current=true;return()=>{mounted.current=false;};},[current]);
 const locked=useRef(false);const requestKey=useRef<{identity:string;key:string}|null>(null);
 if(mode!=='connected'||!config?.connectedReady||!user)return null;
 return <div className="demo-plan-create"><Button variant="outline" disabled={busy} onClick={async()=>{
  if(locked.current)return;locked.current=true;setBusy(true);setError('');const captured=current;
  if(requestKey.current?.identity!==captured)requestKey.current={identity:captured,key:crypto.randomUUID()};
  try{const plan=await new DemoPlanService(new ConnectedService(getAuth(config))).create(requestKey.current!.key,{userId:user.id,isCurrent:()=>mounted.current&&identity.current===captured});if(!mounted.current||identity.current!==captured)return;await reload();if(mounted.current&&identity.current===captured)router.push('/plans/'+encodeURIComponent(plan.id)+'?tab=Overview');}
  catch(cause){if(mounted.current&&identity.current===captured)setError(cause instanceof Error?cause.message:'Could not save the demo plan. Retry to safely reuse this request.');}
  finally{locked.current=false;if(mounted.current&&identity.current===captured)setBusy(false);}
 }}>{busy?'Saving demo walkthrough…':'Add four-friends demo plan'}</Button><small>Creates a saved fictional walkthrough in your account. Scripted AI and votes; no bookings.</small>{error&&<p role="alert">{error}</p>}</div>;
}

export function DemoPlanStory({plan}:{plan:Plan}){
 const {mode,user,workspaceRole}=usePlanning();
 if(mode!=='connected'||plan.demo_template!=='austin-four-friends')return null;
 return <DemoPlanStoryContent key={[mode,user?.id,workspaceRole,plan.id].join('|')} plan={plan}/>;
}
function DemoPlanStoryContent({plan}:{plan:Plan}){
 const {mode,config,user,workspaceRole,sendMessage}=usePlanning();
 const memberId=user?.id;
 const [liveBusy,setLiveBusy]=useState(false),[liveError,setLiveError]=useState('');
 const liveReply=plan.messages.filter(message=>message.assistant&&!message.simulation).at(-1);
 const [open,setOpen]=useState(false),[record,setRecord]=useState<{key:string;story:DemoStory}|null>(null),[error,setError]=useState(''),[loading,setLoading]=useState(false),[step,setStep]=useState(0);
 const current=[mode,memberId,workspaceRole,plan.id].join('|');const identity=useRef(current);
 useEffect(()=>{identity.current=current;},[current]);
 const story=record?.key===current?record.story:null;
 useEffect(()=>{if(!open||mode!=='connected'||!config||!memberId)return;let active=true;const captured=current;
  const api=new DemoPlanService(new ConnectedService(getAuth(config)));
  queueMicrotask(()=>{if(active){setLoading(true);setError('');}});
  void api.story(plan.id,{userId:memberId,isCurrent:()=>active&&identity.current===captured}).then(result=>{if(active&&identity.current===captured){setRecord({key:captured,story:result});setStep(0);}}).catch(cause=>{if(active&&identity.current===captured)setError(cause instanceof Error?cause.message:'Could not load the saved story.');}).finally(()=>{if(active&&identity.current===captured)setLoading(false);});
  return()=>{active=false;};
 },[open,mode,config,memberId,current,plan.id]);
 if(mode!=='connected'||plan.demo_template!=='austin-four-friends')return null;
 const milestone=story?.milestones[step];
 return <><Button variant="outline" onClick={()=>setOpen(true)}>View demo story</Button><Dialog open={open} onOpenChange={setOpen} title="Four friends, one Austin weekend" description="Fictional walkthrough · scripted AI and votes · no bookings">
  <div className="demo-plan-story" aria-busy={loading}>
   <p className="demo-story-disclosure">This saved story illustrates collaboration. Alex, Maya, Sam and Jordan are fictional adults, separate from actual plan members. The assistant text and votes are scripted. Real plan decisions still require real member responses.</p>
   {loading&&<p role="status">Loading the saved walkthrough…</p>}{error&&<p role="alert">{error}</p>}
   {story&&<><div className="demo-story-cast" aria-label="Fictional story cast">{story.cast.map(person=><div key={person.name}><span style={{backgroundColor:person.color}} aria-hidden="true">{person.name[0]}</span><strong>{person.name}</strong><small>Fictional friend</small></div>)}</div>
    <section aria-label="Story replay"><div className="demo-story-controls"><Button variant="outline" disabled={step===0} onClick={()=>setStep(index=>Math.max(0,index-1))}>Previous step</Button><span aria-live="polite">Step {step+1} of {story.milestones.length}</span><Button variant="outline" disabled={step>=story.milestones.length-1} onClick={()=>setStep(index=>Math.min(story.milestones.length-1,index+1))}>Next step</Button><Button variant="ghost" onClick={()=>setStep(0)}>Replay from start</Button></div>
     {milestone&&<article className="demo-story-milestone"><h3>{milestone.title}</h3>{milestone.ai&&<strong>Scripted AI · retrieval illustration</strong>}<p>{milestone.text}</p>{milestone.votes&&<table><caption>Fictional responses · never counted as real plan votes</caption><thead><tr><th>Story cast</th><th>Illustrative response</th></tr></thead><tbody>{Object.entries(milestone.votes).map(([name,vote])=><tr key={name}><td>{name}</td><td>{vote}</td></tr>)}</tbody></table>}<details><summary>Evidence used in this story step ({milestone.sourceIds.length})</summary>{milestone.sourceIds.map(id=>{const source=story.sources.find(item=>item.id===id);return source?<blockquote key={id}><strong>{source.title}</strong><small>Saved source ID: {source.id}</small><p>{source.text}</p></blockquote>:null;})}<p>These excerpts are saved plan documents. This replay does not execute live retrieval, web search or a model call. Ask the connected assistant about these notes to exercise actual configured retrieval.</p></details></article>}
    </section>
    <section aria-label="Story selected options"><h3>The fictional group’s selections</h3><p>All amounts below are fictional estimates for demonstration. Check actual prices, availability, transport, access and cancellation terms. Reference links checked {story.referenceDate}.</p><div className="demo-story-choices">{story.choices.map(choice=><article key={choice.category}>{choice.image&&<StoryPhoto image={choice.image} label={choice.label}/>}<small>{choice.category}</small><h4>{choice.label}</h4>{choice.estimate!=null&&<p>Fictional estimate USD {choice.estimate} per person</p>}{publicWebUrl(choice.url)&&<a href={publicWebUrl(choice.url)} target="_blank" rel="noopener noreferrer">Official reference website</a>}<p>Not booked</p><details><summary>How we chose {choice.category.toLowerCase()}</summary>{choice.alternatives&&<><h5>Alternatives considered</h5><ul>{choice.alternatives.map(alternative=><li key={alternative}>{alternative}</li>)}</ul></>}{choice.reason&&<p>{choice.reason}</p>}{choice.votes&&<><h5>Four fictional responses</h5><ul>{Object.entries(choice.votes).map(([name,response])=><li key={name}><strong>{name}:</strong> {response.replaceAll('_',' ')}</li>)}</ul></>}<small>Story evidence: {choice.sourceIds?.join(', ')}. These scripted responses are separate from real plan ballots.</small></details></article>)}</div></section>
    <section aria-label="Final fictional itinerary"><h3>The story’s final day-by-day itinerary</h3><p>This is a fictional agreed outline, separate from actual decision confirmation or a reservation.</p>{story.days.map(day=><article className="demo-story-day" key={day.date}><h4>{day.title}</h4><small>{day.date}</small><ol>{day.items.map(item=><li key={item.time+item.title}><StoryPhoto image={item.image} label={item.location}/><div><strong>{item.time} · {item.title}</strong><p>{item.location}</p><small>Not booked · verify with provider</small></div></li>)}</ol></article>)}</section>
    <section aria-label="Live RAG and AI demonstration"><h3>Try actual RAG and AI with this plan</h3>{story.liveCheck?.status==='completed'&&<aside aria-label="Saved live RAG verification"><h4>Verified live check</h4><p>Recorded {new Date(story.liveCheck.at).toLocaleString()} · actual configured providers, separate from the scripted story.</p><ul>{story.liveCheck.tools.map((tool,index)=><li key={index}>{tool.tool}: {tool.status} · {tool.match_count} matching sources</li>)}</ul><p>AI model {story.liveCheck.model} produced a saved reply with {story.liveCheck.sourceIds.length} citations.</p></aside>}<p>This button sends the saved fictional context to your configured AI service. It makes a normal assistant request, may use your provider quota, and saves the real reply and citations in Chat. It does not create votes or bookings.</p><Button disabled={liveBusy} onClick={async()=>{if(liveBusy)return;setLiveBusy(true);setLiveError('');try{await sendMessage(plan.id,'@Tagalong remember the fictional demo constraints and discussion documents. Explain how the four friends resolved date availability, lodging cost, vegetarian dining and pace conflicts. Cite saved sources. Keep estimates and votes clearly fictional; do not claim bookings.');}catch(cause){setLiveError(cause instanceof Error?cause.message:'The live assistant check could not finish.');}finally{setLiveBusy(false);}}}>{liveBusy?'Asking the configured assistant…':'Run live RAG and AI check'}</Button>{liveError&&<p role="alert">{liveError}</p>}{liveReply&&<article><h4>Latest live AI reply in this plan</h4><p>{liveReply.text}</p>{liveReply.sources?.map(source=><details key={source.id}><summary>Live citation: {source.title}</summary><p>{source.text}</p></details>)}</article>}</section><details><summary>Saved RAG evidence and how to try the connected assistant</summary><p>The constraints, discussion and official-links notes below are saved as normal plan documents for the configured ingestion pipeline. In Chat, ask: “@Tagalong use the fictional demo constraints and discussion notes to explain how the friends resolved the cost and pace conflict. Cite sources.” Live retrieval depends on configured indexing; Chat shows actual source citations. Use Chat → Find options for actual retrieval and tool receipts, or Check group fit for configured live AI analysis.</p>{story.sources.map(source=><article key={source.id}><h4>{source.title}</h4><small>Source ID: {source.id}</small><p>{source.text}</p></article>)}</details>
   </>}
  </div>
 </Dialog></>;
}
