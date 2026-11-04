'use client';
import {createContext,useContext,useEffect,useState,type ReactNode} from 'react';
import type {Plan,CreatePlanInput} from '@/services/types';
import {initialPlans} from '@/services/demo-data';
import {mockPlanningService} from '@/services/mock-planning-service';
interface Store{plans:Plan[];ready:boolean;create:(input:CreatePlanInput)=>string;update:(id:string,fn:(p:Plan)=>Plan)=>void;notice:string;notify:(message:string)=>void}
const Context=createContext<Store|null>(null);
export function PlanningProvider({children}:{children:ReactNode}){const [plans,setPlans]=useState<Plan[]>(initialPlans);const [ready,setReady]=useState(false);const [notice,setNotice]=useState('');useEffect(()=>{let active=true;void mockPlanningService.load().then(saved=>{if(active){setPlans(saved);setReady(true);}});return()=>{active=false;};},[]);useEffect(()=>{if(ready)mockPlanningService.save(plans);},[plans,ready]);useEffect(()=>{if(!notice)return;const timer=setTimeout(()=>setNotice(''),4500);return()=>clearTimeout(timer);},[notice]);function create(input:CreatePlanInput){const plan=mockPlanningService.create(input);setPlans(old=>[plan,...old]);return plan.id;}function update(id:string,fn:(p:Plan)=>Plan){setPlans(old=>old.map(p=>p.id===id?fn(p):p));}return <Context.Provider value={{plans,ready,create,update,notice,notify:setNotice}}>{children}<div className={'toast '+(notice?'shown':'')} role="status">{notice}</div></Context.Provider>;}
export function usePlanning(){const context=useContext(Context);if(!context)throw new Error('PlanningProvider is required');return context;}
