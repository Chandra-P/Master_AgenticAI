'use client';
import {useEffect,useRef,useState} from 'react';
import Image from 'next/image';
import type {Plan} from '@/services/types';
import {ConnectedService,getAuth} from '@/services/connected';
import {IdeaDiscoveryService,cityIdeaSuggestions,ideaInterests,hasIdeaCity,type CityIdeasResult,type IdeaSuggestion} from '@/services/idea-discovery';
import {publicWebUrl,safeActivityImage} from '@/services/place-links';
import {Button} from '@/components/ui/button';
import {usePlanning} from './store';
import './idea-discovery.css';

export interface IdeaDiscoveryProps {city:string;start:string;end:string;initialInterests?:string[];interestReason?:string;onSelect?:(idea:IdeaSuggestion)=>void;onRemove?:(id:string)=>void;selected?:IdeaSuggestion[];plan?:Plan}
export function IdeaDiscovery(props:IdeaDiscoveryProps){
 const {mode,user,workspaceRole}=usePlanning();
 return <IdeaDiscoveryContent key={[mode,user?.id,workspaceRole,props.plan?.id].join('|')} {...props}/>;
}
function IdeaDiscoveryContent({city,start,end,onSelect,onRemove,selected=[],plan,initialInterests=[],interestReason=''}:IdeaDiscoveryProps){
 const {mode,user,config,workspaceRole}=usePlanning();
 const [interests,setInterests]=useState<string[]>([...new Set(initialInterests.filter(interest=>ideaInterests.some(value=>value===interest)))].slice(0,4)),[custom,setCustom]=useState(''),[query,setQuery]=useState('');
 const [record,setRecord]=useState<{identity:string;result:CityIdeasResult;interests:string[]}|null>(null),[searchKey,setSearchKey]=useState<string|null>(null),[error,setError]=useState('');
 const controller=useRef<AbortController|null>(null),active=useRef(true),sequence=useRef(0),locked=useRef(false);
 const cleanCity=city.trim(),hasCity=hasIdeaCity(cleanCity);
 const validDates=/^\d{4}-\d{2}-\d{2}$/.test(start)&&/^\d{4}-\d{2}-\d{2}$/.test(end)&&end>=start;
 const chosenInterests=[...interests,...(custom.trim()?[custom.trim()]:[])];
 const identity=[mode,user?.id,workspaceRole,plan?.id,plan?.revision,cleanCity,start,end,interests.join('|'),custom,query].join('::');
 const identityRef=useRef(identity);
 useEffect(()=>{identityRef.current=identity;controller.current?.abort();sequence.current++;locked.current=false;},[identity]);
 useEffect(()=>{active.current=true;return()=>{active.current=false;controller.current?.abort();};},[]);
 const result=record?.identity===identity?record.result:null,busy=searchKey===identity;
 async function suggest(){
  if(locked.current||!hasCity||!validDates||mode!=='connected'||!config?.connectedReady||!user)return;
  const searchInterests=chosenInterests.length?chosenInterests:['Food','Outdoors','Arts'];
  locked.current=true;controller.current?.abort();const request=new AbortController();controller.current=request;
  const captured=identity,requestId=++sequence.current;setSearchKey(captured);setError('');setRecord(null);
  try{const response=await new IdeaDiscoveryService(new ConnectedService(getAuth(config))).discover({city:cleanCity,start,end,interests:searchInterests,...(query.trim()?{query:query.trim()}:{})},{userId:user.id,isCurrent:()=>active.current&&identityRef.current===captured},request.signal);
   if(active.current&&sequence.current===requestId&&identityRef.current===captured)setRecord({identity:captured,result:response,interests:searchInterests});
  }catch(cause){if(active.current&&sequence.current===requestId&&!request.signal.aborted)setError(cause instanceof Error?cause.message:'Suggestions are unavailable. You can still create a plan and add your own ideas.');}
  finally{if(active.current&&sequence.current===requestId){locked.current=false;setSearchKey(null);}}
 }
 const suggestions=result?cityIdeaSuggestions(result):[];
 return <section className="idea-discovery" aria-label="Discover ideas for your group" aria-busy={busy}>
  <div className="idea-discovery-heading"><span className="eyebrow">LET’S BUILD A SHORTLIST</span><h3>What would your group enjoy?</h3><p>Let me find places and dated events for your visit. Adjust the interests if you want a different direction.</p></div>
  {initialInterests.length>0&&<p className="idea-starting-point"><strong>AI-proposed starting interests.</strong> {interestReason||'A starting point from your idea; change these to suit the group.'} These are not confirmed group preferences.</p>}
  {!hasCity&&<p className="idea-missing" role="status">Which city or area should we explore? Set the destination above to get relevant ideas.</p>}
  {!validDates&&<p className="idea-missing" role="status">What dates will you be there? Set a working start and end date above so events can match your visit.</p>}
  <div className="idea-interest-chips" role="group" aria-label="Group interests">{ideaInterests.map(interest=><button type="button" key={interest} aria-pressed={interests.includes(interest)} onClick={()=>setInterests(current=>current.includes(interest)?current.filter(item=>item!==interest):[...current,interest])}>{interest}</button>)}</div>
  <details className="idea-advanced"><summary>Refine the search (optional)</summary><label className="field">Other interests<input value={custom} maxLength={80} onChange={event=>setCustom(event.target.value)} placeholder="Architecture, markets, a quiet afternoon…"/></label>
  <label className="field">Anything else for these suggestions?<input value={query} maxLength={250} onChange={event=>setQuery(event.target.value)} placeholder="Live music on Saturday, vegetarian lunch, an easy walk…"/></label>
  </details>{!chosenInterests.length&&<p className="muted">Not sure yet? I can start with a mix of food, outdoors and arts. You can refine it afterward.</p>}
  <p className="muted">Search uses your city, dates and interests. Results need verification; no tickets, reservations or messages are created.</p>
  {mode!=='connected'||!user?<p>Sign in to search current places and events.</p>:<Button type="button" disabled={busy||!hasCity||!validDates||!config?.connectedReady} onClick={()=>void suggest()}>{busy?'Finding things to do…':chosenInterests.length?'Suggest things to do':'Find ideas for me'}</Button>}
  {busy&&<p role="status">Searching the selected city and dates. Source and tool details appear when the request finishes.</p>}{error&&<p role="alert">{error}</p>}
  {result&&<><p className="idea-starting-point">Shortlist for {cleanCity} · {start} to {end}. Searched for {record?.interests.join(', ')}. Review the sources, then choose what to propose.</p>{result.question&&<p className="idea-follow-up">{result.question}</p>}<details className="idea-execution"><summary>Sources and search details</summary><ol>{result.steps.map(step=><li key={step.id}><strong>{step.label}</strong> · {step.status}<p>{step.detail}</p></li>)}</ol>{result.sources.map(source=><details key={source.id}><summary>{source.title}</summary><p>{source.text}</p>{publicWebUrl(source.url)&&<a href={publicWebUrl(source.url)} target="_blank" rel="noopener noreferrer">Source website</a>}</details>)}</details>
   <div className="idea-suggestions">{suggestions.map(idea=>{const image=safeActivityImage(idea.image),chosen=selected.some(item=>item.id===idea.id),url=publicWebUrl(idea.url);return <article key={idea.id} aria-label={idea.name+' suggestion'}>{image&&<figure><Image src={image} alt={'Source image for '+idea.name} unoptimized referrerPolicy="no-referrer" width={360} height={180}/><figcaption>Source image · verify current details</figcaption></figure>}<div className="idea-suggestion-body"><small>{idea.category}{idea.day?' · '+idea.day:''}</small><h4>{idea.name}</h4><p>{idea.details}</p>{url&&<a href={url} target="_blank" rel="noopener noreferrer">Explore {idea.name}</a>}<details><summary>Evidence for {idea.name}</summary>{idea.source_ids.map(id=>{const source=result.sources.find(item=>item.id===id);return source?<div key={id}><strong>{source.title}</strong><p>{source.text}</p></div>:<p key={id}>Source {id}</p>;})}</details>{onSelect&&(chosen?<Button type="button" variant="outline" disabled={!onRemove} onClick={()=>onRemove?.(idea.id)}>{plan?'Proposed for review':'Remove from draft ideas'}</Button>:<Button type="button" disabled={!url||selected.length>=8} onClick={()=>onSelect(idea)}>{plan?'Propose for group decision':'Add to draft ideas'}</Button>)}</div></article>;})}</div>
   {!suggestions.length&&<p>No matching places or dated events were returned. Try another interest or refine the city and dates.</p>}
  </>}
  {selected.length>0&&<aside className="selected-draft-ideas" aria-label={plan?'Proposed group options':'Selected draft ideas'}><h4>{selected.length} of 8 {plan?'group options proposed':'draft ideas selected'}</h4><ul>{selected.map(idea=><li key={idea.id}><span>{idea.name}{idea.day?' · '+idea.day:''}</span>{onRemove&&<button type="button" aria-label={'Remove '+idea.name+' from draft ideas'} onClick={()=>onRemove(idea.id)}>Remove</button>}</li>)}</ul><small>{plan?'Proposed options await group responses and owner review. Nothing is booked.':'Reviewed ideas become draft itinerary entries. The group can still change them; nothing is booked.'}</small></aside>}
 </section>;
}
