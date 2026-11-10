'use client';
import {createContext,useCallback,useContext,useEffect,useRef,useState,type ReactNode} from 'react';
import type {Plan,CreatePlanInput,Activity,Group,GroupDraft} from '@/services/types';
import {mockPlanningService,simulatedAssistant} from '@/services/mock-planning-service';
import {ApiError,ConnectedService,getAuth,type CurrentUser,type PublicConfig,type Proposal,type DocumentSource} from '@/services/connected';

import {clearWorkspaceRole,writeWorkspaceRole,type WorkspaceRole} from '@/services/workspace-role';

import type {AcceptDraft} from '@/services/coordination';

import {captureRecoveryLocation,clearRecovery,recoveryContext} from '@/services/password-recovery';

import {loadGroups,makeGroup,saveGroups,validateGroup,groupOwner} from '@/services/group-service';

interface Store {
 groups:Group[];groupsReady:boolean;groupWarning:string;
 readGroup:(id:string)=>Promise<Group>;setGroupSharing:(id:string,shared:boolean,revision?:number)=>Promise<Group>;
 saveGroup:(draft:GroupDraft,id?:string,revision?:number)=>Promise<{group?:Group;error?:string}>;
 archiveGroup:(id:string,archived:boolean,revision?:number)=>Promise<void>;removeGroup:(id:string,revision?:number)=>Promise<void>;reloadGroups:()=>Promise<void>;
 addDiscoveredPlace:(planId:string,activity:Activity)=>Promise<void>;
 passwordRecovery:boolean;
 createGeneratedPlan:(draft:AcceptDraft)=>Promise<string>;
 deletePlan:(id:string,confirmation:string)=>Promise<void>;transferOwner:(id:string,userId:string)=>Promise<void>;
 workspaceRole:WorkspaceRole;chooseWorkspaceRole:(role:WorkspaceRole)=>Promise<void>;
 plans:Plan[];ready:boolean;mode:'demo'|'connected';config:PublicConfig|null;user:CurrentUser|null;
 error:string;busy:boolean;notice:string;notify:(text:string)=>void;setMode:(mode:'demo'|'connected')=>void;
 reload:()=>Promise<void>;create:(input:CreatePlanInput)=>Promise<string>;update:(id:string,fn:(plan:Plan)=>Plan)=>Promise<void>;
 sendMessage:(id:string,message:string)=>Promise<void>;confirmPreference:(id:string,label:string)=>Promise<void>;
 share:(id:string,email:string)=>Promise<void>;signOut:(scope?:'local'|'global')=>Promise<void>;proposals:(id:string)=>Promise<Proposal[]>;
 revoke:(id:string,userId:string)=>Promise<void>;documents:(id:string)=>Promise<DocumentSource[]>;
 addDocument:(id:string,title:string,text:string)=>Promise<void>;removeDocument:(id:string,sourceId:string)=>Promise<void>;
}
const Context=createContext<Store|null>(null);
export function PlanningProvider({children}:{children:ReactNode}) {
 const [groupsScope,setGroupsScope]=useState('');const groupReads=useRef(0);
 const [groups,setGroups]=useState<Group[]>([]);const groupsRef=useRef<Group[]>([]);const [groupsReady,setGroupsReady]=useState(false);const groupsWritable=useRef(false);const [groupWarning,setGroupWarning]=useState('');
 const [plans,setPlans]=useState<Plan[]>([]);const plansRef=useRef<Plan[]>([]);
 const [mode,setCurrentMode]=useState<'demo'|'connected'>('demo');const [config,setConfig]=useState<PublicConfig|null>(null);
 const [passwordRecovery,setPasswordRecovery]=useState(false);
 const [workspaceRole,setWorkspaceRole]=useState<WorkspaceRole>('member');
 const [user,setUser]=useState<CurrentUser|null>(null);const [ready,setReady]=useState(false);
 const [error,setError]=useState('');const [pending,setPending]=useState(0);const [notice,setNotice]=useState('');
 const service=useRef<ConnectedService|null>(null);const serial=useRef<Promise<unknown>>(Promise.resolve());const generation=useRef(0);const identity=useRef<string|null>(null);const roleRequest=useRef(0);
 const replace=useCallback((next:Plan[])=>{plansRef.current=next;setPlans(next);},[]);
 const reload=useCallback(async()=>{
   const current=generation.current;
   if(!service.current||recoveryContext())return;
   try {const me=await service.current.me();if(current!==generation.current)return;setUser(me);setWorkspaceRole(me.workspace_mode||'member');const next=await service.current.plans();if(current!==generation.current)return;replace(next);setError('');}
   catch(e){if(current!==generation.current)return;setError(e instanceof Error?e.message:'Could not load shared plans.');if(e instanceof ApiError&&(e.status===401||e.status===403)){generation.current++;identity.current=null;setUser(null);replace([]);setReady(true);}}
   finally{if(current===generation.current)setReady(true);}
 },[replace]);
 useEffect(()=>{let active=true;void fetch('/api/config',{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error('Could not load app configuration.');return r.json() as Promise<PublicConfig>;}).then(c=>{if(!active)return;setConfig(c);const recovering=captureRecoveryLocation();setPasswordRecovery(recovering);let selected:string|null=null;try{selected=localStorage.getItem('tagalong-workspace-mode');}catch{}setCurrentMode(recovering||selected==='connected'||(!selected&&(c.connectedReady||c.requireConnected))?'connected':'demo');}).catch(()=>{if(active){setCurrentMode('connected');replace([]);setUser(null);setReady(true);setError('Could not load app configuration. Please reload.');}});return()=>{active=false;};},[replace]);
 useEffect(()=>{
   if(!config)return;
   ++generation.current;let disposed=false;service.current=null;
   if(mode==='demo'){void mockPlanningService.load().then(next=>{if(!disposed){replace(next);setUser(null);setReady(true);}});return()=>{disposed=true;};}
   if(!config.connectedReady){queueMicrotask(()=>{if(!disposed){replace([]);setUser(null);setError('Shared workspace needs Supabase and the API configuration.');setReady(true);}});return()=>{disposed=true;};}
   const auth=getAuth(config);service.current=new ConnectedService(auth);
   const load=async()=>{const current=generation.current;const {data:{session}}=await auth.auth.getSession();if(disposed||current!==generation.current)return;const recovery=recoveryContext();if(recovery){if(recovery.userId&&session?.user.id&&recovery.userId!==session.user.id){clearRecovery();setPasswordRecovery(false);}else{setPasswordRecovery(true);setUser(null);replace([]);setReady(true);return;}}if(session)await reload();else{setUser(null);replace([]);setReady(true);}};
   void load();
   const {data:{subscription}}=auth.auth.onAuthStateChange((_event,session)=>{if(disposed)return;if(_event==='PASSWORD_RECOVERY'){generation.current++;identity.current=session?.user.id??null;setPasswordRecovery(true);setWorkspaceRole('member');replace([]);setUser(null);setReady(true);return;}if(_event==='SIGNED_OUT'){clearRecovery();setPasswordRecovery(false);}const next=session?.user.id??null;if(identity.current!==next){identity.current=next;generation.current++;replace([]);setUser(null);++groupReads.current;groupsRef.current=[];setGroups([]);setGroupsReady(false);setGroupWarning('');}setTimeout(()=>{if(!disposed)void load();},0);});
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
 const groupUserId=user?.id;
 const reloadGroups=useCallback(async()=>{
   const api=service.current,current=generation.current,request=++groupReads.current;
   if(!api)return;
   try{const next=await api.groups();if(current!==generation.current||request!==groupReads.current)return;groupsRef.current=next;setGroups(next);setGroupWarning('');}
   catch(cause){if(current!==generation.current||request!==groupReads.current)return;groupsRef.current=[];setGroups([]);setGroupWarning(cause instanceof Error?cause.message:'Could not load your groups.');}
   finally{if(current===generation.current&&request===groupReads.current)setGroupsReady(true);}
 },[]);
 const readGroup=useCallback(async(id:string)=>{
   const api=service.current,current=generation.current;
   if(!api)throw new Error('Sign in to view this group.');
   const group=await api.group(id,{userId:identity.current??undefined,isCurrent:()=>current===generation.current});
   if(current!==generation.current)throw new Error('Workspace changed.');
   return group;
 },[]);
 async function setGroupSharing(id:string,shared:boolean,revision?:number){
   if(mode!=='connected'||!user)throw new Error('Sign in to share a group.');
   const old=groupsRef.current.find(g=>g.id===id&&g.ownerId===user.id);
   if(!old)throw new Error('Only the owner can share this group.');
   try{return await execute(async valid=>{
     const group=await service.current!.groupSharing({...old,revision:revision??old.revision},shared);
     if(!valid())throw new Error('Workspace changed.');
     ++groupReads.current;const next=groupsRef.current.map(g=>g.id===id?group:g);groupsRef.current=next;setGroups(next);
     setNotice(shared?'Group shared with matching verified accounts. No messages were sent.':'Group sharing stopped.');return group;
   });}catch(cause){await reloadGroups();throw cause;}
 }
 useEffect(()=>{
   if(!config)return;let active=true;
   queueMicrotask(()=>{
     if(!active)return;
     ++groupReads.current;groupsRef.current=[];setGroups([]);setGroupsReady(false);setGroupWarning('');setGroupsScope(mode+':'+(groupUserId||''));
     if(mode==='demo'){const loaded=loadGroups();groupsRef.current=loaded.groups;setGroups(loaded.groups);groupsWritable.current=loaded.writable;setGroupWarning(loaded.warning);setGroupsReady(true);}
     else{groupsWritable.current=false;if(groupUserId)void reloadGroups();else setGroupsReady(true);}
   });return()=>{active=false;};
 },[config,mode,groupUserId,reloadGroups]);
 function persistGroups(next:Group[],message:string){const warning=saveGroups(next,groupsWritable.current);groupsRef.current=next;setGroups(next);setGroupWarning(warning);setNotice(warning?'Updated for this session only. '+warning:message);}
 async function saveGroup(draft:GroupDraft,id?:string,revision?:number){
   if(!groupsReady)return {error:'Groups are still loading. Try again shortly.'};
   if(mode==='connected'&&!user)return {error:'Sign in to save your groups.'};
   const current=groupsRef.current,old=id?current.find(g=>g.id===id):undefined;
   if(id&&!old)return {error:'This group is no longer available.'};
   const owner=mode==='demo'?groupOwner:{id:user!.id,preferredName:(user!.display_name||user!.name).slice(0,40),color:'#edc6b3'};
   if(mode==='connected'&&old&&old.ownerId!==user!.id)return {error:'Only the owner can edit this group.'};
   const error=validateGroup(draft,mode==='demo'?current:current.filter(g=>g.ownerId===user!.id),id,owner);if(error)return {error};
   if(mode==='demo'){const group={...makeGroup(draft,id),archived:old?.archived??false};persistGroups(id?current.map(g=>g.id===id?group:g):[group,...current],id?'Group updated. Existing plans stay as they are.':'Your group is ready. No invitations were sent.');return {group};}
   try{return await execute(async valid=>{
     const group=await service.current!.saveGroup(draft,old,revision);if(!valid())throw new Error('Workspace changed.');
     ++groupReads.current;const next=id?groupsRef.current.map(g=>g.id===id?group:g):[group,...groupsRef.current];groupsRef.current=next;setGroups(next);setGroupWarning('');setNotice('Group saved to your account. No invitations were sent.');return {group};
   });}catch(cause){await reloadGroups();return {error:cause instanceof Error?cause.message:'Could not save this group.'};}
 }
 async function archiveGroup(id:string,archived:boolean,revision?:number){
   if(!groupsReady)throw new Error('Groups are still loading.');
   const old=groupsRef.current.find(g=>g.id===id);if(!old)throw new Error('This group is no longer available.');
   if(mode==='demo'){persistGroups(groupsRef.current.map(g=>g.id===id?{...g,archived}:g),archived?'Group archived. Existing plans stay as they are.':'Group restored.');return;}
   try{await execute(async valid=>{const group=await service.current!.archiveGroup(old,archived,revision);if(!valid())return;++groupReads.current;const next=groupsRef.current.map(g=>g.id===id?group:g);groupsRef.current=next;setGroups(next);setNotice(archived?'Group archived. Existing plans stay as they are.':'Group restored.');});}catch(cause){await reloadGroups();throw cause;}
 }
 async function removeGroup(id:string,revision?:number){
   if(!groupsReady)throw new Error('Groups are still loading.');
   const old=groupsRef.current.find(g=>g.id===id);if(!old)throw new Error('This group is no longer available.');
   if(mode==='demo'){persistGroups(groupsRef.current.filter(g=>g.id!==id),'Group removed. Existing plans stay as they are.');return;}
   try{await execute(async valid=>{await service.current!.removeGroup(old,revision);if(!valid())return;++groupReads.current;const next=groupsRef.current.filter(g=>g.id!==id);groupsRef.current=next;setGroups(next);setNotice('Group removed. Existing plans stay as they are.');});}catch(cause){await reloadGroups();throw cause;}
 }
 function setMode(next:'demo'|'connected'){groupsRef.current=[];setGroups([]);setGroupsReady(false);clearRecovery();setPasswordRecovery(false);generation.current++;try{localStorage.setItem('tagalong-workspace-mode',next);}catch{}replace([]);setUser(null);setError('');setReady(false);setCurrentMode(next);}
 async function execute<T>(action:(valid:()=>boolean)=>Promise<T>):Promise<T>{
   const current=generation.current;setPending(n=>n+1);
   const valid=()=>current===generation.current;
   const task=serial.current.catch(()=>undefined).then(async()=>{if(!valid())throw new Error('Workspace changed. Please try again.');return action(valid);});serial.current=task;
   try{return await task;}catch(e){if(!valid())throw e;const message=e instanceof ApiError&&e.status===409&&!/group/i.test(e.message)?'Someone changed this plan. We refreshed it; please retry your change.':e instanceof Error?e.message:'Your change could not be saved.';setError(message);setNotice(message);if(service.current){try{const next=await service.current.plans();if(valid())replace(next);}catch{}}throw e;}finally{setPending(n=>n-1);}
 }
 async function createGeneratedPlan(draft:AcceptDraft){return execute(async valid=>{const plan=await service.current!.request<Plan>('/v1/plans/from-draft',{method:'POST',body:JSON.stringify(draft)});if(!valid())throw new Error('Workspace changed.');replace([plan,...plansRef.current.filter(p=>p.id!==plan.id)]);setError('');setNotice('Your reviewed plan is ready.');return plan.id;});}
 async function create(input:CreatePlanInput){return execute(async valid=>{
   const group=input.groupId?groupsRef.current.find(g=>g.id===input.groupId&&!g.archived):undefined;
   if(input.groupId&&(!groupsReady||!group))throw new Error('Choose an active group before creating this plan.');
   const plan=mode==='demo'?mockPlanningService.create(input,group):await service.current!.create({...input,expectedGroupRevision:input.expectedGroupRevision??group?.revision});
   if(!valid())throw new Error('Workspace changed.');replace([plan,...plansRef.current]);setError('');return plan.id;
 });}
 async function addDiscoveredPlace(id:string,activity:Activity){await execute(async valid=>{const old=plansRef.current.find(p=>p.id===id);if(!old)throw new Error('This plan is unavailable.');if(old.itinerary.some(a=>a.id===activity.id||a.source_url===activity.source_url&&a.title===activity.title&&a.location===activity.location&&a.day===activity.day))throw new Error('This place is already in the draft for that day.');const next={...old,itinerary:[...old.itinerary,activity]};const saved=mode==='demo'?next:await service.current!.save(next,old.revision??0,old);if(!valid())throw new Error('Workspace changed.');replace(plansRef.current.map(p=>p.id===id?saved:p));setError('');setNotice('Place added to your draft itinerary. Nothing is booked.');});}
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
 async function deletePlan(id:string,confirmation:string){await execute(async valid=>{const plan=plansRef.current.find(p=>p.id===id);if(!plan)throw new Error('Plan is unavailable.');await service.current!.deletePlan(id,plan.revision??0,confirmation);if(valid()){replace(plansRef.current.filter(p=>p.id!==id));setNotice('Plan deleted from member workspaces. Records are retained for admin review.');}});}
 async function transferOwner(id:string,userId:string){await execute(async valid=>{const plan=plansRef.current.find(p=>p.id===id);if(!plan)throw new Error('Plan is unavailable.');const saved=await service.current!.transferOwner(id,plan.revision??0,userId);if(valid()){replace(plansRef.current.map(p=>p.id===id?saved:p));setNotice('Ownership transferred. You remain a member.');}});}
 async function chooseWorkspaceRole(role:WorkspaceRole){
   if(!config||!service.current)throw new Error('Shared workspace is unavailable.');
   const current=generation.current;const request=++roleRequest.current;const api=service.current;
   const auth=getAuth(config);const initial=await auth.auth.getSession();const accountId=initial.data.session?.user.id;
   if(!accountId)throw new Error('Please sign in again.');
   const me=await api.request<CurrentUser>('/v1/me',{headers:{'X-Workspace-Mode':'member'}});
   const latest=await auth.auth.getSession();
   if(current!==generation.current||request!==roleRequest.current||latest.data.session?.user.id!==accountId||me.id!==accountId)throw new Error('Workspace changed. Please try again.');
   if(role==='admin'&&!me.app_admin)throw new Error('This account does not have app administrator access.');
   writeWorkspaceRole(me.id,role);generation.current++;replace([]);setWorkspaceRole(role);setUser(null);setReady(false);await reload();
 }
 async function signOut(scope:'local'|'global'='global'){++groupReads.current;groupsRef.current=[];setGroups([]);setGroupsReady(false);setGroupsScope('');setGroupWarning('');clearRecovery();setPasswordRecovery(false);clearWorkspaceRole();setWorkspaceRole('member');generation.current++;identity.current=null;setUser(null);replace([]);setError('');if(config?.connectedReady)await getAuth(config).auth.signOut({scope});}
 const documents=useCallback((id:string)=>service.current?.documents(id)??Promise.resolve([]),[]);
 async function addDocument(id:string,title:string,text:string){await execute(async valid=>{await service.current!.addDocument(id,title,text);if(valid())setNotice('Saved to Notes. Available to the assistant now; historical search indexing continues in the background.');});}
 async function removeDocument(id:string,sourceId:string){await execute(async valid=>{await service.current!.removeDocument(id,sourceId);if(valid())setNotice('Document removed from retrieval.');});}
 async function revoke(id:string,userId:string){await execute(async valid=>{const api=service.current!;await api.revoke(id,userId);if(!valid())return;const plan=await api.plan(id);if(valid())replace(plansRef.current.map(p=>p.id===id?plan:p));});}
 return <Context.Provider value={{groups:groupsScope===mode+':'+(user?.id||'')?groups:[],groupsReady:groupsReady&&groupsScope===mode+':'+(user?.id||''),groupWarning:groupsScope===mode+':'+(user?.id||'')?groupWarning:'',readGroup,setGroupSharing,saveGroup,archiveGroup,removeGroup,reloadGroups,addDiscoveredPlace,passwordRecovery,createGeneratedPlan,deletePlan,transferOwner,workspaceRole,chooseWorkspaceRole,plans,ready,mode,config,user,error,busy:pending>0,notice,notify:setNotice,setMode,reload,create,update,sendMessage,confirmPreference,share,signOut,revoke,documents,addDocument,removeDocument,proposals:id=>service.current?.proposals(id)??Promise.resolve([])}}>{children}<div className={'toast '+(notice?'shown':'')} role="status">{notice}</div></Context.Provider>;
}
export function usePlanning(){const store=useContext(Context);if(!store)throw new Error('PlanningProvider is required');return store;}
