'use client';
import {createContext,useCallback,useContext,useEffect,useRef,useState,type ReactNode} from 'react';
import type {Plan,CreatePlanInput} from '@/services/types';
import {mockPlanningService,simulatedAssistant} from '@/services/mock-planning-service';
import {ApiError,ConnectedService,getAuth,type CurrentUser,type PublicConfig,type Proposal,type DocumentSource} from '@/services/connected';

interface Store {
 plans:Plan[];ready:boolean;mode:'demo'|'connected';config:PublicConfig|null;user:CurrentUser|null;
 error:string;busy:boolean;notice:string;notify:(text:string)=>void;setMode:(mode:'demo'|'connected')=>void;
 reload:()=>Promise<void>;create:(input:CreatePlanInput)=>Promise<string>;update:(id:string,fn:(plan:Plan)=>Plan)=>Promise<void>;
 sendMessage:(id:string,message:string)=>Promise<void>;confirmPreference:(id:string,label:string)=>Promise<void>;
 share:(id:string,email:string)=>Promise<void>;signOut:()=>Promise<void>;proposals:(id:string)=>Promise<Proposal[]>;
 revoke:(id:string,userId:string)=>Promise<void>;documents:(id:string)=>Promise<DocumentSource[]>;
 addDocument:(id:string,title:string,text:string)=>Promise<void>;removeDocument:(id:string,sourceId:string)=>Promise<void>;
}
const Context=createContext<Store|null>(null);
export function PlanningProvider({children}:{children:ReactNode}) {
 const [plans,setPlans]=useState<Plan[]>([]);const plansRef=useRef<Plan[]>([]);
 const [mode,setCurrentMode]=useState<'demo'|'connected'>('demo');const [config,setConfig]=useState<PublicConfig|null>(null);
 const [user,setUser]=useState<CurrentUser|null>(null);const [ready,setReady]=useState(false);
 const [error,setError]=useState('');const [pending,setPending]=useState(0);const [notice,setNotice]=useState('');
 const service=useRef<ConnectedService|null>(null);const serial=useRef<Promise<unknown>>(Promise.resolve());const generation=useRef(0);const identity=useRef<string|null>(null);
 const replace=useCallback((next:Plan[])=>{plansRef.current=next;setPlans(next);},[]);
 const reload=useCallback(async()=>{
   const current=generation.current;
   if(!service.current)return;
   try {const me=await service.current.me();if(current!==generation.current)return;setUser(me);const next=await service.current.plans();if(current!==generation.current)return;replace(next);setError('');}
   catch(e){if(current!==generation.current)return;setError(e instanceof Error?e.message:'Could not load shared plans.');if(e instanceof ApiError&&e.status===401){setUser(null);replace([]);}}
   finally{if(current===generation.current)setReady(true);}
 },[replace]);
 useEffect(()=>{let active=true;void fetch('/api/config',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error('Could not load app configuration.');return r.json() as Promise<PublicConfig>;}).then(c=>{if(!active)return;setConfig(c);let selected:string|null=null;try{selected=localStorage.getItem('tagalong-workspace-mode');}catch{}setCurrentMode(selected==='connected'||(!selected&&(c.connectedReady||c.requireConnected))?'connected':'demo');}).catch(()=>{if(active){setCurrentMode('connected');replace([]);setUser(null);setReady(true);setError('Could not load app configuration. Please reload.');}});return()=>{active=false;};},[replace]);
 useEffect(()=>{
   if(!config)return;
   ++generation.current;let disposed=false;service.current=null;
   if(mode==='demo'){void mockPlanningService.load().then(next=>{if(!disposed){replace(next);setUser(null);setReady(true);}});return()=>{disposed=true;};}
   if(!config.connectedReady){queueMicrotask(()=>{if(!disposed){replace([]);setUser(null);setError('Shared workspace needs Supabase and the API configuration.');setReady(true);}});return()=>{disposed=true;};}
   const auth=getAuth(config);service.current=new ConnectedService(auth);
   const load=async()=>{const current=generation.current;const {data:{session}}=await auth.auth.getSession();if(disposed||current!==generation.current)return;if(session)await reload();else{setUser(null);replace([]);setReady(true);}};
   void load();
   const {data:{subscription}}=auth.auth.onAuthStateChange((_event,session)=>{if(disposed)return;const next=session?.user.id??null;if(identity.current!==next){identity.current=next;generation.current++;replace([]);setUser(null);}setTimeout(()=>{if(!disposed)void load();},0);});
   return()=>{disposed=true;subscription.unsubscribe();};
 },[config,mode,reload,replace]);
 useEffect(()=>{if(mode==='demo'&&ready)mockPlanningService.save(plans);},[mode,plans,ready]);
 useEffect(()=>{if(!notice)return;const timer=setTimeout(()=>setNotice(''),5000);return()=>clearTimeout(timer);},[notice]);
 useEffect(()=>{
   if(mode!=='connected'||!config?.connectedReady||!user)return;
   const auth=getAuth(config);let timer:ReturnType<typeof setTimeout>|undefined;
   const refresh=()=>{clearTimeout(timer);timer=setTimeout(()=>{if(pending===0)void reload();},250);};
   const channel=auth.channel('tagalong-plans-'+user.id).on('postgres_changes',{event:'*',schema:'public',table:'tagalong_revisions'},refresh).subscribe();
   const poll=setInterval(()=>{if(document.visibilityState==='visible'&&pending===0)void reload();},15000);
   window.addEventListener('focus',refresh);
   return()=>{clearTimeout(timer);clearInterval(poll);window.removeEventListener('focus',refresh);void auth.removeChannel(channel);};
 },[config,mode,user,pending,reload]);
 function setMode(next:'demo'|'connected'){generation.current++;try{localStorage.setItem('tagalong-workspace-mode',next);}catch{}replace([]);setUser(null);setError('');setReady(false);setCurrentMode(next);}
 async function execute<T>(action:(valid:()=>boolean)=>Promise<T>):Promise<T>{
   const current=generation.current;setPending(n=>n+1);
   const valid=()=>current===generation.current;
   const task=serial.current.catch(()=>undefined).then(async()=>{if(!valid())throw new Error('Workspace changed. Please try again.');return action(valid);});serial.current=task;
   try{return await task;}catch(e){if(!valid())throw e;const message=e instanceof ApiError&&e.status===409?'Someone changed this plan. We refreshed it; please retry your change.':e instanceof Error?e.message:'Your change could not be saved.';setError(message);setNotice(message);if(service.current){try{const next=await service.current.plans();if(valid())replace(next);}catch{}}throw e;}finally{setPending(n=>n-1);}
 }
 async function create(input:CreatePlanInput){return execute(async valid=>{const plan=mode==='demo'?mockPlanningService.create(input):await service.current!.create(input);if(!valid())throw new Error('Workspace changed.');replace([plan,...plansRef.current]);setError('');return plan.id;});}
 async function update(id:string,fn:(plan:Plan)=>Plan){
   try{await execute(async valid=>{const old=plansRef.current.find(p=>p.id===id);if(!old)throw new Error('This plan is unavailable.');const next=fn(old);const saved=mode==='demo'?next:await service.current!.save(next,old.revision??0,old);if(!valid())return;replace(plansRef.current.map(p=>p.id===id?saved:p));setError('');});}catch{/* The shared error banner retains failures for the user. */}
 }
 async function sendMessage(id:string,message:string){await execute(async valid=>{
   const old=plansRef.current.find(p=>p.id===id);if(!old)throw new Error('This plan is unavailable.');
   const time=new Date().toLocaleTimeString('en-US',{hour:'numeric',minute:'2-digit'});
   let next:Plan={...old,messages:[...old.messages,{id:crypto.randomUUID(),author:user?.name||'Alex',user_id:user?.id,text:message,time}]};
   if(mode==='connected')next=await service.current!.save(next,old.revision??0,old);
   if(!valid())return;replace(plansRef.current.map(p=>p.id===id?next:p));
   if(/@tagalong/i.test(message)){
     if(mode==='demo'){const answer=simulatedAssistant.reply(message);next={...next,messages:[...next.messages,{id:crypto.randomUUID(),author:'Tagalong',assistant:true,text:answer.text,time}],preferences:[...next.preferences,...answer.preferences.filter(pref=>!next.preferences.some(x=>x.label===pref.label))]};}
     else{const api=service.current!;await api.assistant(id,message);if(!valid())return;next=await api.plan(id);}
     if(!valid())return;replace(plansRef.current.map(p=>p.id===id?next:p));
   }setError('');
 });}
 async function confirmPreference(id:string,label:string){if(mode==='demo'){await update(id,p=>({...p,preferences:p.preferences.map(x=>x.label===label?{...x,confirmed:true}:x)}));return;}await execute(async valid=>{const api=service.current!;const proposals=await api.proposals(id);if(!valid())return;const proposal=proposals.find(p=>p.label===label&&p.status==='pending');if(!proposal)throw new Error('This proposal changed. Refresh the plan before confirming.');const saved=await api.confirm(id,proposal.id);if(valid())replace(plansRef.current.map(p=>p.id===id?saved:p));});}
 async function share(id:string,email:string){await execute(async valid=>{const api=service.current!;await api.share(id,email);if(!valid())return;const plan=await api.plan(id);if(!valid())return;replace(plansRef.current.map(p=>p.id===id?plan:p));setNotice('Member added. No email was sent.');});}
 async function signOut(){generation.current++;identity.current=null;setUser(null);replace([]);setError('');if(config?.connectedReady)await getAuth(config).auth.signOut();}
 const documents=useCallback((id:string)=>service.current?.documents(id)??Promise.resolve([]),[]);
 async function addDocument(id:string,title:string,text:string){await execute(async valid=>{await service.current!.addDocument(id,title,text);if(valid())setNotice('Document saved. It will be searchable after indexing.');});}
 async function removeDocument(id:string,sourceId:string){await execute(async valid=>{await service.current!.removeDocument(id,sourceId);if(valid())setNotice('Document removed from retrieval.');});}
 async function revoke(id:string,userId:string){await execute(async valid=>{const api=service.current!;await api.revoke(id,userId);if(!valid())return;const plan=await api.plan(id);if(valid())replace(plansRef.current.map(p=>p.id===id?plan:p));});}
 return <Context.Provider value={{plans,ready,mode,config,user,error,busy:pending>0,notice,notify:setNotice,setMode,reload,create,update,sendMessage,confirmPreference,share,signOut,revoke,documents,addDocument,removeDocument,proposals:id=>service.current?.proposals(id)??Promise.resolve([])}}>{children}<div className={'toast '+(notice?'shown':'')} role="status">{notice}</div></Context.Provider>;
}
export function usePlanning(){const store=useContext(Context);if(!store)throw new Error('PlanningProvider is required');return store;}
