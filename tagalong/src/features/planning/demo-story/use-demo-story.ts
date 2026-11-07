'use client';
import {useEffect,useState} from 'react';
import {ApiError,ConnectedService,getAuth} from '@/services/connected';
import {DemoPlanService,type DemoStory} from '@/services/demo-plan';
import type {Plan} from '@/services/types';
import {usePlanning} from '../store';

/** Read only, account scoped, and cancelled whenever this plan or session leaves view. */
export function useDemoStory(plan:Plan){
 const {mode,config,user,workspaceRole}=usePlanning();
 const userId=user?.id,planId=plan.id,template=plan.demo_template;
 const supabaseUrl=config?.supabaseUrl||'',supabaseAnonKey=config?.supabaseAnonKey||'',connectedReady=!!config?.connectedReady;
 const enabled=mode==='connected'&&template==='austin-four-friends'&&!!userId&&connectedReady;
 const identity=[mode,userId,workspaceRole,planId,template].join('|');
 const [record,setRecord]=useState<{identity:string;story:DemoStory|null;error:string;loading:boolean}|null>(null);
 const [retry,setRetry]=useState(0);
 useEffect(()=>{
  if(!enabled||!userId)return;
  let active=true;const controller=new AbortController();
  queueMicrotask(()=>{if(active)setRecord({identity,story:null,error:'',loading:true});});
  const api=new ConnectedService(getAuth({supabaseUrl,supabaseAnonKey,connectedReady}));
  void new DemoPlanService(api).story(planId,{userId,isCurrent:()=>active},controller.signal).then(story=>{
   if(active&&story.planId===planId&&story.template==='austin-four-friends')setRecord({identity,story,error:'',loading:false});
   else if(active)setRecord({identity,story:null,error:'The saved demo does not match this plan. Reload to try again.',loading:false});
  }).catch(cause=>{if(active&&!controller.signal.aborted)setRecord({identity,story:null,error:cause instanceof ApiError&&cause.status===404?'The saved demo is unavailable for this account.':cause instanceof Error?cause.message:'Could not load the saved group decisions.',loading:false});});
  return()=>{active=false;controller.abort();};
 },[enabled,userId,planId,identity,supabaseUrl,supabaseAnonKey,connectedReady,retry]);
 const visible=enabled&&record?.identity===identity?record:null;
 return {story:visible?.story||null,error:visible?.error||'',loading:enabled&&(!visible||visible.loading),reload:()=>setRetry(value=>value+1)};
}
