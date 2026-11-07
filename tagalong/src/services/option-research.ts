import {ConnectedService,getAuth,type PublicConfig} from './connected';
import type {OptionProvenance} from './decisions';
export interface ResearchOption {id:string;name:string;details:string;url?:string;image?:string;estimated_cost_per_person?:number|null;source_ids:string[];provenance?:OptionProvenance}
export interface ResearchResult {plan_id:string;plan_revision:number;query:string;sources:{id:string;title:string;text:string}[];options:ResearchOption[];steps:{id:string;label:string;status:'completed'|'unavailable'|'skipped';detail:string}[];context_truncated:boolean}
export class OptionResearchService {
 private api:ConnectedService;
 constructor(config:PublicConfig){this.api=new ConnectedService(getAuth(config));}
 search(planId:string,revision:number,query:string,category:string,location:string,signal:AbortSignal,userId:string,isCurrent:()=>boolean){
  return this.api.request<ResearchResult>('/v1/plans/'+encodeURIComponent(planId)+'/research',{method:'POST',body:JSON.stringify({expected_revision:revision,query,category,location}),signal},{userId,isCurrent});
 }
}
