import {ApiError,ConnectedService} from './connected';

export type DecisionResponse='support'|'can_live_with'|'object'|'abstain';
export type DecisionStatus='needs_options'|'awaiting_responses'|'needs_discussion'|'ready_to_confirm'|'confirmed'|'reopened';
export interface OptionProvenance {url:string;retrievedAt:string;excerpt:string}
export interface DecisionOptionDetails {label:string;url?:string;notes?:string;estimatedCostPerPerson?:number|null;image?:string;sourceIds?:string[];provenance?:OptionProvenance}
export interface DecisionOption extends DecisionOptionDetails {id:string;sourceIds:string[]}
export interface Decision {
 id:string;planId:string;title:string;category:string;required:boolean;status:DecisionStatus;version:number;
 options:DecisionOption[];eligibleMemberIds:string[];
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
 |{kind:'create';title:string;category:string;required:boolean;options:string[];optionDetails?:DecisionOptionDetails[]}
 |{kind:'edit';decisionId:string;title?:string;required?:boolean;options?:string[];optionDetails?:DecisionOptionDetails[]}
 |{kind:'respond';decisionId:string;optionId:string|null;response:DecisionResponse}
 |{kind:'comment';decisionId:string;text:string}
 |{kind:'confirm';decisionId:string;optionId:string}
 |{kind:'reopenDecision';decisionId:string}
 |{kind:'finalize';reviewed:true;idempotencyKey:string}
 |{kind:'reopenPlan'};

interface DecisionRequestContext {memberId?:string;isCurrent?:()=>boolean}
const requestScope=(context:DecisionRequestContext)=>({userId:context.memberId,isCurrent:context.isCurrent});

export class DecisionService {
 constructor(private api:ConnectedService){}
 async load(planId:string,context:DecisionRequestContext={}){return validateDecisionSnapshot(await this.api.request<unknown>('/v1/plans/'+encodeURIComponent(planId)+'/decisions',undefined,requestScope(context)),planId);}
 comments(planId:string,decisionId:string,offset=0,context:DecisionRequestContext={}){return this.api.request<DecisionComment[]>('/v1/plans/'+encodeURIComponent(planId)+'/decisions/'+encodeURIComponent(decisionId)+'/comments?offset='+offset+'&limit=50',undefined,requestScope(context));}
 summarize(snapshot:DecisionSnapshot,decisionId:string,context:DecisionRequestContext={}){
  const decision=snapshot.decisions.find(d=>d.id===decisionId);if(!decision)throw new Error('Decision not found.');
  return this.api.request<DecisionSummary>('/v1/plans/'+encodeURIComponent(snapshot.plan_id)+'/decisions/'+encodeURIComponent(decisionId)+'/summary',{method:'POST',body:JSON.stringify({expected_revision:snapshot.plan_revision,expected_version:decision.version})},requestScope(context));
 }
 async execute(snapshot:DecisionSnapshot,command:DecisionCommand,context:DecisionRequestContext={}){
  const current=context.isCurrent||(()=>true);
  if(!current())throw new Error('The workspace changed. Review the current plan before saving.');
  try{return await this.write(snapshot,command,context);}
  catch(error){
   // A 409 guarantees this command was not applied. Never retry uncertain writes.
   if(!(error instanceof ApiError)||error.status!==409||!context.isCurrent||(command.kind!=='respond'&&command.kind!=='comment'))throw error;
   const latest=await this.load(snapshot.plan_id,context);
   if(!current())throw new Error('The workspace changed. Review the current plan before saving.');
   const previous=snapshot.decisions.find(d=>d.id===command.decisionId),decision=latest.decisions.find(d=>d.id===command.decisionId);
   if(!previous||!decision||decision.version!==previous.version||decision.eligibleMemberIds.length!==previous.eligibleMemberIds.length||previous.eligibleMemberIds.some(id=>!decision.eligibleMemberIds.includes(id)))throw new Error('This decision changed. Review its latest options before saving.');
   if(command.kind==='respond'){
    const member=context.memberId;
    if(!member||!decision.eligibleMemberIds.includes(member)||latest.finalized||decision.status==='confirmed')throw new Error('This decision changed. Review the current responses before saving.');
    const oldVote=previous.ballots.find(b=>b.memberId===member),newVote=decision.ballots.find(b=>b.memberId===member);
    if(oldVote?.response!==newVote?.response||oldVote?.optionId!==newVote?.optionId||oldVote?.decisionVersion!==newVote?.decisionVersion)throw new Error('Your response changed on another device. Review it before saving.');
   }
   // Exactly one rebase; the server still validates both current revisions.
   return this.write(latest,command,context);
  }
 }
 private async write(snapshot:DecisionSnapshot,command:DecisionCommand,context:DecisionRequestContext){
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
  if((command.kind==='create'||command.kind==='edit')&&command.optionDetails)data.option_details=command.optionDetails;
  return validateDecisionSnapshot(await this.api.request<unknown>(path,{method,body:JSON.stringify(data)},requestScope(context)),snapshot.plan_id);
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
