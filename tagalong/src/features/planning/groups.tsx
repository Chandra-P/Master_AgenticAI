'use client';
import {useRef,useState} from 'react';
import {Archive,ArrowRight,Heart,Plus,Sparkles,Trash2,Users,Utensils,Mountain,Pencil,RotateCcw} from 'lucide-react';
import type {Group} from '@/services/types';
import {Button} from '@/components/ui/button';
import {Dialog} from '@/components/ui/dialog';
import {usePlanning} from './store';
import {Avatars} from './shared';
import {GroupEditor} from './group-editor';
import {CreatePlan} from './create-plan';

export function Groups(){
 const {groups,groupsReady,groupWarning,archiveGroup,removeGroup}=usePlanning();
 const returnFocus=useRef<HTMLButtonElement|null>(null);
 const [filter,setFilter]=useState<'Active'|'Archived'>('Active');
 const [editing,setEditing]=useState<Group|'new'|null>(null);
 const [removing,setRemoving]=useState<Group|null>(null);
 const [planning,setPlanning]=useState<{id:string;session:number}|null>(null);
 const visible=groups.filter(g=>g.archived===(filter==='Archived'));
 return <main className="page-content groups-page">
  <div className="page-heading"><div><div className="eyebrow">YOUR PEOPLE, READY FOR THE NEXT PLAN</div><h1>Good company, on repeat<span className="coral">.</span></h1><p>A familiar circle for Sunday suppers, weekend adventures, and everything in between.</p></div><Button id="create-group-button" disabled={!groupsReady} onClick={event=>{returnFocus.current=event.currentTarget;setEditing('new');}}><Plus size={17}/> Create a group</Button></div>
  <div className="groups-intro"><span className="activity-icon coral-bg"><Users size={23}/></span><div><strong>Less “who’s coming?” More “let’s go.”</strong><p>Save your adult aliases once. Choose your group whenever a new idea comes along.</p></div><Heart size={26}/></div>
  <div className="filter-row"><div className="segmented">{(['Active','Archived'] as const).map(value=><button key={value} className={filter===value?'selected':''} aria-pressed={filter===value} onClick={()=>setFilter(value)}>{value}<span>{groups.filter(g=>g.archived===(value==='Archived')).length}</span></button>)}</div><span className="groups-demo-label">Local demo · Owner: Alex</span></div>
  {groupWarning&&<p className="group-storage-warning" role="alert">{groupWarning}</p>}
  {!groupsReady?<p role="status" className="muted">Getting your people together…</p>:visible.length===0?<div className="empty-state"><Users size={34}/><h3>{filter==='Archived'?'No groups tucked away.':'Make room for your people.'}</h3><p>{filter==='Archived'?'Archived groups will appear here. Existing plans always stay as they are.':'Create your first group and give your next plan a familiar starting point.'}</p>{filter==='Active'&&<Button onClick={event=>{returnFocus.current=event.currentTarget;setEditing('new');}}><Plus size={16}/> Create a group</Button>}</div>:<div className="groups-grid">{visible.map(group=>{
  const Icon=group.theme==='Sunday supper'?Utensils:group.theme==='Weekend friends'?Mountain:group.theme==='Family outings'?Heart:Sparkles;
  const tone=group.theme==='Sunday supper'?'coral-bg':group.theme==='Weekend friends'?'mint':'lavender';
  return <article className="group-card" key={group.id} aria-label={group.name}><div className="group-card-top"><span className={'activity-icon '+tone}><Icon size={22}/></span><span className={'status '+(group.archived?'':'mint')}>{group.archived?'Archived':'Ready for a plan'}</span></div><span className="group-theme-label">{group.theme}</span><h2>{group.name}</h2><p className="group-card-members">{group.members.map(m=>m.preferredName).join(', ')}</p><div className="group-card-people"><Avatars members={group.members.map(m=>({name:m.preferredName,color:m.color}))}/><span>{group.members.length} {group.members.length===1?'adult':'adults'} · Alex owns this group</span></div><div className="group-card-actions">{!group.archived&&<Button size="sm" onClick={()=>setPlanning({id:group.id,session:Date.now()})}>Plan with this group <ArrowRight size={14}/></Button>}<div className="group-card-tools"><button className="icon-button" aria-label={'Edit '+group.name} onClick={event=>{returnFocus.current=event.currentTarget;setEditing(group);}}><Pencil size={15}/></button><button className="icon-button" aria-label={(group.archived?'Restore ':'Archive ')+group.name} onClick={()=>archiveGroup(group.id,!group.archived)}>{group.archived?<RotateCcw size={15}/>:<Archive size={15}/>}</button><button className="icon-button" aria-label={'Remove '+group.name} onClick={event=>{returnFocus.current=event.currentTarget;setRemoving(group);}}><Trash2 size={15}/></button></div></div></article>;
 })}</div>}
  <div className="demo-disclaimer"><Sparkles size={16}/><span>Reusable groups, individual plans. Group changes never rewrite earlier plans. No invitations are sent.</span></div>
  <Dialog onCloseAutoFocus={event=>{event.preventDefault();returnFocus.current?.focus();}} open={editing!==null} onOpenChange={open=>{if(!open)setEditing(null);}} title={editing==='new'?'Your people, together.':'A little update to your circle.'} description="Choose a theme, give your group a name, and add adult aliases.">{editing&&<GroupEditor key={editing==='new'?'new':editing.id} group={editing==='new'?undefined:editing} onSaved={()=>setEditing(null)} onCancel={()=>setEditing(null)}/>}</Dialog>
  <Dialog onCloseAutoFocus={event=>{event.preventDefault();if(returnFocus.current?.isConnected)returnFocus.current.focus();else document.getElementById('create-group-button')?.focus();}} open={removing!==null} onOpenChange={open=>{if(!open)setRemoving(null);}} title="Remove this group?" description="Existing plans, participants, messages and votes will stay exactly as they are."><p className="group-remove-copy">Remove <strong>{removing?.name}</strong> from your reusable groups? This removes its saved contact details from this browser’s group list.</p><div className="group-form-actions"><Button variant="outline" onClick={()=>setRemoving(null)}>Keep group</Button><Button onClick={()=>{if(removing)removeGroup(removing.id);setRemoving(null);}}>Remove group <Trash2 size={15}/></Button></div></Dialog>
  {planning&&<CreatePlan key={planning.session} open onOpenChange={open=>{if(!open)setPlanning(null);}} initialGroupId={planning.id}/>}
 </main>;
}
