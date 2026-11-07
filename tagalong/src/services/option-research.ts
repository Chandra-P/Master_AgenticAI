import {ConnectedService,getAuth,type PublicConfig} from './connected';
import type {OptionProvenance} from './decisions';
export interface ResearchFinding {text:string;source_ids:string[]}
export interface ResearchAssessment {option_id:string;verdict:'fits'|'conflicts'|'needs_info';basis:'saved_group_context'|'confirmed_plan_facts'|'insufficient_context';summary:string;matches:ResearchFinding[];conflicts:ResearchFinding[];unknowns:string[]}
export interface ResearchOption {id:string;name:string;details:string;url?:string;image?:string;estimated_cost_per_person?:number|null;source_ids:string[];provenance?:OptionProvenance;assessment?:ResearchAssessment|null}
export interface ResearchResult {plan_id:string;plan_revision:number;query:string;sources:{id:string;title:string;text:string;retrieval_origin?:string}[];options:ResearchOption[];steps:{id:string;label:string;status:'completed'|'unavailable'|'skipped'|'pending'|'failed';detail:string}[];assessment_status:'available'|'unavailable'|'skipped';index_freshness:{status:'current'|'pending'|'failed';current_sources:number;indexed_sources:number;pending_sources:number;failed_sources:number};context_truncated:boolean}
export class OptionResearchService {
 private api:ConnectedService;
 constructor(config:PublicConfig){this.api=new ConnectedService(getAuth(config));}
 search(planId:string,revision:number,query:string,category:string,location:string,signal:AbortSignal,userId:string,isCurrent:()=>boolean){
  return this.api.request<ResearchResult>('/v1/plans/'+encodeURIComponent(planId)+'/research',{method:'POST',body:JSON.stringify({expected_revision:revision,query,category,location}),signal},{userId,isCurrent});
 }
}
