'use client';
import {useCallback,useEffect,useMemo,useRef,useState} from 'react';
import {ConnectedService,getAuth} from '@/services/connected';
import {DecisionService,type DecisionSnapshot,type DecisionCommand} from '@/services/decisions';
import {demoSnapshot,applyDemoDecision,demoMemberId} from '@/services/demo-decisions';
import type {Plan} from '@/services/types';
import {usePlanning} from '../store';

export function useDecisionSnapshot(plan:Plan){
 const {mode,config,user,workspaceRole,update,reload:reloadPlans}=usePlanning();
 const memberId=user?.id;
 const [snapshot,setSnapshot]=useState<DecisionSnapshot|null>(null);const [snapshotKey,setSnapshotKey]=useState('');
 const [loading,setLoading]=useState(false);const [pending,setPending]=useState(false);const [error,setError]=useState('');
 const key=plan.id+'|'+mode+'|'+(memberId||'demo')+'|'+workspaceRole;
 const currentKey=useRef(key);
 const actionLock=useRef(false);const sequence=useRef(0);
 const service=useMemo(()=>mode==='connected'&&config?new DecisionService(new ConnectedService(getAuth(config))):null,[mode,config]);
 const planRef=useRef(plan);
 const snapshotRef=useRef(snapshot);
 useEffect(()=>{currentKey.current=key;planRef.current=plan;snapshotRef.current=snapshot;},[key,plan,snapshot]);
 const reload=useCallback(async()=>{
  const captured=key;const request=++sequence.current;
  if(mode==='demo'){setSnapshot(demoSnapshot(planRef.current));setSnapshotKey(captured);setError('');return;}
  if(!service)return;
  setLoading(true);
  try{const result=await service.load(planRef.current.id,{memberId,isCurrent:()=>currentKey.current===captured});if(currentKey.current===captured&&sequence.current===request){setSnapshot(result);setSnapshotKey(captured);setError('');}}
  catch(e){if(currentKey.current===captured&&sequence.current===request){setSnapshot(null);setError(e instanceof Error?e.message:'Decisions are unavailable. Try again.');}}
  finally{if(currentKey.current===captured&&sequence.current===request)setLoading(false);}
 },[key,mode,service,memberId]);
 useEffect(()=>{
  queueMicrotask(()=>{if(currentKey.current===key)void reload();});
  const timer=setInterval(()=>{if(document.visibilityState==='visible'&&!actionLock.current)void reload();},10000);
  return()=>{currentKey.current='';clearInterval(timer);};
 },[reload,key,plan.revision,plan.decisionState,plan.members]);
 useEffect(()=>{actionLock.current=false;queueMicrotask(()=>{if(currentKey.current===key)setPending(false);});},[key]);
 const run=useCallback(async(command:DecisionCommand)=>{
  if(actionLock.current)throw new Error('A decision update is already in progress.');
  const before=mode==='demo'?demoSnapshot(planRef.current):snapshotRef.current;
  if(!before)throw new Error('Load the current decisions before making changes.');
  actionLock.current=true;setPending(true);setError('');const captured=key;sequence.current++;
  try{
   let result:DecisionSnapshot;
   if(mode==='demo'){
    result=applyDemoDecision(planRef.current,before,command,demoMemberId(planRef.current,0));
    await update(planRef.current.id,p=>({...p,decisionState:result}));
   }else{
    if(!service)throw new Error('The shared workspace is unavailable.');
    result=await service.execute(before,command,{memberId,isCurrent:()=>currentKey.current===captured});
    if(currentKey.current!==captured)return;
    await reloadPlans();
   }
   if(currentKey.current===captured){setSnapshot(result);setSnapshotKey(captured);}
  }catch(e){if(currentKey.current===captured){await reload();setError(e instanceof Error?e.message:'Could not update this decision.');}throw e;}
  finally{if(currentKey.current===captured){actionLock.current=false;setPending(false);}}
 },[key,mode,service,update,reloadPlans,reload,memberId]);
 const loadComments=useCallback(async(decisionId:string,offset=0)=>{
  const captured=key;
  const comments=mode==='demo'?(demoSnapshot(planRef.current).comments.filter(c=>c.decisionId===decisionId).slice(offset,offset+50))
   :await service!.comments(planRef.current.id,decisionId,offset,{memberId,isCurrent:()=>currentKey.current===captured});
  return captured===currentKey.current?comments:[];
 },[key,mode,service,memberId]);
 const summarize=useCallback(async(decisionId:string)=>{
  const captured=key;const before=snapshotRef.current;
  if(mode!=='connected'||!service||!before)throw new Error('AI summaries require a connected plan.');
  const result=await service.summarize(before,decisionId,{memberId,isCurrent:()=>currentKey.current===captured});
  if(currentKey.current!==captured||snapshotRef.current?.plan_revision!==result.planRevision)throw new Error('The plan changed. Refresh before reviewing this summary.');
  return result;
 },[key,mode,service,memberId]);
 const visibleSnapshot=snapshotKey===key?snapshot:null;
 // The decision endpoint can be newer than the independently polled plan list.
 // Only an older decision snapshot must wait; commands use its authoritative revision.
 const refreshing=!!visibleSnapshot&&mode==='connected'&&visibleSnapshot.plan_revision<(plan.revision??0);
 return {snapshot:visibleSnapshot,refreshing,loading,error,pending:pending||refreshing,run,reload,loadComments,summarize};
}
