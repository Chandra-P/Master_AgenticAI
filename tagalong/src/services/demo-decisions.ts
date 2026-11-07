import type {Plan} from './types';
import {decisionParticipation,type Decision,type DecisionSnapshot,type DecisionCommand} from './decisions';

export const demoMemberId=(plan:Plan,index:number)=>plan.members[index]?.user_id||'demo-member-'+index;
const signature=(plan:Plan)=>JSON.stringify({title:plan.title,kind:plan.kind,members:plan.members.map((m,i)=>[demoMemberId(plan,i),m.name]),start:plan.start,end:plan.end,location:plan.location,budget:plan.budget,itinerary:plan.itinerary});
type DemoSnapshot=DecisionSnapshot&{demoSignature?:string;lastFinalizationKey?:string};
const option=(label:string,index:number)=>({id:'option-'+index,label,sourceIds:[] as string[]});
const status=(decision:Decision)=>{
 if(decision.confirmation?.decisionVersion===decision.version)return 'confirmed' as const;
 if(!decision.options.length)return 'needs_options' as const;
 const {ballots,missing}=decisionParticipation(decision);
 if(ballots.some(b=>b.response==='object'))return 'needs_discussion' as const;
 const consent=ballots.filter(b=>b.response==='support'||b.response==='can_live_with');
 if(!missing.length&&consent.length&&new Set(consent.map(b=>b.optionId)).size===1)return 'ready_to_confirm' as const;
 return !missing.length?'needs_discussion' as const:'awaiting_responses' as const;
};
function derive(snapshot:DemoSnapshot){
 let total=0;const required=snapshot.decisions.filter(d=>d.required);
 for(const decision of snapshot.decisions){
  decision.status=status(decision);
  if(!decision.required)continue;
  if(decision.status==='confirmed'){total++;continue;}
  const {ballots}=decisionParticipation(decision);const abstaining=ballots.filter(b=>b.response==='abstain').length;
  const denominator=decision.eligibleMemberIds.length-abstaining;
  const counts=decision.options.map(o=>ballots.filter(b=>b.optionId===o.id&&(b.response==='support'||b.response==='can_live_with')).length);
  total+=denominator?Math.max(0,...counts)/denominator:0;
 }
 snapshot.finalized=!!snapshot.finalization;
 snapshot.score=snapshot.finalized?100:Math.min(99,required.length?Math.round(total/required.length*100):0);
 return snapshot;
}

export function demoSnapshot(plan:Plan):DemoSnapshot {
 const existing=plan.decisionState as DemoSnapshot|undefined;
 if(existing){
  const snapshot=structuredClone(existing);
  if(snapshot.demoSignature!==signature(plan)){
   for(const decision of snapshot.decisions){decision.version++;decision.ballots=[];decision.confirmation=null;decision.selectedOptionId=null;decision.eligibleMemberIds=plan.members.map((_,i)=>demoMemberId(plan,i));}
   snapshot.finalization=null;snapshot.demoSignature=signature(plan);
  }
  return derive(snapshot);
 }
 const defaults:[string,string,string[]][]=[[plan.kind==='trip'?'destination':'place',plan.kind==='trip'?'Destination':'Place',/to decide|somewhere together/i.test(plan.location)?[]:[plan.location].filter(Boolean)],['dates',plan.kind==='trip'?'Dates':'Date and time',[plan.date].filter(Boolean)],['budget','Budget',plan.budget>0?[`USD ${plan.budget} per person`]:[]],...(plan.kind==='trip'?[['lodging','Lodging',[]] as [string,string,string[]]]:[]),['activities',plan.kind==='trip'?'Activities':'Activity or meal',plan.itinerary.length?[plan.itinerary.map(a=>a.title).join(', ').slice(0,300)]:[]]];
 return derive({plan_id:plan.id,plan_revision:0,decisions:defaults.map(([category,title,options])=>({id:'decision-'+category,planId:plan.id,title,category,required:true,status:'needs_options',version:1,options:options.map(option),eligibleMemberIds:plan.members.map((_,i)=>demoMemberId(plan,i)),ballots:[],selectedOptionId:null,confirmation:null})),comments:[],score:0,finalized:false,finalization:null,last_activity_at:null,demoSignature:signature(plan)});
}

