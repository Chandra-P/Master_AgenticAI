'use client';
import {useEffect,useState} from 'react';
import type {Group} from '@/services/types';
import {Button} from '@/components/ui/button';
import {usePlanning} from './store';

/** Mounted only in the connected workspace. Always read fresh authorized details. */
export function GroupDetails({id,onEdit}:{id:string;onEdit:(group:Group)=>void}){
 const {readGroup,setGroupSharing,reloadGroups,busy}=usePlanning();
 const [group,setGroup]=useState<Group|null>(null);
 const [error,setError]=useState('');
 const [saving,setSaving]=useState(false);
 useEffect(()=>{
  let active=true,request=0;
  async function refresh(){
   const current=++request;
   try{const next=await readGroup(id);if(active&&current===request){setGroup(previous=>previous&&(previous.revision??0)>(next.revision??0)?previous:next);setError('');}}
   catch(cause){if(active&&current===request){setGroup(null);setError(cause instanceof Error?cause.message:'This group is unavailable.');void reloadGroups();}}
  }
  void refresh();
  const focus=()=>{setGroup(null);void refresh();};
  const timer=setInterval(()=>{if(document.visibilityState==='visible')void refresh();},15000);
  window.addEventListener('focus',focus);
  return()=>{active=false;++request;clearInterval(timer);window.removeEventListener('focus',focus);};
 },[id,readGroup,reloadGroups]);
 if(!group)return error?<p className="group-error" role="alert">{error}</p>:<p role="status">Loading group details…</p>;
 const owner=group.role==='owner';
 return <div className="group-details">
  <span className="group-theme-label">{group.theme}</span>
  <h3>{group.name}</h3>
  <p className="muted">Owner: {group.ownerName} · {group.archived?'Archived':'Active'} · {owner?'Your group':'Shared with you · View only'}</p>
  <h4>Adults in this group</h4>
  <ul className="group-details-members">{group.members.map(member=><li key={member.id}><strong>{member.preferredName}</strong>{member.id===group.ownerId&&<span className="status mint">Owner</span>}{owner&&member.email&&<span className="muted">{member.email}</span>}</li>)}</ul>
  <p className="group-privacy-note">Viewing this group does not give access to its plans. Emails and legal names stay private to the owner.</p>
  {owner&&<div className="group-sharing">
   <h4>{group.shared?'Shared with members':'Private group'}</h4>
   <p>Sharing lets people whose verified account email matches an added adult’s email see this name, theme and adult aliases. No messages are sent. Adults without an email cannot receive access.</p>
   {group.shared&&<p>Saving changes to this roster updates who can view the group. Stop sharing to make it private again.</p>}
   {error&&<p className="group-error" role="alert">{error}</p>}
   <div className="group-form-actions"><Button variant="outline" disabled={busy||saving} onClick={()=>onEdit(group)}>Edit group</Button><Button disabled={busy||saving} onClick={async()=>{
    setSaving(true);setError('');
    try{setGroup(await setGroupSharing(group.id,!group.shared,group.revision));}
    catch(cause){setGroup(null);setError(cause instanceof Error?cause.message:'Could not update sharing.');}
    finally{setSaving(false);}
   }}>{saving?'Saving…':group.shared?'Stop sharing':'Share with members'}</Button></div>
  </div>}
 </div>;
}
