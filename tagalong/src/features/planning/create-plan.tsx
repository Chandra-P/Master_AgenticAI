'use client';
import {useState} from 'react';
import {useRouter} from 'next/navigation';
import {ArrowRight,Sun,Backpack,Users,CalendarDays} from 'lucide-react';
import {Dialog} from '@/components/ui/dialog';
import {Button} from '@/components/ui/button';
import {usePlanning} from './store';
import {PlanGenerator} from './plan-generator';
import {GroupPicker} from './group-picker';
import {GroupEditor} from './group-editor';
import type {PlanKind} from '@/services/types';

function ManualCreatePlan({open,onOpenChange,initialGroupId='',onGroupChange}:{open:boolean;onOpenChange:(open:boolean)=>void;initialGroupId?:string;onGroupChange?:(id:string)=>void}) {
 const {groups,groupsReady,create,notify,mode,busy}=usePlanning();
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
 {creatingGroup?<GroupEditor onCancel={()=>setCreatingGroup(false)} onSaved={group=>{setGroupId(group.id);onGroupChange?.(group.id);setCreatingGroup(false);}}/>:<form onSubmit={async e=>{
  e.preventDefault();if(!title.trim())return;
  try{
   const id=await create({kind,title,start,end:kind==='outing'?start:end,participants,groupId:groupId||undefined,expectedGroupRevision:mode==='connected'?selectedGroup?.revision:undefined});
   onOpenChange(false);notify(mode==='demo'?'Your demo plan is ready. Let’s make memories.':'Your shared plan is ready.');router.push('/plans/'+id);
  }catch(cause){setError(cause instanceof Error?cause.message:'Your plan could not be created.');}
 }}>
  <div className="type-options"><button type="button" aria-label="Outing" aria-pressed={kind==='outing'} className={kind==='outing'?'selected':''} onClick={()=>setKind('outing')}><Sun/><strong>Outing</strong><span>A few hours, a good time</span></button><button type="button" aria-label="Trip" aria-pressed={kind==='trip'} className={kind==='trip'?'selected':''} onClick={()=>setKind('trip')}><Backpack/><strong>Trip</strong><span>A little further together</span></button></div>
  <label className="field">Plan name<input autoFocus required maxLength={80} value={title} onChange={e=>setTitle(e.target.value)} placeholder="e.g. A weekend by the coast"/></label>
  <div className="field-row"><label className="field"><span><CalendarDays size={15}/> Start date</span><input aria-label="Start date" type="date" value={start} onChange={e=>{setStart(e.target.value);if(end&&end<e.target.value)setEnd(e.target.value);}}/></label>{kind==='trip'&&<label className="field">End date<input aria-label="End date" type="date" min={start} value={end} onChange={e=>setEnd(e.target.value)}/></label>}</div>
  <GroupPicker groupId={groupId} onChange={id=>{setGroupId(id);onGroupChange?.(id);setError('');}} onCreate={()=>setCreatingGroup(true)} disabled={busy}/>
  {mode==='demo'&&!groupId&&<label className="field"><span><Users size={15}/> Invite participants</span><input value={participants} onChange={e=>setParticipants(e.target.value)} placeholder="Maya, Sam, Jordan"/><small>Separate names with commas. Demo only — no invitations are sent.</small></label>}
  {error&&<p className="group-error" role="alert">{error}</p>}
  <Button className="full" type="submit" disabled={busy||(!!groupId&&(!groupsReady||!selectedGroup))}>{mode==='demo'?'Create demo plan':'Create shared plan'} <ArrowRight size={17}/></Button>
 </form>}
 </Dialog>;
}

function CreatePlanFlow({open,onOpenChange,initialGroupId=''}:{open:boolean;onOpenChange:(open:boolean)=>void;initialGroupId?:string}){
 const {mode}=usePlanning();const [manual,setManual]=useState(false);const [groupId,setGroupId]=useState(initialGroupId);
 if(mode==='demo'||manual)return <ManualCreatePlan open={open} initialGroupId={groupId} onGroupChange={setGroupId} onOpenChange={value=>{onOpenChange(value);if(!value)setManual(false);}}/>;
 return <Dialog open={open} onOpenChange={onOpenChange} title="Good company starts here." description="Describe an outing or trip. Tagalong helps your group figure out the rest."><PlanGenerator groupId={groupId} onGroupChange={setGroupId} onCreated={()=>onOpenChange(false)}/><button type="button" className="text-button generator-manual" onClick={()=>setManual(true)}>Create a plan manually</button></Dialog>;
}
export function CreatePlan(props:{open:boolean;onOpenChange:(open:boolean)=>void;initialGroupId?:string}){
 const {mode,user}=usePlanning();return <CreatePlanFlow key={mode+'-'+(user?.id||'demo')} {...props}/>;
}
