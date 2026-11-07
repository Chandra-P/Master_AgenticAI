import {ConnectedService} from './connected';

export type DecisionResponse='support'|'can_live_with'|'object'|'abstain';
export type DecisionStatus='needs_options'|'awaiting_responses'|'needs_discussion'|'ready_to_confirm'|'confirmed'|'reopened';
export interface Decision {
 id:string;planId:string;title:string;category:string;required:boolean;status:DecisionStatus;version:number;
 options:{id:string;label:string;sourceIds:string[]}[];eligibleMemberIds:string[];
 ballots:{memberId:string;optionId:string|null;response:DecisionResponse;decisionVersion:number;updatedAt:string}[];
 selectedOptionId:string|null;confirmation:null|{by:string;at:string;decisionVersion:number};
}
export interface DecisionComment {id:string;planId:string;decisionId:string;authorId:string;decisionVersion:number;text:string;createdAt:string}
export interface DecisionSummary {decisionId:string;decisionVersion:number;planRevision:number;text:string;sources:{id:string;title:string;text:string;version:number}[];generatedAt:string|null;providerStatus:'live'|'unavailable'}
export interface DecisionSnapshot {
 plan_id:string;plan_revision:number;decisions:Decision[];comments:DecisionComment[];score:number;finalized:boolean;
 finalization:null|{by:string;at:string;planRevision:number;decisionVersions:Record<string,number>};last_activity_at:string|null;comment_counts?:Record<string,number>;
}
export type DecisionCommand=
 |{kind:'create';title:string;category:string;required:boolean;options:string[]}
 |{kind:'edit';decisionId:string;title?:string;required?:boolean;options?:string[]}
 |{kind:'respond';decisionId:string;optionId:string|null;response:DecisionResponse}
 |{kind:'comment';decisionId:string;text:string}
 |{kind:'confirm';decisionId:string;optionId:string}
 |{kind:'reopenDecision';decisionId:string}
 |{kind:'finalize';reviewed:true;idempotencyKey:string}
 |{kind:'reopenPlan'};

export const decisionStatusLabel=(status:DecisionStatus)=>({needs_options:'Needs options',awaiting_responses:'Awaiting responses',needs_discussion:'Needs discussion',ready_to_confirm:'Ready to confirm',confirmed:'Confirmed',reopened:'Reopened'}[status]);

export class DecisionService {
 constructor(private api:ConnectedService){}
 async load(planId:string){return validateDecisionSnapshot(await this.api.request<unknown>('/v1/plans/'+encodeURIComponent(planId)+'/decisions'),planId);}
 comments(planId:string,decisionId:string,offset=0){return this.api.request<DecisionComment[]>('/v1/plans/'+encodeURIComponent(planId)+'/decisions/'+encodeURIComponent(decisionId)+'/comments?offset='+offset+'&limit=50');}
 summarize(snapshot:DecisionSnapshot,decisionId:string){
  const decision=snapshot.decisions.find(d=>d.id===decisionId);if(!decision)throw new Error('Decision not found.');
  return this.api.request<DecisionSummary>('/v1/plans/'+encodeURIComponent(snapshot.plan_id)+'/decisions/'+encodeURIComponent(decisionId)+'/summary',{method:'POST',body:JSON.stringify({expected_revision:snapshot.plan_revision,expected_version:decision.version})});
 }
 async execute(snapshot:DecisionSnapshot,command:DecisionCommand){
  const base='/v1/plans/'+encodeURIComponent(snapshot.plan_id);
  const data:Record<string,unknown>={expected_revision:snapshot.plan_revision};
  let path=base+'/decisions';let method='POST';
  if('decisionId' in command){
   const decision=snapshot.decisions.find(d=>d.id===command.decisionId);
   if(!decision)throw new Error('Decision is no longer available. Reload this plan.');
   path+='/'+encodeURIComponent(decision.id);data.expected_version=decision.version;
  }
  switch(command.kind){
   case 'create':Object.assign(data,{title:command.title,category:command.category,required:command.required,options:command.options});break;
   case 'edit':method='PATCH';for(const field of ['title','required','options'] as const)if(command[field]!==undefined)data[field]=command[field];break;
   case 'respond':path+='/response';method='PUT';Object.assign(data,{option_id:command.optionId,response:command.response});break;
   case 'comment':path+='/comments';data.text=command.text;break;
   case 'confirm':path+='/confirm';data.option_id=command.optionId;break;
   case 'reopenDecision':path+='/reopen';break;
   case 'finalize':path=base+'/finalize';Object.assign(data,{idempotency_key:command.idempotencyKey,reviewed:command.reviewed});break;
   case 'reopenPlan':path=base+'/reopen';break;
  }
  return validateDecisionSnapshot(await this.api.request<unknown>(path,{method,body:JSON.stringify(data)}),snapshot.plan_id);
 }
}

export function validateDecisionSnapshot(value:unknown,planId:string):DecisionSnapshot {
 const snapshot=value as DecisionSnapshot|null;
 if(!snapshot||snapshot.plan_id!==planId||!Number.isInteger(snapshot.plan_revision)||!Array.isArray(snapshot.decisions)||!Array.isArray(snapshot.comments)||!Number.isFinite(snapshot.score)||snapshot.score<0||snapshot.score>100||typeof snapshot.finalized!=='boolean'||snapshot.decisions.some(d=>!d||typeof d.id!=='string'||typeof d.title!=='string'||!Array.isArray(d.options)||!Array.isArray(d.ballots)||!Array.isArray(d.eligibleMemberIds))){
  throw new Error('The decision service returned an unexpected response. Please reload this plan.');
 }
 return snapshot;
}

export function decisionParticipation(decision:Decision){
 const ballots=decision.ballots.filter(b=>b.decisionVersion===decision.version&&decision.eligibleMemberIds.includes(b.memberId));
 const missing=decision.eligibleMemberIds.filter(id=>!ballots.some(b=>b.memberId===id));
 return {ballots,missing};
}

export function decisionNextAction(snapshot:DecisionSnapshot){
 const required=snapshot.decisions.filter(d=>d.required);
 const decision=required.find(d=>d.status!=='confirmed');
 return decision?{label:decision.options.length?'Review '+decision.title.toLowerCase():'Propose '+decision.title.toLowerCase(),decisionId:decision.id}
  :{label:snapshot.finalized?'View final itinerary':'Review and finalize',decisionId:null};
}
