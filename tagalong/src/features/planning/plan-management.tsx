'use client';
import {useState} from 'react';
import {useRouter} from 'next/navigation';
import type {Plan} from '@/services/types';
import {usePlanning} from './store';
import {Button} from '@/components/ui/button';
import {Dialog} from '@/components/ui/dialog';

export function PlanManagement({plan}:{plan:Plan}){
 const {deletePlan,transferOwner,busy}=usePlanning();const router=useRouter();
 const [action,setAction]=useState<'delete'|'transfer'|null>(null);const [confirmation,setConfirmation]=useState('');const [target,setTarget]=useState('');const [error,setError]=useState('');
 const members=plan.members.filter(m=>m.user_id&&m.user_id!==plan.owner_id);
 if(plan.role!=='owner')return null;
 function open(value:'delete'|'transfer'){setConfirmation('');setTarget('');setError('');setAction(value);}
 async function submit(e:React.FormEvent){e.preventDefault();setError('');try{if(action==='delete'){await deletePlan(plan.id,confirmation);router.push('/');}else if(action==='transfer'){await transferOwner(plan.id,target);}setAction(null);}catch(e){setError(e instanceof Error?e.message:'Could not change the plan.');}}
 return <div className="plan-management"><Button variant="outline" size="sm" onClick={()=>open('transfer')}>Transfer ownership</Button><Button variant="outline" size="sm" onClick={()=>open('delete')}>Delete plan</Button><Dialog open={action!==null} onOpenChange={value=>{if(!value&&!busy)setAction(null);}} title={action==='delete'?'Delete this plan?':'Transfer plan ownership'} description={action==='delete'?'This removes the plan from all member workspaces, disables its invitation link and queues removal of search vectors. Records are retained for admin review; this is not permanent erasure.':'Choose an existing member as the new owner. You will remain a member and lose owner controls. The old invitation link will stop working.'}><form onSubmit={e=>void submit(e)}>{action==='delete'?<label className="field">Type the plan name to confirm: {plan.title}<input aria-label="Plan name confirmation" required maxLength={200} value={confirmation} onChange={e=>setConfirmation(e.target.value)}/></label>:<><label className="field">New plan owner<select required value={target} onChange={e=>setTarget(e.target.value)}><option value="">Choose a member</option>{members.map(m=><option key={m.user_id} value={m.user_id}>{m.name}</option>)}</select></label>{members.length===0&&<p>Add another member before transferring ownership.</p>}</>}{error&&<p role="alert">{error}</p>}<Button type="submit" disabled={busy||(action==='delete'?confirmation!==plan.title:!target)}>{busy?'Saving…':action==='delete'?'Confirm delete plan':'Confirm transfer ownership'}</Button><Button type="button" variant="outline" disabled={busy} onClick={()=>setAction(null)}>Cancel</Button></form></Dialog></div>;
}
