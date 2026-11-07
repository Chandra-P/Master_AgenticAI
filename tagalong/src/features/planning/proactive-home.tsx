'use client';
import {useCallback,useEffect,useState} from 'react';
import Link from 'next/link';
import {ArrowRight,Plus,Compass} from 'lucide-react';
import {Button} from '@/components/ui/button';
import type {Plan} from '@/services/types';
import type {DecisionSnapshot} from '@/services/decisions';
import {usePlanning} from './store';
import {CreatePlan} from './create-plan';
import {PlanGenerator,ideaExamples} from './plan-generator';
import {useDecisionSnapshot} from './decisions/use-decision-snapshot';
import {DecisionPlanCard} from './decisions/decision-plan-card';
import {NextStepCard} from './decisions/next-step-card';
import {homePlanModel} from './decisions/home-plan-model';
import {TravelMotif} from '@/components/travel-motif';

type Loaded={snapshot:DecisionSnapshot|null;error:string};
function HomeDecisionLoader({plan,onLoad}:{plan:Plan;onLoad:(id:string,value:Loaded)=>void}){
 const {snapshot,error}=useDecisionSnapshot(plan);
 useEffect(()=>{onLoad(plan.id,{snapshot,error});},[plan.id,snapshot,error,onLoad]);
 return null;
}
export function Dashboard(){const {user,mode,workspaceRole}=usePlanning();return <DecisionHome key={(user?.id||'demo')+mode+workspaceRole}/>;}
function DecisionHome(){
 const {plans,user,mode}=usePlanning();
 const [initialGroupId,setInitialGroupId]=useState('');
 const [create,setCreate]=useState(false);const [initialTitle,setInitialTitle]=useState('');
 const [filter,setFilter]=useState('All plans');const [idea,setIdea]=useState('');
 const [loaded,setLoaded]=useState<Record<string,Loaded>>({});
 const onLoad=useCallback((id:string,value:Loaded)=>setLoaded(current=>({...current,[id]:value})),[]);
 const memberId=mode==='demo'?'demo-member-0':user?.id||'';
 const attention=plans.flatMap(plan=>{const snapshot=loaded[plan.id]?.snapshot;return snapshot&&!snapshot.finalized?[{plan,snapshot,model:homePlanModel(plan,snapshot,memberId)}]:[];}).sort((a,b)=>a.model.priority-b.model.priority||(Date.parse(b.snapshot.last_activity_at||'')||0)-(Date.parse(a.snapshot.last_activity_at||'')||0));
 const displayed=plans.filter(plan=>filter==='Trips'?plan.kind==='trip':filter==='Outings'?plan.kind==='outing':true);
 const insights=[...new Set(plans.flatMap(plan=>plan.preferences.filter(p=>p.confirmed).map(p=>p.label)))];
 function manual(title:string,groupId=''){setInitialGroupId(groupId);setInitialTitle(title.slice(0,80));setCreate(true);}
 return <main className="dashboard coordination-home decision-home page-content">
 {plans.map(plan=><HomeDecisionLoader key={plan.id} plan={plan} onLoad={onLoad}/>)}
 <div className="home-greeting"><p>Hey {user?(user.display_name||'there'):'Alex'}, let’s make plans.</p><Button variant="outline" size="sm" onClick={()=>manual('')}><Plus size={16}/> Create a plan</Button></div>
 <section className="coordination-hero"><div className="hero-intro"><span className="eyebrow">FROM “WE SHOULD” TO “LET’S GO”</span><h1>Good company starts here.</h1><p className="hero-subtitle">Turn group chats into plans.</p><p className="decision-hero-description">Describe an idea in one sentence. Tagalong organizes decisions, gathers preferences, and helps your group move forward.</p><TravelMotif/></div>
 {mode==='connected'?<PlanGenerator onManual={manual}/>:<div className="plan-generator"><form onSubmit={event=>{event.preventDefault();manual(idea.trim());}}><label className="generator-label" htmlFor="demo-plan-idea">What would you like to do?</label><div className="generator-input"><textarea id="demo-plan-idea" aria-label="Describe your plan" required minLength={5} maxLength={2000} value={idea} onChange={event=>setIdea(event.target.value)} placeholder={ideaExamples[0]}/><Button type="submit">Start Planning <ArrowRight size={17}/></Button></div><div className="generator-examples">{ideaExamples.map(example=><button type="button" key={example} onClick={()=>setIdea(example)}>{example}</button>)}</div></form><p className="muted">Local demo · Review your idea and working details before creating a plan. No live AI or invitations.</p><button type="button" className="text-button generator-manual" onClick={()=>manual(idea)}>Create a plan manually</button></div>}
 </section>
 <section className="home-section" aria-labelledby="next-steps-heading"><div className="section-heading"><h2 id="next-steps-heading">Your next steps</h2><a className="text-button" href="#continue-planning">All actions <ArrowRight size={15}/></a></div><div className="decision-home-grid">{attention.slice(0,3).map(({plan,snapshot})=><NextStepCard key={plan.id} plan={plan} snapshot={snapshot} memberId={memberId}/>)}</div>{!attention.length&&<p className="home-empty">{plans.length?'Your decision actions will appear here as plans load. Open a plan to review its decisions.':'Start with an idea above. Your first plan and its next steps will appear here.'}</p>}</section>
 <section id="continue-planning" className="home-section"><div className="section-heading"><h2>Continue planning</h2><span className="number-badge">{plans.length}</span></div><div className="segmented">{['All plans','Trips','Outings'].map(value=><button type="button" aria-pressed={filter===value} className={filter===value?'selected':''} key={value} onClick={()=>setFilter(value)}>{value}</button>)}</div><div className="decision-home-grid">{displayed.map(plan=><DecisionPlanCard key={plan.id} plan={plan} snapshot={loaded[plan.id]?.snapshot||undefined} error={loaded[plan.id]?.error} memberId={memberId}/>)}</div>{!displayed.length&&<p className="home-empty">No {filter==='All plans'?'plans':filter.toLowerCase()} yet.</p>}</section>
 <details className="home-section decision-home-insights"><summary>Group Insights</summary><p>Based on explicitly confirmed preferences in plans you can access.</p><div className="insight-tags">{insights.length?insights.map(label=><span key={label}>{label}</span>):<p>No confirmed preferences yet.</p>}</div></details>
 <div className="discover-strip"><Compass size={21}/><span>From an idea to a shared experience.</span><Link href="/discover">Explore places <ArrowRight size={16}/></Link></div><CreatePlan key={initialTitle+String(create)} initialManual initialGroupId={initialGroupId} initialTitle={initialTitle} open={create} onOpenChange={setCreate}/>
 </main>;
}
