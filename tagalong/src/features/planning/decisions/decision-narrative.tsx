'use client';
import {useEffect,useMemo,useState} from 'react';
import type {Plan} from '@/services/types';
import {ConnectedService,getAuth} from '@/services/connected';
import {CoordinationService,type Coordination} from '@/services/coordination';
import {usePlanning} from '../store';
export function DecisionNarrative({plan}:{plan:Plan}){
 const {mode,config,user,workspaceRole}=usePlanning();const [cached,setCached]=useState<{key:string;record:Coordination}|null>(null);
 const key=[mode,user?.id,workspaceRole,plan.id,plan.revision].join('|');const record=cached?.key===key?cached.record:null;
 const api=useMemo(()=>mode==='connected'&&config?new CoordinationService(new ConnectedService(getAuth(config))):null,[mode,config]);
 useEffect(()=>{let active=true;if(!api)return;async function load(){try{const result=await api!.plan(plan.id);if(active)setCached({key,record:result});}catch{if(active)setCached(null);}}void load();const timer=setInterval(()=>{if(document.visibilityState==='visible')void load();},10000);return()=>{active=false;clearInterval(timer);};},[api,plan.id,key]);
 const current=mode==='connected'&&record?.plan_id===plan.id&&record?.plan_revision===plan.revision;const live=current&&record?.provider_status==='live'&&!record.stale;
 return <section className="decision-narrative"><h2>{live?'AI Summary':'Plan summary'}</h2>{live?<><p>{record.summary}</p><small>Generated {record.generated_at?new Date(record.generated_at).toLocaleString():'time unavailable'} · plan revision {record.plan_revision}</small><p><a href="#decision-evidence">Review decision evidence below</a></p></>:<p>{record&&(!current||record.stale)?'Summary needs refresh. Current decision evidence is shown below.':'AI summary unavailable. People confirm decisions; working details are proposals.'}</p>}</section>;
}
