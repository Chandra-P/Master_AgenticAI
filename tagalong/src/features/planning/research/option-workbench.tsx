'use client';
import {useEffect,useRef,useState} from 'react';
import {Button} from '@/components/ui/button';
import {Dialog} from '@/components/ui/dialog';
import {publicWebUrl} from '@/services/place-links';
import {OptionResearchService,type ResearchResult,type ResearchOption} from '@/services/option-research';
import type {DecisionOptionDetails} from '@/services/decisions';
import type {Plan} from '@/services/types';
import {usePlanning} from '../store';
import {useDecisionSnapshot} from '../decisions/use-decision-snapshot';
import {GroupFit} from '../group-fit';
import {ResearchResults} from './research-results';
import './option-workbench.css';

export function OptionWorkbench({plan,decisionId,initialMode='manual',onDone,initialOption}:{plan:Plan;decisionId?:string;initialMode?:'manual'|'research';onDone:()=>void;initialOption?:ResearchOption}){
 const {mode,user,workspaceRole}=usePlanning();
 return <Workbench key={[plan.id,mode,user?.id,workspaceRole].join('|')} plan={plan} decisionId={decisionId} initialMode={initialMode} onDone={onDone} initialOption={initialOption}/>;
}
function Workbench({plan,decisionId,initialMode,onDone,initialOption}:{plan:Plan;decisionId?:string;initialMode:'manual'|'research';onDone:()=>void;initialOption?:ResearchOption}){
 const {mode,user,config,workspaceRole,notify}=usePlanning();
 const {snapshot,run,pending,loading,error:decisionError}=useDecisionSnapshot(plan);
 const [target,setTarget]=useState(decisionId||'');
 const current=snapshot?.decisions.find(d=>d.id===(target||snapshot.decisions[0]?.id));
 const [view,setView]=useState(initialMode),[name,setName]=useState(initialOption?.name||''),[url,setUrl]=useState(initialOption?.url||''),[cost,setCost]=useState(initialOption?.estimated_cost_per_person?.toString()||''),[notes,setNotes]=useState(initialOption?.details||'');
 const [query,setQuery]=useState(''),[location,setLocation]=useState(/to decide|somewhere/i.test(plan.location)?'':plan.location);
 const [result,setResult]=useState<{key:string;data:ResearchResult}|null>(null),[searchKey,setSearching]=useState<string|null>(null),[error,setError]=useState('');
 const [selected,setSelected]=useState<ResearchOption|null>(initialOption||null),[fit,setFit]=useState<ResearchOption|null>(null);
 const controller=useRef<AbortController|null>(null),sequence=useRef(0),active=useRef(true),busyRef=useRef(false);
 const identity=[plan.id,plan.revision,mode,user?.id,workspaceRole,query,location,current?.category,current?.id,current?.version].join('|');
 const searching=searchKey===identity;
 const identityRef=useRef(identity);
 useEffect(()=>{identityRef.current=identity;controller.current?.abort();sequence.current++;busyRef.current=false;},[identity]);
 useEffect(()=>{active.current=true;return()=>{active.current=false;controller.current?.abort();};},[]);
 const owner=mode==='demo'||plan.role==='owner';
 const displayed=result?.key===identity?result.data:null;
 async function search(){
  if(busyRef.current||!config||!user||mode!=='connected')return;
  busyRef.current=true;const seq=++sequence.current;const captured=identity;const request=new AbortController();controller.current=request;setSearching(identity);setError('');setResult(null);
  try{const data=await new OptionResearchService(config).search(plan.id,plan.revision??0,query.trim(),current?.category||'general',location.trim(),request.signal,user.id,()=>active.current&&identityRef.current===captured);
   if(active.current&&seq===sequence.current&&identityRef.current===captured)setResult({key:captured,data});
  }catch(cause){if(active.current&&seq===sequence.current&&!request.signal.aborted)setError(cause instanceof Error?cause.message:'Research could not finish. You can still add an option manually.');}
  finally{if(active.current&&seq===sequence.current){setSearching(null);busyRef.current=false;}}
 }
 function choose(option:ResearchOption){setSelected(option);setName(option.name);setUrl(option.url||'');setNotes(option.details);setCost(option.estimated_cost_per_person?.toString()||'');setView('manual');setFit(null);setError('');}
 async function save(){
  if(!current)return;
  const website=url.trim()?publicWebUrl(url.trim()):undefined;
  if(url.trim()&&!website){setError('Use a public HTTP or HTTPS website link.');return;}
  const estimate=cost.trim()?Number(cost):undefined;
  if(estimate!==undefined&&(!Number.isFinite(estimate)||estimate<0||estimate>1000000)){setError('Enter a cost estimate between 0 and 1,000,000.');return;}
  const label=name.trim();if(!label){setError('Give this option a name.');return;}
  if(current.options.some(o=>o.label.toLowerCase()===label.toLowerCase())){setError('This option is already in the decision.');return;}
  const details:DecisionOptionDetails={label,notes:notes.trim(),...(website?{url:website}:{}),...(estimate!==undefined?{estimatedCostPerPerson:estimate}:{}),...(selected?.image?{image:selected.image}:{}),...(selected&&selected.provenance?{provenance:selected.provenance}:{}),sourceIds:selected?selected.source_ids.filter(id=>!id.startsWith('external:')):[]};
  try{if(!owner){await run({kind:'comment',decisionId:current.id,text:['Option suggestion: '+label,website,selected?.provenance?'Unverified source retrieved '+selected.provenance.retrievedAt:'',estimate!==undefined?'Unverified estimate per person: '+estimate:'',notes.trim()].filter(Boolean).join('\n').slice(0,2000)});notify('Suggestion shared in this decision’s comments. The owner can add it as a voting option.');onDone();return;}await run({kind:'edit',decisionId:current.id,options:[...current.options.map(o=>o.label),label],optionDetails:[...current.options.map(({id:_id,...o})=>{void _id;return o;}),details]});notify('Option added for group review. Earlier responses need to be renewed. Nothing is booked.');onDone();}
  catch(cause){setError(cause instanceof Error?cause.message:'The option could not be saved. Your draft is kept.');}
 }
 return <div className="option-workbench">
  <p>Find a real option or add one yourself, compare it with the group’s needs, then decide together.</p>
  <label className="field">Decision<select aria-label="Decision" value={current?.id||''} disabled={!!decisionId||pending||loading} onChange={e=>{setTarget(e.target.value);setFit(null);setSelected(null);setName('');setUrl('');setNotes('');setCost('');setError('');}}>{snapshot?.decisions.map(d=><option key={d.id} value={d.id}>{d.title}</option>)}</select></label>
  <div className="segmented"><button type="button" aria-pressed={view==='manual'} onClick={()=>setView('manual')}>Add your own</button><button type="button" aria-pressed={view==='research'} onClick={()=>setView('research')}>Find options</button></div>
  {view==='research'&&<section aria-label="Find options for your group">
   {mode==='demo'?<p>Live search and saved-source retrieval require a shared account. You can add a manual option in this demo.</p>:<form onSubmit={e=>{e.preventDefault();void search();}}>
    <label className="field">What are you looking for?<textarea required minLength={3} maxLength={250} value={query} onChange={e=>{setQuery(e.target.value);setSearching(null);}} placeholder={current?.category==='lodging'?'Hotels or rentals with room for our group':'What should we do in Austin during April?'}/></label>
    <label className="field">Search location<input required maxLength={150} value={location} onChange={e=>{setLocation(e.target.value);setSearching(null);}} placeholder="City or area"/></label>
    <p className="muted">Your query and relevant plan context are used for retrieval and external search. Website snippets and images need verification.</p>
    <Button disabled={searching||!user||!config?.connectedReady} type="submit">{searching?'Finding options…':'Search with group context'}</Button>
   </form>}
   {searching&&<p role="status">Reading group context and searching places. Execution details appear when the request completes.</p>}
   {displayed&&<ResearchResults result={displayed} disabled={!current||pending} onFit={setFit} onChoose={choose}/>}
  </section>}
  {view==='manual'&&<form onSubmit={e=>{e.preventDefault();void save();}}>
   <label className="field">Option name<input required maxLength={160} value={name} onChange={e=>{setName(e.target.value);setSelected(null);setFit(null);}} placeholder={current?.category==='lodging'?'Hotel or rental name':'Name of the option'}/></label>
   <label className="field">Website link<input type="url" maxLength={2048} value={url} onChange={e=>{setUrl(e.target.value);setSelected(null);setFit(null);}} placeholder="https://…"/></label>
   <label className="field">Estimated cost per person<input type="number" min="0" max="1000000" step="0.01" value={cost} onChange={e=>setCost(e.target.value)}/></label>
   <label className="field">Option notes<textarea maxLength={2000} value={notes} onChange={e=>setNotes(e.target.value)} placeholder="Rooms, dates, transport, dietary or accessibility details to check"/></label>
   <p className="muted">Estimates and notes are unverified. Owner changes to options reopen the decision and require new responses. Member suggestions are comments until the owner adds them. Nothing is booked.</p>
   <div className="option-actions"><Button variant="outline" type="button" disabled={!name.trim()||mode!=='connected'} onClick={()=>setFit({id:'manual',name:name.trim(),details:notes,url:publicWebUrl(url),estimated_cost_per_person:cost?Number(cost):null,source_ids:[]})}>Check group fit</Button><Button disabled={pending||!current||(owner&&current.options.length>=12)} type="submit">{owner?'Add to decision':'Suggest in comments'}</Button></div>
  </form>}
  {selected&&result&&result.key!==identity&&<p role="status">The group plan changed after this search. Your selected option and original source are kept. Review the current group needs before adding it.</p>}
  {!owner&&<p>Suggest an alternative in this decision’s comments. The owner adds voting options, and every member can respond.</p>}
  {(error||decisionError)&&<p role="alert">{error||decisionError}</p>}
  {fit&&<section className="option-fit-review"><Button variant="ghost" onClick={()=>setFit(null)}>Close fit check</Button><GroupFit key={fit.id} plan={plan} initialOption={{name:fit.name,details:fit.details,url:publicWebUrl(fit.url),...(fit.estimated_cost_per_person!=null?{estimated_cost_per_person:fit.estimated_cost_per_person}:{})}}/></section>}
 </div>;
}

export function FindOptionsButton({plan,decisionId,label='Find options',manual=false}:{plan:Plan;decisionId?:string;label?:string;manual?:boolean}){
 const [open,setOpen]=useState(false);
 return <><Button variant="outline" onClick={()=>setOpen(true)}>{label}</Button><Dialog open={open} onOpenChange={setOpen} title={manual?'Add an option':'Find options for your group'} description="Use group context, compare alternatives and propose a choice. People make the decision.">{open&&<OptionWorkbench plan={plan} decisionId={decisionId} initialMode={manual?'manual':'research'} onDone={()=>setOpen(false)}/>}</Dialog></>;
}

export function DecisionOptionActions({planId,decisionId,owner}:{planId:string;decisionId:string;owner:boolean}){
 const {plans}=usePlanning();const plan=plans.find(p=>p.id===planId);
 if(!plan)return null;
 return <>{owner&&<FindOptionsButton plan={plan} decisionId={decisionId} label="Add option" manual/>}<FindOptionsButton plan={plan} decisionId={decisionId}/></>;
}
