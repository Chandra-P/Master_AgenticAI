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
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[expanded,setExpanded]=useState<string|null>(null);
 const sequence=useRef(0),controller=useRef<AbortController|null>(null),pending=useRef(false);
 const sourcePrefix=useId();
 const detailsId=sourcePrefix+'-option-details';
 const connected=mode==='connected'&&!!user&&!!config?.connectedReady;

 useEffect(()=>()=>{sequence.current++;controller.current?.abort();},[]);

 function invalidate(){
  sequence.current++;controller.current?.abort();controller.current=null;pending.current=false;
  setBusy(false);setResult(null);setError('');setExpanded(null);
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
  event.preventDefault();setExpanded(id);
  const index=result?.sources.findIndex(source=>source.id===id)??-1;
  requestAnimationFrame(()=>document.getElementById(sourcePrefix+'-'+index)?.scrollIntoView({behavior:'smooth',block:'nearest'}));
 }

 function reasons(items:GroupFitReason[]){return <ul>{items.map((item,index)=><li key={index}><p>{item.text}</p><div className="group-fit-citations">{item.source_ids.map(id=>{
  const sourceIndex=result?.sources.findIndex(source=>source.id===id)??-1;
  const source=result?.sources[sourceIndex];
  return source?<a key={id} href={'#'+sourcePrefix+'-'+sourceIndex} onClick={event=>showSource(event,id)}>View source: {source.title}</a>:null;
 })}</div></li>)}</ul>;}

 return <section className="tab-content group-fit-panel">
  <div className="eyebrow">DECIDE WITH CONTEXT</div>
  <h2>Does this option fit our group?</h2>
  <p>Compare an option with current plan facts, saved Notes, and relevant conversation evidence. This is advice for the group to review, not an approval or booking.</p>
  {!connected?<p>Sign in to a shared plan to check an option against your group’s sources. <Link href="/account">Open your account</Link></p>:<>
   <form onSubmit={event=>{event.preventDefault();void assess();}} className="group-fit-form">
    <label className="field">Option name<input required maxLength={160} value={name} onChange={event=>{invalidate();setName(event.target.value);}} placeholder="Restaurant, activity, or travel option"/></label>
    <div className="field"><label htmlFor={detailsId}>Option details or menu</label><textarea id={detailsId} maxLength={6000} value={details} onChange={event=>{invalidate();setDetails(event.target.value);}} rows={5} placeholder="Paste the menu, accessibility details, or information you want checked."/></div>
    <div className="group-fit-inputs"><label className="field">Estimated cost per person<input type="number" min={0} step="0.01" value={cost} onChange={event=>{invalidate();setCost(event.target.value);}} placeholder="Optional estimate"/></label>
    <label className="field">Option website (optional)<input type="url" maxLength={2048} value={url} onChange={event=>{invalidate();setUrl(event.target.value);}} placeholder="https://venue.example/menu"/></label></div>
    <p className="muted">Your option and selected plan evidence are sent to OpenAI. Option details are user-provided and unverified; website links are not fetched. Add a menu in Notes or paste its text here. Current hours, availability, accessibility, and allergen handling still need direct confirmation.</p>
    <Button type="submit" disabled={busy}>{busy?'Checking your group’s context…':'Check group fit'}</Button>
   </form>
   {busy&&<p role="status">Retrieving group evidence and checking this option…</p>}
   {error&&<p role="alert">{error}</p>}
   {result&&<div className="group-fit-result" aria-live="polite">
    <h3>{result.verdict==='fits'?'Fits the recorded constraints':result.verdict==='conflicts'?'Conflicts with the group':'More information needed'}</h3>
    <p>{result.summary}</p>
    {result.retrieval_status==='unavailable'&&<p className="group-fit-notice">Historical retrieval was unavailable. This check uses the current plan facts and any available saved Notes; it may miss earlier discussion.</p>}
    {result.context_truncated&&<p className="group-fit-notice">Only selected evidence excerpts were considered. Review the original sources for full context.</p>}
    {result.matches.length>0&&<section><h4>What fits</h4>{reasons(result.matches)}</section>}
    {result.conflicts.length>0&&<section><h4>What conflicts</h4>{reasons(result.conflicts)}</section>}
    {result.unknowns.length>0&&<section><h4>What to check next</h4><ul>{result.unknowns.map((item,index)=><li key={index}>{item}</li>)}</ul></section>}
    <section className="group-fit-sources"><h4>Sources used</h4><p>Current plan facts are authoritative. Menus, messages, and option details are evidence to review, not guarantees about a venue.</p>
     {result.sources.length===0&&<p>No supporting source excerpts were returned. Add a Note or more option details and check again.</p>}
     {result.sources.map((source,index)=><article id={sourcePrefix+'-'+index} key={source.id}>
      <button type="button" aria-expanded={expanded===source.id} aria-controls={sourcePrefix+'-text-'+index} onClick={()=>setExpanded(expanded===source.id?null:source.id)}>Source: {source.title}</button>
      {expanded===source.id&&<p id={sourcePrefix+'-text-'+index}>{source.text}</p>}
     </article>)}
    </section>
    <p className="muted">Nothing was added to the itinerary and no decision was changed. Discuss the result, update missing details, or create a poll before deciding.</p>
   </div>}
  </>}
 </section>;
}
