'use client';
import type {Group} from '@/services/types';
export function PlanShareReview({group,checked,onChange,disabled=false}:{group:Group;checked:boolean;onChange:(value:boolean)=>void;disabled?:boolean}){
 const adults=group.members.filter(m=>m.id!==group.ownerId);
 const recipients=adults.filter(m=>m.email);
 const missing=adults.filter(m=>!m.email);
 return <div className="plan-share-review">
  <label><input type="checkbox" checked={checked} disabled={disabled||!recipients.length} onChange={e=>onChange(e.target.checked)}/> Share this plan with group members</label>
  <p>Review these recipients. Matching verified accounts can view, chat and vote, and receive an in-app notification on their next sign-in or refresh. No email is sent.</p>
  {recipients.length?<ul>{recipients.map(m=><li key={m.id}>{m.preferredName} <span className="muted">({m.email})</span></li>)}</ul>:<p>Add an adult’s account email to the group before sharing.</p>}
  {!!missing.length&&<p>Cannot receive automatic access — no account email: {missing.map(m=>m.preferredName).join(', ')}.</p>}
 </div>;
}
