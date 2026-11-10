'use client';
import {avatarTextColor} from '@/lib/avatar-contrast';
import {useState} from 'react';
import {Check,Plus,Trash2,Users} from 'lucide-react';
import type {Group,GroupMember} from '@/services/types';
import {groupThemes,members as demoMembers} from '@/services/demo-data';
import {groupOwner,suggestGroupName} from '@/services/group-service';
import {Button} from '@/components/ui/button';
import {usePlanning} from './store';

export function GroupEditor({group,onSaved,onCancel}:{group?:Group;onSaved:(group:Group)=>void;onCancel:()=>void}) {
 const {groups,groupsReady,groupWarning,saveGroup,mode,user}=usePlanning();
 const owner=mode==='demo'?groupOwner:{id:user!.id,preferredName:(user!.display_name||user!.name).slice(0,40),color:groupOwner.color};
 const [saving,setSaving]=useState(false);
 const [theme,setTheme]=useState(group?(groupThemes.includes(group.theme)?group.theme:'Custom'):groupThemes[0]);
 const [customTheme,setCustomTheme]=useState(group&&!groupThemes.includes(group.theme)?group.theme:'');
 const [name,setName]=useState(group?.name??suggestGroupName(groupThemes[0],groups,owner.preferredName));
 const [editedName,setEditedName]=useState(!!group);
 const [members,setMembers]=useState<GroupMember[]>(()=>group?structuredClone(group.members).map(m=>m.id===owner.id?{...m,preferredName:owner.preferredName}:m):[{...owner}]);
 const [error,setError]=useState('');
 const effectiveTheme=theme==='Custom'?customTheme:theme;
 function changeTheme(value:string,custom=customTheme){setTheme(value);if(!editedName)setName(suggestGroupName(value==='Custom'?custom||'Our group':value,groups,owner.preferredName));}
 function changeMember(id:string,field:'preferredName'|'email'|'firstName'|'lastName',value:string){setMembers(old=>old.map(m=>m.id===id?{...m,[field]:value}:m));}
 return <form className="group-editor" noValidate onSubmit={async event=>{
  event.preventDefault();
  if(saving)return;setSaving(true);setError('');
  try{const result=await saveGroup({name,theme:effectiveTheme,members},group?.id,group?.revision);if(result.error){setError(result.error);return;}onSaved(result.group!);}
  catch(cause){setError(cause instanceof Error?cause.message:'Could not save your group.');}
  finally{setSaving(false);}
 }}>
  <fieldset className="group-editor-fields" disabled={saving}><div className="group-editor-note"><Users size={17}/><span>Good company, ready for the next plan. Adult aliases only; no children’s names or photos.</span></div>
  <fieldset className="group-theme-field"><legend>Group theme</legend><div className="group-theme-options">{[...groupThemes,'Custom'].map(value=><button type="button" key={value} aria-pressed={theme===value} className={theme===value?'selected':''} onClick={()=>changeTheme(value)}>{value}</button>)}</div></fieldset>
  {theme==='Custom'&&<label className="field">Custom theme<input autoFocus maxLength={60} value={customTheme} onChange={e=>{setCustomTheme(e.target.value);changeTheme('Custom',e.target.value);}} placeholder="e.g. Board game nights"/></label>}
  <label className="field">Group name<input aria-label="Group name" aria-describedby="group-name-help" autoFocus={theme!=='Custom'} maxLength={80} value={name} onChange={e=>{setName(e.target.value);setEditedName(true);}}/><small id="group-name-help">Suggested from your theme. Make it memorable and unique in your space.</small></label>
  <div className="group-owner"><span className="avatar" style={{background:owner.color,color:avatarTextColor(owner.color)}}>{owner.preferredName.slice(0,2).toUpperCase()}</span><div><strong>{owner.preferredName}</strong><small>You · Group owner</small></div><span className="status mint">Always included</span></div>
  <div className="group-members-heading"><h3>Bring your people</h3><span>{members.length-1} / 12 adults added</span></div>
  {members.filter(m=>m.id!==owner.id).map((member,index)=><fieldset className="group-member-row" key={member.id}><legend>Adult {index+1}</legend><div className="group-member-top"><label className="field">Preferred name / alias<input maxLength={40} value={member.preferredName} onChange={e=>changeMember(member.id,'preferredName',e.target.value)} placeholder="e.g. Maya"/></label><button type="button" className="icon-button" aria-label={'Remove adult '+(index+1)} onClick={()=>setMembers(old=>old.filter(m=>m.id!==member.id))}><Trash2 size={16}/></button></div><label className="field">Email (optional)<input type="email" autoComplete="off" maxLength={254} value={member.email??''} onChange={e=>changeMember(member.id,'email',e.target.value)} placeholder="maya@example.test"/></label><details><summary>More details (optional)</summary><div className="field-row"><label className="field">First name<input maxLength={40} value={member.firstName??''} onChange={e=>changeMember(member.id,'firstName',e.target.value)}/></label><label className="field">Last name<input maxLength={40} value={member.lastName??''} onChange={e=>changeMember(member.id,'lastName',e.target.value)}/></label></div></details></fieldset>)}
  <Button type="button" variant="outline" size="sm" disabled={members.length>=13} onClick={()=>setMembers(old=>[...old,{id:crypto.randomUUID(),preferredName:'',color:demoMembers[old.length%demoMembers.length].color}])}><Plus size={15}/> Add adult</Button>
  <p className="group-privacy-note">{mode==='demo'?'Email is optional and stays in this browser. Creating a group sends no invitations. Use synthetic details for this demo.':group?.shared?'This group is shared. Saving member emails updates who can view its name, theme and aliases through a matching verified account. Contact details stay private to you. No messages are sent and no plan access is granted.':'Contact details stay private to you. After saving, open the group card and choose Share with members to let matching verified accounts view the group. Adding a contact sends no invitation and grants no plan access.'}</p>
  {error&&<p className="group-error" role="alert">{error}</p>}
  {groupWarning&&<p className="group-storage-warning" role="alert">{groupWarning}</p>}
  </fieldset><div className="group-form-actions"><Button type="button" variant="outline" disabled={saving} onClick={onCancel}>Cancel</Button><Button type="submit" disabled={!groupsReady||saving}><Check size={16}/>{saving?'Saving…':group?'Save group':'Create group'}</Button></div>
 </form>;
}
