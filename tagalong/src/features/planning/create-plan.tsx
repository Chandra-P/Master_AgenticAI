'use client';
import {useState} from 'react';
import {useRouter} from 'next/navigation';
import {ArrowRight,Sun,Backpack,Users,CalendarDays,Plus} from 'lucide-react';
import {Dialog} from '@/components/ui/dialog';
import {Button} from '@/components/ui/button';
import {usePlanning} from './store';
import {GroupEditor} from './group-editor';
import type {PlanKind} from '@/services/types';

export function CreatePlan({open,onOpenChange,initialGroupId=''}:{open:boolean;onOpenChange:(open:boolean)=>void;initialGroupId?:string}) {
 const {groups,groupsReady,groupWarning,create,notify}=usePlanning();
 const router=useRouter();
 const [kind,setKind]=useState<PlanKind>('outing');
 const [title,setTitle]=useState('');
 const [start,setStart]=useState('');
 const [end,setEnd]=useState('');
 const [participants,setParticipants]=useState('');
 const [groupId,setGroupId]=useState(initialGroupId);
 const [creatingGroup,setCreatingGroup]=useState(false);
 const [error,setError]=useState('');
 const selectedGroup=groups.find(g=>g.id===groupId&&!g.archived);
 return <Dialog open={open} onOpenChange={value=>{if(!value)setCreatingGroup(false);onOpenChange(value);}} title={creatingGroup?'Your people, together.':'Good company starts here.'} description={creatingGroup?'Create a reusable demo group, then return to your plan.':'A little outing or a big adventure. Make room for both.'}>
 {creatingGroup?<GroupEditor onCancel={()=>setCreatingGroup(false)} onSaved={group=>{setGroupId(group.id);setCreatingGroup(false);}}/>:<form onSubmit={e=>{
  e.preventDefault();if(!title.trim())return;
  try{
   const id=create({kind,title,start,end:kind==='outing'?start:end,participants,groupId:groupId||undefined});
   onOpenChange(false);notify('Your demo plan is ready. Let’s make memories.');router.push('/plans/'+id);
  }catch(cause){setError(cause instanceof Error?cause.message:'Your plan could not be created.');}
 }}>
  <div className="type-options"><button type="button" aria-label="Outing" className={kind==='outing'?'selected':''} onClick={()=>setKind('outing')}><Sun/><strong>Outing</strong><span>A few hours, a good time</span></button><button type="button" aria-label="Trip" className={kind==='trip'?'selected':''} onClick={()=>setKind('trip')}><Backpack/><strong>Trip</strong><span>A little further together</span></button></div>
  <label className="field">Plan name<input autoFocus required maxLength={80} value={title} onChange={e=>setTitle(e.target.value)} placeholder="e.g. A weekend by the coast"/></label>
  <div className="field-row"><label className="field"><span><CalendarDays size={15}/> Start date</span><input aria-label="Start date" type="date" value={start} onChange={e=>{setStart(e.target.value);if(end&&end<e.target.value)setEnd(e.target.value);}}/></label>{kind==='trip'&&<label className="field">End date<input aria-label="End date" type="date" min={start} value={end} onChange={e=>setEnd(e.target.value)}/></label>}</div>
  <label className="field"><span><Users size={15}/> Plan with a group</span><select aria-label="Plan with a group" value={groupId} disabled={!groupsReady} onChange={e=>{setGroupId(e.target.value);setError('');}}><option value="">Choose people just for this plan</option>{groups.filter(g=>!g.archived).map(g=><option key={g.id} value={g.id}>{g.name}</option>)}{groupId&&!selectedGroup&&<option value={groupId}>Group no longer available</option>}</select></label>
  {selectedGroup?<div className="group-selection-summary"><strong>{selectedGroup.name}</strong><span>{selectedGroup.members.map(m=>m.preferredName).join(', ')}</span><small>These adults will be copied into this plan. No invitations are sent.</small></div>:!groupId&&<label className="field"><span><Users size={15}/> Invite participants</span><input value={participants} onChange={e=>setParticipants(e.target.value)} placeholder="Maya, Sam, Jordan"/><small>Separate names with commas. Demo only — no invitations are sent.</small></label>}
  <button type="button" className="group-create-inline" disabled={!groupsReady} onClick={()=>setCreatingGroup(true)}><Plus size={15}/> Create a new group</button>
  {groupWarning&&<p className="group-storage-warning" role="alert">{groupWarning}</p>}
  {error&&<p className="group-error" role="alert">{error}</p>}
  <Button className="full" type="submit" disabled={!!groupId&&(!groupsReady||!selectedGroup)}>Create demo plan <ArrowRight size={17}/></Button>
 </form>}
 </Dialog>;
}