export function applyDemoDecision(plan:Plan,input:DecisionSnapshot,command:DecisionCommand,actor:string):DemoSnapshot {
 const snapshot=structuredClone(input) as DemoSnapshot;
 const owner=demoMemberId(plan,0);const now=new Date().toISOString();
 if(!plan.members.some((_,i)=>demoMemberId(plan,i)===actor))throw new Error('Member access required.');
 const ownerOnly=()=>{if(actor!==owner)throw new Error('Only the plan owner can do this.');};
 const decision='decisionId' in command?snapshot.decisions.find(d=>d.id===command.decisionId):undefined;
 if('decisionId' in command&&!decision)throw new Error('Decision not found.');
 const invalidate=()=>{snapshot.finalization=null;delete snapshot.lastFinalizationKey;};
 if(command.kind==='finalize'&&snapshot.lastFinalizationKey===command.idempotencyKey&&snapshot.finalization)return derive(snapshot);
 switch(command.kind){
  case 'create':{
   ownerOnly();if(snapshot.decisions.length>=20)throw new Error('Decision limit reached.');
   const title=command.title.trim();if(!title||title.length>120)throw new Error('Provide a decision title (120 characters maximum).');
   const options=validateOptions(command.options);
   snapshot.decisions.push({id:crypto.randomUUID(),planId:plan.id,title,category:command.category,required:command.required,status:'needs_options',version:1,options:options.map(option),eligibleMemberIds:plan.members.map((_,i)=>demoMemberId(plan,i)),ballots:[],selectedOptionId:null,confirmation:null});invalidate();break;
  }
  case 'edit':{
   ownerOnly();if(command.title!==undefined){if(!command.title.trim()||command.title.length>120)throw new Error('Provide a valid decision title.');decision!.title=command.title.trim();}
   if(command.options!==undefined)decision!.options=validateOptions(command.options).map(option);
   if(command.required!==undefined)decision!.required=command.required;
   decision!.version++;decision!.ballots=[];decision!.confirmation=null;decision!.selectedOptionId=null;invalidate();break;
  }
  case 'respond':{
   if(command.response!=='abstain'&&!decision!.options.some(o=>o.id===command.optionId))throw new Error('Choose a current option.');
   decision!.ballots=decision!.ballots.filter(b=>b.memberId!==actor);
   decision!.ballots.push({memberId:actor,optionId:command.response==='abstain'?null:command.optionId,response:command.response,decisionVersion:decision!.version,updatedAt:now});
   decision!.confirmation=null;decision!.selectedOptionId=null;invalidate();break;
  }
  case 'comment':{
   const text=command.text.trim();if(!text||text.length>2000)throw new Error('Comments need 1–2000 characters.');
  if(snapshot.comments.length>=2000)throw new Error('Comment limit reached.');
   snapshot.comments.push({id:crypto.randomUUID(),planId:plan.id,decisionId:decision!.id,authorId:actor,decisionVersion:decision!.version,text,createdAt:now});break;
  }
  case 'confirm':{
   ownerOnly();if(!decision!.options.some(o=>o.id===command.optionId))throw new Error('Choose a current option.');
   const {ballots,missing}=decisionParticipation(decision!);const consent=ballots.filter(b=>b.response==='support'||b.response==='can_live_with');
   if(missing.length||ballots.some(b=>b.response==='object')||!consent.length||consent.some(b=>b.optionId!==command.optionId))throw new Error('Every member must respond and objections must be resolved before confirmation.');
   decision!.selectedOptionId=command.optionId;decision!.confirmation={by:actor,at:now,decisionVersion:decision!.version};invalidate();break;
  }
  case 'reopenDecision':ownerOnly();decision!.version++;decision!.ballots=[];decision!.selectedOptionId=null;decision!.confirmation=null;invalidate();break;
  case 'finalize':{
   ownerOnly();const required=snapshot.decisions.filter(d=>d.required);
   if(!command.reviewed||!required.length||required.some(d=>status(d)!=='confirmed')||snapshot.decisions.some(d=>decisionParticipation(d).ballots.some(b=>b.response==='object')))throw new Error('Confirm every required decision, resolve objections and review the itinerary first.');
   snapshot.finalization={by:actor,at:now,planRevision:snapshot.plan_revision+1,decisionVersions:Object.fromEntries(required.map(d=>[d.id,d.version]))};snapshot.lastFinalizationKey=command.idempotencyKey;break;
  }
  case 'reopenPlan':ownerOnly();invalidate();break;
 }
 snapshot.plan_revision++;snapshot.last_activity_at=now;snapshot.demoSignature=signature(plan);
 return derive(snapshot);
}

function validateOptions(options:string[]){const cleaned=options.map(s=>s.trim());if(cleaned.length>12||cleaned.some(s=>!s||s.length>300)||new Set(cleaned.map(s=>s.toLowerCase())).size!==cleaned.length)throw new Error('Use up to 12 distinct options, each 1–300 characters.');return cleaned;}
