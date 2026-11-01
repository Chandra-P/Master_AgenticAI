import React, {useEffect, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import './styles.css';
import {ApprovedVendors} from './ApprovedVendors';
import {ApprovedPlan} from './ApprovedPlan';

type Brief = {version:number;occasion:string|null;services:string[];event_date:string|null;date_flexibility:string|null;time_window:string|null;children:number|null;family:number|null;guest_estimate:number|null;budget:string|null;theme:string|null;priorities:string|null;explicit_unknown:string[];tentative_fields:string[]};
type Event = {id:string;brief:Brief;confirmed_version:number|null};
type Source = {id:string;kind:string;title:string;content:string;source_id:string;retrieved_at:string};
type Turn = {role:'user'|'assistant';body:string;sources?:Source[]};
type Reply = {event:Event;question:{key:string;text:string}|null;assistant_message?:string;sources?:Source[];next_action:string};
let csrf='';
async function api(path:string,body?:unknown):Promise<any> {
  const response=await fetch(path,{method:body===undefined?'GET':'POST',credentials:'same-origin',
    headers:{'Content-Type':'application/json',...(csrf?{'X-CSRF-Token':csrf}:{})},
    body:body===undefined?undefined:JSON.stringify(body)});
  const data=response.status===204?null:await response.json();
  if(!response.ok)throw new Error(typeof data?.detail==='string'?data.detail:'Please try again.');
  return data;
}

function App(){
  const [event,setEvent]=useState<Event|null>(null),[events,setEvents]=useState<Event[]>([]);
  const [turns,setTurns]=useState<Turn[]>([]),[message,setMessage]=useState('');
  const [busy,setBusy]=useState(true),[error,setError]=useState(''),[review,setReview]=useState(false);
  const [notice,setNotice]=useState('');
  const bottom=useRef<HTMLDivElement>(null);
  // Preserve the request ID on an ambiguous network error so Retry cannot append twice.
  const pending=useRef<{message:string;expected_version:number;request_id:string}|null>(null);
  async function refreshEvents(){const data=await api('/api/events');setEvents(data.events);return data.events as Event[];}
  async function openEvent(id:string){
    setBusy(true);setError('');setNotice('');pending.current=null;
    try{const data=await api(`/api/events/${id}`);setEvent(data.event);setTurns(data.messages);setReview(data.next_action==='review_brief');}
    catch(e){setError((e as Error).message);}finally{setBusy(false);}
  }
  async function start(){
    setBusy(true);setError('');setNotice('');pending.current=null;
    try{const data:Reply=await api('/api/events',{});setEvent(data.event);setTurns([{role:'assistant',body:data.question!.text}]);setReview(false);await refreshEvents();}
    catch(e){setError((e as Error).message);}finally{setBusy(false);}
  }
  useEffect(()=>{void(async()=>{try{
    const session=await api('/api/session',{});csrf=session.csrf_token;
    const saved=await refreshEvents();if(saved.length)await openEvent(saved[0].id);else await start();
  }catch(e){setError((e as Error).message);setBusy(false);}})();},[]);
  useEffect(()=>{bottom.current?.scrollIntoView({behavior:'smooth',block:'nearest'});},[turns,busy]);
  async function send(e:React.FormEvent){
    e.preventDefault();if(!event||busy||!message.trim())return;
    setBusy(true);setError('');setNotice('');
    if(!pending.current||pending.current.message!==message.trim())pending.current={message:message.trim(),expected_version:event.brief.version,request_id:crypto.randomUUID()};
    const payload=pending.current;
    try{const data:Reply=await api(`/api/events/${event.id}/messages`,payload);
      setEvent(data.event);setTurns(old=>[...old,{role:'user',body:payload.message},{role:'assistant',body:data.assistant_message||data.question?.text||'Here is your brief. Take a look and tell me if anything needs changing before we research.',sources:data.sources}]);
      setReview(!data.question);setMessage('');pending.current=null;await refreshEvents();
    }catch(e){setError((e as Error).message);}finally{setBusy(false);}
  }
  async function confirm(){
    if(!event)return;setBusy(true);setError('');
    try{const data=await api(`/api/events/${event.id}/confirm`,{expected_version:event.brief.version});setEvent(data.event);
      setNotice('Your brief is confirmed. Comparing the approved directory below; no web research or provider messages will be made.');
    }catch(e){setError((e as Error).message);}finally{setBusy(false);}
  }
  const brief=event?.brief;
  const guests=brief?.children!=null&&brief.family!=null?brief.children+brief.family:brief?.guest_estimate;
  const fact=(label:string,value:unknown,key:string)=><div className="fact" key={key}><dt>{label}</dt><dd>{value==null||value===''?'Not decided':String(value)}{brief?.tentative_fields.includes(key)&&<span className="tag">Tentative</span>}</dd></div>;
  return <div className="app"><header><a className="brand" href="/" aria-label="CONVENE home"><span className="brand-mark">c</span>convene<span className="brand-dot">.</span></a><span className="city">SAN ANTONIO, TEXAS</span><span className="preview">Local preview</span></header>
    <main><aside className="sidebar"><p className="eyebrow">A LITTLE LESS PLANNING. A LOT MORE JOY.</p><h1>Good things<br/>bring us<br/><em>together.</em></h1><p className="intro">Your celebration, your people. Let’s make a plan that feels like you.</p><div className="steps"><div className="step active"><b>01</b><span>Tell me your idea<small>A conversation, one question at a time</small></span></div><div className="step"><b>02</b><span>Review your brief<small>You decide what we research</small></span></div><div className="step"><b>03</b><span>Find your people<small>Venues, decorators & restaurant trays</small></span></div></div>
    <div className="saved"><label htmlFor="events">YOUR CELEBRATIONS · THIS BROWSER</label><select id="events" value={event?.id||''} disabled={busy||!events.length} onChange={e=>void openEvent(e.target.value)}>{events.map(e=><option key={e.id} value={e.id}>{e.brief.occasion||'New celebration'} · {e.brief.event_date||'Date undecided'}</option>)}</select><button className="text-button" disabled={busy} onClick={()=>void start()}>+ Plan another celebration</button></div></aside>
    <section className="workspace" aria-label="Planning conversation"><div className="chat-heading"><div className="avatar">c.</div><div><h2>Your celebration starts here</h2><p>A warm welcome from your CONVENE planner</p></div><span className="pill">LET’S PLAN</span></div>
      <div className="conversation" aria-live="polite" aria-busy={busy}>{turns.map((turn,i)=><div className={`turn ${turn.role}`} key={i}>{turn.role==='assistant'&&<span className="speaker">CONVENE</span>}<p>{turn.body}</p>{!!turn.sources?.length&&<details className="sources"><summary>Knowledge used · {turn.sources.length} {turn.sources.length===1?'source':'sources'}</summary>{turn.sources.map(source=><article key={source.id}><strong>{source.title}</strong><small>{source.kind==='planning'?'CONVENE planning guide · not a provider quote':'Event evidence'}</small><p>{source.content}</p>{source.source_id.startsWith('https://')&&<a href={source.source_id} target="_blank" rel="noopener noreferrer">View source ↗</a>}</article>)}</details>}</div>)}{busy&&<p className="thinking">{turns.length?'Taking a moment to understand…':'Getting your planner ready…'}</p>}<div ref={bottom}/></div>
      {error&&<div className="alert" role="alert">{error} {event&&<button className="text-button" onClick={()=>void openEvent(event.id)}>Reload saved brief</button>}</div>}
      {notice&&<div className="notice" role="status">{notice}</div>}
      {review&&<div className="review-action"><span>Ready to explore? Review your brief first.</span><button onClick={()=>void confirm()} disabled={busy||event?.confirmed_version===brief?.version}>{event?.confirmed_version===brief?.version?'Brief confirmed':'Confirm my brief'} <span aria-hidden="true">↗</span></button></div>}
      <form onSubmit={send}><label className="sr-only" htmlFor="message">Your answer or correction</label><textarea id="message" placeholder={review?'Tell me anything you’d like to change…':'Tell me a little about it…'} value={message} maxLength={4000} onChange={e=>setMessage(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();void send(e);}}} rows={2} disabled={!event||busy}/><button className="send" type="submit" disabled={busy||!message.trim()} aria-label="Send answer">↗</button></form><p className="chat-footnote">It’s okay to be unsure. We’ll work it out together. Nothing is booked or sent during this conversation.</p>
    </section>
    <aside className="brief"><p className="eyebrow">COMING TOGETHER</p><h2>Your celebration brief</h2><p className="brief-sub">A little clearer with every answer.</p><div className="version">{event?.confirmed_version===brief?.version?'Confirmed brief':'Draft brief'}{brief&&` · v${brief.version}`}</div><dl>{fact('Celebrating',brief?.occasion,'occasion')}{fact('Help with',brief?.services.length?brief.services.join(', '):null,'services')}{fact('All guests',guests,'guest_estimate')}{fact('When',brief?.event_date||brief?.date_flexibility,'event_date')}{fact('Time',brief?.time_window,'time_window')}{fact('Total budget',brief?.budget?`$${Number(brief.budget).toLocaleString()}`:null,'budget')}{brief?.services.includes('decoration')&&fact('Theme',brief.theme,'theme')}</dl><div className="brief-note"><span aria-hidden="true">✳</span><p><strong>You’re in control.</strong><br/>We’ll show you this brief before researching. Provider availability and final prices need confirmation.</p></div></aside>
    </main><ApprovedPlan event={event} locked={busy} api={api}/><ApprovedVendors ready={!!event} load={()=>api('/api/vendors')}/><footer><span>Made for meaningful moments.</span><span>Private browser session · Google account saving coming next</span></footer></div>;
}
createRoot(document.getElementById('root')!).render(<App/>);
