'use client';
import {useEffect,useRef,useState} from 'react';
import Link from 'next/link';
import {Bell} from 'lucide-react';
import {Dialog} from '@/components/ui/dialog';
import {Button} from '@/components/ui/button';
import {ConnectedService,getAuth} from '@/services/connected';
import {usePlanning} from './store';
import './plan-sharing.css';
interface Notice {id:string;plan_id:string;title:string;created_at:string;read:boolean}
export function PlanNotifications(){
 const {config,user,reload}=usePlanning();const [open,setOpen]=useState(false);
 const [items,setItems]=useState<Notice[]>([]);const [error,setError]=useState('');const [loading,setLoading]=useState(true);
 const live=useRef(false);const userId=user?.id;const button=useRef<HTMLButtonElement|null>(null);const reads=useRef(0);
 useEffect(()=>{
  live.current=true;if(!config||!userId)return()=>{live.current=false;};
  const api=new ConnectedService(getAuth(config));const scope={userId:userId,isCurrent:()=>live.current};
  async function refresh(){
   const request=++reads.current;
   try{const next=await api.request<Notice[]>('/v1/notifications',{},scope);if(live.current&&request===reads.current){setItems(next);setError('');void reload();}}
   catch(cause){if(live.current&&request===reads.current){setItems([]);setError(cause instanceof Error?cause.message:'Notifications unavailable.');}}
   finally{if(live.current&&request===reads.current)setLoading(false);}
  }
  void refresh();const focus=()=>{setItems([]);void refresh();};
  const timer=setInterval(()=>{if(document.visibilityState==='visible')void refresh();},15000);
  window.addEventListener('focus',focus);
  return()=>{live.current=false;clearInterval(timer);window.removeEventListener('focus',focus);};
 },[config,userId,reload,open]);
 async function mark(id:string){
  if(!config||!user)return;
  try{await new ConnectedService(getAuth(config)).request('/v1/notifications/'+encodeURIComponent(id)+'/read',{method:'POST'}, {userId:userId,isCurrent:()=>live.current});if(live.current){++reads.current;setItems(current=>current.map(n=>n.id===id?{...n,read:true}:n));}}
  catch(cause){if(live.current){setItems([]);setError(cause instanceof Error?cause.message:'Could not update this notification.');}}
 }
 const unread=items.filter(n=>!n.read).length;
 return <><button ref={button} className="icon-button plan-notifications-button" aria-label={'Notifications, '+unread+' unread'} onClick={()=>setOpen(true)}><Bell size={19}/>{unread>0&&<span>{unread}</span>}</button>
  <Dialog open={open} onOpenChange={setOpen} title="Notifications" description="Plans shared with you. No email is sent." onCloseAutoFocus={event=>{event.preventDefault();button.current?.focus();}}>
   {loading&&<p role="status">Loading notifications…</p>}{error&&<p className="group-error" role="alert">{error}</p>}
   {!loading&&!error&&!items.length&&<p>No shared-plan notifications yet.</p>}
   <ul className="plan-notification-list">{items.map(item=><li key={item.id}><strong>A plan was shared with you</strong><span>{item.title}</span><small>{item.read?'Read':'Unread'}</small><div><Link className="btn btn-primary" href={'/plans/'+encodeURIComponent(item.plan_id)} onClick={()=>{void mark(item.id);setOpen(false);}}>Open plan</Link>{!item.read&&<Button variant="outline" size="sm" onClick={()=>void mark(item.id)}>Mark as read</Button>}</div></li>)}</ul>
  </Dialog>
 </>;
}
