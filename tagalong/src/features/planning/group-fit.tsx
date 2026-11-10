'use client';

import {useEffect,useId,useRef,useState,type MouseEvent} from 'react';
import Link from 'next/link';
import {Button} from '@/components/ui/button';
import {publicWebUrl} from '@/services/place-links';
import {GroupFitService,type GroupFitOption,type GroupFitReason,type GroupFitResult} from '@/services/group-fit';
import type {Plan} from '@/services/types';
import {usePlanning} from './store';

export function GroupFit({plan,initialOption}:{plan:Plan;initialOption?:GroupFitOption}){
 const {mode,user,workspaceRole}=usePlanning();
 return <GroupFitForm key={JSON.stringify([mode,user?.id,workspaceRole,plan.id,plan.revision,initialOption])} plan={plan} initialOption={initialOption}/>;
}

function GroupFitForm({plan,initialOption}:{plan:Plan;initialOption?:GroupFitOption}){
 const {mode,user,config}=usePlanning();
 const [name,setName]=useState(initialOption?.name||'');
 const [details,setDetails]=useState(initialOption?.details||'');
 const [url,setUrl]=useState(initialOption?.url||'');
 const [cost,setCost]=useState(initialOption?.estimated_cost_per_person?.toString()||'');
 const [result,setResult]=useState<GroupFitResult|null>(null);
 const [busy,setBusy]=useState(false),[error,setError]=useState('');
 const sequence=useRef(0),controller=useRef<AbortController|null>(null),pending=useRef(false);
 const sourcePrefix=useId();
 const detailsId=sourcePrefix+'-option-details';
 const connected=mode==='connected'&&!!user&&!!config?.connectedReady;

 useEffect(()=>()=>{sequence.current++;controller.current?.abort();},[]);

 function invalidate(){
  sequence.current++;controller.current?.abort();controller.current=null;pending.current=false;
  setBusy(false);setResult(null);setError('');
 }

 async function assess(){
  if(!connected||!config||pending.current)return;
  invalidate();
  if(!name.trim()){setError('Give this option a name.');return;}
  const website=url.trim()?publicWebUrl(url.trim(),true):undefined;
  if(url.trim()&&!website){setError('Use a public HTTPS website link. The link is not fetched by this check.');return;}
  const estimate=cost.trim()?Number(cost):undefined;
  if(estimate!==undefined&&(!Number.isFinite(estimate)||estimate<0)){setError('Enter a non-negative cost per person.');return;}
  const current=sequence.current,request=new AbortController();controller.current=request;pending.current=true;setBusy(true);
  try{
   const option:GroupFitOption={name:name.trim(),details:details.trim(),...(website?{url:website}:{}),...(estimate!==undefined?{estimated_cost_per_person:estimate}:{})};
   const response=await new GroupFitService(config).assess(plan.id,plan.revision??0,option,request.signal);
   if(current===sequence.current&&!request.signal.aborted)setResult(response);
  }catch(cause){
   if(current===sequence.current&&!request.signal.aborted)setError(cause instanceof Error?cause.message:'Could not check group fit. Try again.');
  }finally{
   if(current===sequence.current){pending.current=false;setBusy(false);controller.current=null;}
  }
 }

 function showSource(event:MouseEvent<HTMLAnchorElement>,id:string){
  if(event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
  event.preventDefault();
  const index=result?.sources.findIndex(source=>source.id===id)??-1;
  const section=document.getElementById(sourcePrefix+'-evidence');
  const item=document.getElementById(sourcePrefix+'-'+index);
  if(section instanceof HTMLDetailsElement)section.open=true;
  if(item instanceof HTMLDetailsElement)item.open=true;
  requestAnimationFrame(()=>item?.scrollIntoView({behavior:'smooth',block:'nearest'}));
 }

 function reasons(items:GroupFitReason[]){return <ul>{items.map((item,index)=><li key={index}><p>{item.text}</p><div className="group-fit-citations">{item.source_ids.map(id=>{
  const sourceIndex=result?.sources.findIndex(source=>source.id===id)??-1;
  const source=result?.sources[sourceIndex];
  return source?<a key={id} href={'#'+sourcePrefix+'-'+sourceIndex} aria-label={'Evidence '+(sourceIndex+1)+': '+source.title} title={source.title} onClick={event=>showSource(event,id)}>Evidence {sourceIndex+1}</a>:null;
 })}</div></li>)}</ul>;}

 return <section className="tab-content group-fit-panel">
  <div className="eyebrow">DECIDE WITH CONTEXT</div>
  <h2>Does this option fit our group?</h2>
  <p>See how this option fits your group’s recorded needs.</p>
  {!connected?<p>Sign in to a shared plan to check an option against your group’s sources. <Link href="/account">Open your account</Link></p>:<>
   <form onSubmit={event=>{event.preventDefault();void assess();}} className="group-fit-form">
    <label className="field">Option name<input required maxLength={160} value={name} onChange={event=>{invalidate();setName(event.target.value);}} placeholder="Restaurant, activity, or travel option"/></label>
    <div className="field"><label htmlFor={detailsId}>Option details or menu</label><textarea id={detailsId} maxLength={6000} value={details} onChange={event=>{invalidate();setDetails(event.target.value);}} rows={5} placeholder="Paste the menu, accessibility details, or information you want checked."/></div>
    <div className="group-fit-inputs"><label className="field">Estimated cost per person<input type="number" min={0} step="0.01" value={cost} onChange={event=>{invalidate();setCost(event.target.value);}} placeholder="Optional estimate"/></label>
    <label className="field">Option website (optional)<input type="url" maxLength={2048} value={url} onChange={event=>{invalidate();setUrl(event.target.value);}} placeholder="https://venue.example/menu"/></label></div>
    <details className="group-fit-disclosure"><summary>What the AI checks</summary><p>Your option is compared with saved group context and plan facts. Website links are not fetched; venue details, prices, hours, access and allergy handling need direct confirmation.</p></details>
    <Button type="submit" disabled={busy}>{busy?'Checking your group’s context…':'Check group fit'}</Button>
   </form>
   {busy&&<p role="status">Retrieving group evidence and checking this option…</p>}
   {error&&<p role="alert">{error}</p>}
   {result&&<div className="group-fit-result" aria-live="polite">
    <h3>{result.verdict==='fits'?'Fits the recorded constraints':result.verdict==='conflicts'?'Conflicts with the group':'More information needed'}</h3>
    <p>{result.summary}</p>
    <div className="group-fit-agent-trace" aria-label="AI work used"><span>{result.retrieval_status==='unavailable'?'Pinecone RAG unavailable':`Pinecone RAG · ${result.sources.filter(source=>source.retrieval_origin==='pinecone').length} ${result.sources.filter(source=>source.retrieval_origin==='pinecone').length===1?'source':'sources'}`}</span><span>OpenAI group-fit check</span><span>Group decides</span></div>
    {result.retrieval_status==='unavailable'&&<p className="group-fit-notice">Historical retrieval was unavailable. This check uses the current plan facts and any available saved Notes; it may miss earlier discussion.</p>}
    {result.index_freshness&&result.index_freshness.status!=='current'&&<p className="group-fit-notice" role="status">{result.index_freshness.status==='pending'?'Some saved sources are waiting to be indexed.':'Some saved sources could not be indexed.'} Current Notes and plan facts are included; older discussion may be missing ({result.index_freshness.indexed_sources} of {result.index_freshness.current_sources} current sources indexed).</p>}
    {result.context_truncated&&<p className="group-fit-notice">Only selected evidence excerpts were considered. Review the original sources for full context.</p>}
    {(result.matches.length+result.conflicts.length+result.unknowns.length)>0&&<details className="group-fit-findings"><summary>Review findings · {result.matches.length+result.conflicts.length+result.unknowns.length}</summary>
     {result.matches.length>0&&<section><h4>What fits</h4>{reasons(result.matches)}</section>}
     {result.conflicts.length>0&&<section><h4>What conflicts</h4>{reasons(result.conflicts)}</section>}
     {result.unknowns.length>0&&<section><h4>What to check next</h4><ul>{result.unknowns.map((item,index)=><li key={index}>{item}</li>)}</ul></section>}
    </details>}
    {result.sources.length===0?<p className="group-fit-empty-evidence">No group evidence found. Add a Note or option details.</p>:<details className="group-fit-sources" id={sourcePrefix+'-evidence'}><summary>Evidence used · {result.sources.length}</summary><p>Plan facts are authoritative. Saved messages and menus are evidence to review, not guarantees.</p>
     {result.sources.map((source,index)=><details id={sourcePrefix+'-'+index} key={source.id}>
      <summary><span>Evidence {index+1} · {source.title}</span><small className="group-fit-source-origin">{originLabel(source.retrieval_origin)}</small></summary>
      <p id={sourcePrefix+'-text-'+index}>{source.text}</p>
     </details>)}
    </details>}
    <p className="muted group-fit-next-step">No plan changes made. Review the evidence, then decide together.</p>
   </div>}
  </>}
 </section>;
}

function originLabel(origin:string|undefined){switch(origin){case 'pinecone':return 'retrieved from this plan’s Pinecone memory';case 'saved_note':return 'current saved Note';case 'recent_message':return 'recent conversation';case 'current_decision':return 'current decision or comment';case 'postgres':return 'current plan facts';case 'user_input':return 'option details you supplied';default:return 'saved plan evidence';}}
