'use client';
import {Plus,Users} from 'lucide-react';
import {usePlanning} from './store';

export function GroupPicker({groupId,onChange,onCreate,disabled=false}:{groupId:string;onChange:(id:string)=>void;onCreate:()=>void;disabled?:boolean}){
 const {groups,groupsReady,groupWarning,mode,reloadGroups,user}=usePlanning();
 const owned=groups.filter(g=>mode==='demo'||g.ownerId===user?.id);
 const selected=owned.find(g=>g.id===groupId&&!g.archived);
 return <>
  <label className="field"><span><Users size={15}/> Plan with a group</span><select aria-label="Plan with a group" value={groupId} disabled={!groupsReady||disabled||(mode==='connected'&&!user)} onChange={event=>onChange(event.target.value)}><option value="">{mode==='demo'?'Choose people just for this plan':'No saved group'}</option>{owned.filter(g=>!g.archived).map(g=><option key={g.id} value={g.id}>{g.name}</option>)}{groupId&&!selected&&<option value={groupId}>Group no longer available</option>}</select></label>
  {selected&&<div className="group-selection-summary"><strong>{selected.name}</strong><span>{selected.members.map(m=>m.preferredName).join(', ')}</span><small>{mode==='demo'?'These adults will be copied into this plan. No invitations are sent.':'Intended participants only. Creating this plan gives access to you; use Add member or a private join link to invite others explicitly.'}</small></div>}
  <div className="group-picker-actions">
   <button type="button" className="group-create-inline" disabled={!groupsReady||disabled||(mode==='connected'&&!user)} onClick={onCreate}><Plus size={15}/> Create a new group</button>
   {mode==='connected'&&<button type="button" className="text-button group-create-inline" disabled={disabled} onClick={()=>void reloadGroups()}>Refresh saved groups</button>}
  </div>
  {groupWarning&&<div className="group-storage-warning" role="alert">{groupWarning}{mode==='connected'&&<button type="button" className="text-button" onClick={()=>void reloadGroups()}>Retry loading groups</button>}</div>}
 </>;
}
