'use client';
import {useEffect,useMemo,useState} from 'react';
import {Sparkles,ArrowRight} from 'lucide-react';
import {usePlanning} from './store';
import {ConnectedService,getAuth} from '@/services/connected';
import {CoordinationService,statusLabel,type Coordination} from '@/services/coordination';
import type {Plan,Tab} from '@/services/types';
import {Button} from '@/components/ui/button';

export function CoordinationCard({plan,onTab}:{plan:Plan;onTab:(tab:Tab)=>void}){
 const {config,mode}=usePlanning();const [record,setData]=useState<Coordination|null>(null);const [error,setError]=useState('');
 const data=record?.plan_revision===plan.revision?record:null;
 const api=useMemo(()=>config&&mode==='connected'?new CoordinationService(new ConnectedService(getAuth(config))):null,[config,mode]);
 useEffect(()=>{if(!api)return;let active=true;let loading=false;async function load(){if(loading)return;loading=true;try{const result=await api!.plan(plan.id);if(active){setData(result);setError('');}}catch(e){if(active){setError(e instanceof Error?e.message:'Coordination is temporarily unavailable.');setData(null);}}finally{loading=false;}}void load();const timer=setInterval(()=>{if(document.visibilityState==='visible')void load();},10000);return()=>{active=false;clearInterval(timer);};},[api,plan.id,plan.revision]);
 if(mode!=='connected')return null;
 return <section className="coordination-card" aria-label="Plan coordination"><div className="coordination-heading"><span className="eyebrow"><Sparkles size={14}/> YOUR PLANNING SIDEKICK</span>{data&&<span className={'coord-status '+(data.status==='STALLED'?'stalled':'')}>{statusLabel(data.status)}</span>}</div>{data?<><div className="coordination-columns"><div><h2>Everyone on the same page.</h2><p>{data.summary}</p><small>{data.provider_status==='live'&&!data.stale?'AI summary · review before treating it as a decision':data.provider_status==='unavailable'?'AI summary unavailable · showing current plan facts':'AI summary is being prepared · current facts shown'}</small>{data.decisions_made.length>0&&<><h3>Confirmed preferences</h3><ul>{data.decisions_made.map(x=><li key={x}>{x}</li>)}</ul></>}{data.open_questions.length>0&&<><h3>Open questions</h3><ul>{data.open_questions.slice(0,5).map(x=><li key={x}>{x}</li>)}</ul></>}</div><aside><span className="eyebrow">NEXT BEST STEP</span><h3>{data.next_step}</h3><p>{data.reason}</p>{data.ai_next_step&&data.ai_next_step!==data.next_step&&<p>Also suggested: {data.ai_next_step}</p>}<Button variant="outline" onClick={()=>onTab(data.target_tab as Tab)}>{data.status==='STALLED'?'Resume Planning':'Take the next step'} <ArrowRight size={14}/></Button><div className="coord-progress"><span style={{width:data.health+'%'}}/></div><small>Planning progress {data.health}/100 · based on recorded details, votes and tasks.</small></aside></div></>:<p>Checking your plan for blockers and next steps…</p>}{error&&<p role="status">{error}</p>}<p className="coordination-disclosure">Tagalong uses plan messages, polls and documents to draft summaries and recommendations automatically while you use the app. People confirm decisions.</p></section>;
}
