import {test,expect} from '@playwright/test';
import {ApiError,ConnectedService} from '../src/services/connected';
import type {SupabaseClient} from '@supabase/supabase-js';
import {DecisionService,type DecisionSnapshot,type DecisionCommand} from '../src/services/decisions';

function state():DecisionSnapshot{return {plan_id:'plan',plan_revision:10,score:0,finalized:false,finalization:null,last_activity_at:null,comments:[],decisions:[{id:'place',planId:'plan',title:'Place',category:'place',required:true,status:'awaiting_responses',version:3,options:[{id:'one',label:'One',sourceIds:[]}],eligibleMemberIds:['alice','bob'],ballots:[],selectedOptionId:null,confirmation:null}]};}
function client(latest:DecisionSnapshot,error:Error=new ApiError('Plan changed; reload',409)){
 const writes:Record<string,unknown>[]=[];let reads=0;
 const api={request:async(_path:string,options?:RequestInit)=>{if(!options){reads++;return latest;}writes.push(JSON.parse(String(options.body)));if(writes.length===1)throw error;return {...latest,plan_revision:latest.plan_revision+1};}} as unknown as ConnectedService;
 return {service:new DecisionService(api),writes,reads:()=>reads};
}
const response:DecisionCommand={kind:'respond',decisionId:'place',optionId:'one',response:'support'};

test('another member response is safely rebased once without losing the current choice',async()=>{
 const before=state(),latest=state();latest.plan_revision=11;latest.decisions[0].ballots=[{memberId:'bob',optionId:'one',response:'support',decisionVersion:3,updatedAt:'2027-05-01T12:00:00Z'}];
 const c=client(latest);await expect(c.service.execute(before,response,{memberId:'alice',isCurrent:()=>true})).resolves.toMatchObject({plan_revision:12});
 expect(c.reads()).toBe(1);expect(c.writes).toHaveLength(2);expect(c.writes[1]).toMatchObject({expected_revision:11,expected_version:3,option_id:'one',response:'support'});
});

test('changed options and a response from another device require human review',async()=>{
 for(const change of ['version','own response','confirmed','membership']){
  const before=state(),latest=state();latest.plan_revision=11;
  if(change==='version')latest.decisions[0].version=4;
  if(change==='own response')latest.decisions[0].ballots=[{memberId:'alice',optionId:null,response:'abstain',decisionVersion:3,updatedAt:'2027-05-01T12:00:00Z'}];
  if(change==='confirmed')latest.decisions[0].status='confirmed';
  if(change==='membership')latest.decisions[0].eligibleMemberIds=['alice'];
  const c=client(latest);await expect(c.service.execute(before,response,{memberId:'alice',isCurrent:()=>true})).rejects.toThrow();expect(c.writes).toHaveLength(1);
 }
});

test('comment retry preserves text but never retries uncertain network writes or owner actions',async()=>{
 const latest=state();latest.plan_revision=11;
 const c=client(latest);await c.service.execute(state(),{kind:'comment',decisionId:'place',text:'Parking concern'},{memberId:'alice',isCurrent:()=>true});
 expect(c.writes).toHaveLength(2);expect(c.writes[1]).toMatchObject({text:'Parking concern',expected_revision:11});
 for(const command of [response,{kind:'confirm',decisionId:'place',optionId:'one'}] as DecisionCommand[]){
  const failed=client(latest,new Error('Network unavailable'));await expect(failed.service.execute(state(),command,{memberId:'alice',isCurrent:()=>true})).rejects.toThrow();expect(failed.writes).toHaveLength(1);expect(failed.reads()).toBe(0);
 }
 const owner=client(latest);await expect(owner.service.execute(state(),{kind:'confirm',decisionId:'place',optionId:'one'})).rejects.toThrow();expect(owner.reads()).toBe(0);
 const unscoped=client(latest);await expect(unscoped.service.execute(state(),{kind:'comment',decisionId:'place',text:'Unscoped comment'})).rejects.toThrow();expect(unscoped.reads()).toBe(0);
});

test('an account switch cancels a retry before another write',async()=>{
 const latest=state();latest.plan_revision=11;let current=true;const c=client(latest);
 await expect(c.service.execute(state(),response,{memberId:'alice',isCurrent:()=>{const result=current;current=false;return result;}})).rejects.toThrow();expect(c.writes).toHaveLength(1);
});

test('a switch during token acquisition cannot submit a previous account draft',async()=>{
 const original=globalThis.fetch;
 try{
  for(const scenario of ['different session','changed workspace']){
   let release!:(value:unknown)=>void;const session=new Promise(resolve=>{release=resolve;});let active=true,calls=0;
   const auth={auth:{getSession:()=>session}} as unknown as SupabaseClient;
   globalThis.fetch=async()=>{calls++;return Response.json(state());};
   const pending=new DecisionService(new ConnectedService(auth)).execute(state(),response,{memberId:'alice',isCurrent:()=>active});
   if(scenario==='changed workspace')active=false;
   release({data:{session:{access_token:'synthetic-token',user:{id:scenario==='different session'?'bob':'alice'}}},error:null});
   await expect(pending).rejects.toThrow('account');expect(calls).toBe(0);
  }
 }finally{globalThis.fetch=original;}
});
