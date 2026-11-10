'use client';
import {useEffect,useRef,useState} from 'react';
import type {Plan} from '@/services/types';
import {ConnectedService,getAuth} from '@/services/connected';
import {Button} from '@/components/ui/button';
import {usePlanning} from './store';
import {PlanShareReview} from './plan-share-review';
import './plan-sharing.css';

interface Recipients {plan_revision:number;recipients:{id:string;alias:string;status:'pending'|'claimed'|'revoked'}[]}
export function PlanGroupSharing({plan}:{plan:Plan}){
 const {groups,user,config,reload,reloadGroups}=usePlanning();
 const [groupId,setGroupId]=useState('');const [approval,setApproval]=useState('');
 const [data,setData]=useState<Recipients|null>(null);const [error,setError]=useState('');const [busy,setBusy]=useState(false);
 const live=useRef(false);const userId=user?.id;
 const owned=groups.filter(g=>g.ownerId===user?.id&&!g.archived);
 const selected=owned.find(g=>g.id===groupId);const key=selected?selected.id+':'+selected.revision:'';
 useEffect(()=>{
  live.current=true;void reloadGroups();
  if(config&&userId){const api=new ConnectedService(getAuth(config));void api.request<Recipients>('/v1/plans/'+encodeURIComponent(plan.id)+'/group-sharing',{}, {userId:userId,isCurrent:()=>live.current}).then(next=>{if(live.current)setData(next);}).catch(cause=>{if(live.current)setError(cause instanceof Error?cause.message:'Could not load recipients.');});}
  return()=>{live.current=false;};
 },[config,userId,plan.id,reloadGroups]); // Account-scoped by the parent key.
 async function change(path:string,body:object,method='POST'){
  if(!config||!user)return;setBusy(true);setError('');
  const api=new ConnectedService(getAuth(config));const scope={userId:userId,isCurrent:()=>live.current};
  try{
   await api.request(path,{method,body:JSON.stringify(body)},scope);
   if(!live.current)return;
   setApproval('');await reload();
   const next=await api.request<Recipients>('/v1/plans/'+encodeURIComponent(plan.id)+'/group-sharing',{},scope);
   if(live.current)setData(next);
  }catch(cause){if(live.current){setError(cause instanceof Error?cause.message:'Could not update sharing.');await reload();}}
  finally{if(live.current)setBusy(false);}
 }
 return <section className="plan-group-sharing" aria-label="Share with group">
  <h3>Share with group</h3><p>Approve a group’s current recipients for this plan. Earlier group snapshots and other plans stay unchanged.</p>
  <label className="field"><span>Group to share with</span><select aria-label="Group to share with" value={groupId} disabled={busy} onChange={e=>{setGroupId(e.target.value);setApproval('');}}><option value="">Choose an owned group</option>{owned.map(g=><option key={g.id} value={g.id}>{g.name}</option>)}</select></label>
  {selected&&<PlanShareReview group={selected} checked={!!key&&approval===key} onChange={value=>setApproval(value?key:'')} disabled={busy}/>}
  <Button variant="outline" disabled={busy||!key||approval!==key} onClick={()=>void change('/v1/plans/'+encodeURIComponent(plan.id)+'/group-sharing',{group_id:selected!.id,expected_group_revision:selected!.revision,expected_revision:plan.revision,share_with_group:true})}>Share plan with group</Button>
  {data&&data.recipients.length>0&&<><h4>Approved group recipients</h4><ul className="plan-recipient-list">{data.recipients.map(recipient=><li key={recipient.id}><span>{recipient.alias} · {recipient.status==='pending'?'Waiting for verified sign-in / refresh':recipient.status==='claimed'?'Already a plan member':'Access approval revoked'}</span>{recipient.status==='pending'&&<Button variant="outline" size="sm" disabled={busy} aria-label={'Revoke pending access for '+recipient.alias} onClick={()=>void change('/v1/plans/'+encodeURIComponent(plan.id)+'/group-sharing/'+encodeURIComponent(recipient.id),{expected_revision:data.plan_revision},'DELETE')}>Revoke</Button>}</li>)}</ul></>}
  {error&&<p className="group-error" role="alert">{error}</p>}
 </section>;
}
