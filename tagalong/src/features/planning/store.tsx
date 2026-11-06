'use client';
import {createContext,useContext,useEffect,useState,type ReactNode} from 'react';
import type {Plan,CreatePlanInput,Group,GroupDraft} from '@/services/types';
import {initialPlans} from '@/services/demo-data';
import {mockPlanningService} from '@/services/mock-planning-service';
import {loadGroups,makeGroup,saveGroups,validateGroup} from '@/services/group-service';

interface Store {
 plans:Plan[];ready:boolean;create:(input:CreatePlanInput)=>string;update:(id:string,fn:(p:Plan)=>Plan)=>void;
 groups:Group[];groupsReady:boolean;groupWarning:string;
 saveGroup:(draft:GroupDraft,id?:string)=>{group?:Group;error?:string};
 archiveGroup:(id:string,archived:boolean)=>void;removeGroup:(id:string)=>void;
 notice:string;notify:(message:string)=>void;
}
const Context=createContext<Store|null>(null);
export function PlanningProvider({children}:{children:ReactNode}) {
 const [plans,setPlans]=useState<Plan[]>(initialPlans);
 const [ready,setReady]=useState(false);
 const [notice,setNotice]=useState('');
 const [groups,setGroups]=useState<Group[]>([]);
 const [groupsReady,setGroupsReady]=useState(false);
 const [groupsWritable,setGroupsWritable]=useState(false);
 const [groupWarning,setGroupWarning]=useState('');
 useEffect(()=>{
  let active=true;
  void mockPlanningService.load().then(saved=>{if(active){setPlans(saved);setReady(true);}});
  void Promise.resolve().then(()=>{
   if(!active)return;
   const loaded=loadGroups();
   setGroups(loaded.groups);setGroupsWritable(loaded.writable);setGroupWarning(loaded.warning);setGroupsReady(true);
  });
  return()=>{active=false;};
 },[]);
 useEffect(()=>{if(ready)mockPlanningService.save(plans);},[plans,ready]);
 useEffect(()=>{if(!notice)return;const timer=setTimeout(()=>setNotice(''),4500);return()=>clearTimeout(timer);},[notice]);
 function create(input:CreatePlanInput){
  const group=input.groupId?groups.find(g=>g.id===input.groupId&&!g.archived):undefined;
  if(input.groupId&&(!groupsReady||!group))throw new Error('Choose an active group before creating this plan.');
  const plan=mockPlanningService.create(input,group);
  setPlans(old=>[plan,...old]);return plan.id;
 }
 function update(id:string,fn:(p:Plan)=>Plan){setPlans(old=>old.map(p=>p.id===id?fn(p):p));}
 function persistGroups(next:Group[],message:string){
  const warning=saveGroups(next,groupsWritable);
  setGroups(next);setGroupWarning(warning);setNotice(warning?'Updated for this session only. '+warning:message);
 }
 function saveGroup(draft:GroupDraft,id?:string){
  if(!groupsReady)return {error:'Groups are still loading. Try again shortly.'};
  if(id&&!groups.some(g=>g.id===id))return {error:'This group is no longer available.'};
  const error=validateGroup(draft,groups,id);
  if(error)return {error};
  const group={...makeGroup(draft,id),archived:id?groups.find(g=>g.id===id)!.archived:false};
  persistGroups(id?groups.map(g=>g.id===id?group:g):[group,...groups],id?'Group updated. Existing plans stay as they are.':'Your group is ready. No invitations were sent.');
  return {group};
 }
 function archiveGroup(id:string,archived:boolean){if(groupsReady)persistGroups(groups.map(g=>g.id===id?{...g,archived}:g),archived?'Group archived. Existing plans stay as they are.':'Group restored.');}
 function removeGroup(id:string){if(groupsReady)persistGroups(groups.filter(g=>g.id!==id),'Group removed. Existing plans stay as they are.');}
 return <Context.Provider value={{plans,ready,create,update,groups,groupsReady,groupWarning,saveGroup,archiveGroup,removeGroup,notice,notify:setNotice}}>{children}<div className={'toast '+(notice?'shown':'')} role="status">{notice}</div></Context.Provider>;
}
export function usePlanning(){const context=useContext(Context);if(!context)throw new Error('PlanningProvider is required');return context;}
