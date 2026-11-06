import {ConnectedService,getAuth,type PublicConfig} from './connected';

export interface GroupFitOption {name:string;details:string;url?:string;estimated_cost_per_person?:number}
export interface GroupFitReason {text:string;source_ids:string[]}
export interface GroupFitResult {
 verdict:'fits'|'conflicts'|'needs_info';
 summary:string;
 matches:GroupFitReason[];
 conflicts:GroupFitReason[];
 unknowns:string[];
 sources:{id:string;title:string;text:string}[];
 retrieval_status:'available'|'unavailable';
 context_truncated:boolean;
}

export class GroupFitService {
 private api:ConnectedService;
 constructor(config:PublicConfig){this.api=new ConnectedService(getAuth(config));}
 assess(planId:string,revision:number,option:GroupFitOption,signal:AbortSignal){
  return this.api.request<GroupFitResult>('/v1/plans/'+encodeURIComponent(planId)+'/group-fit',{
   method:'POST',body:JSON.stringify({expected_revision:revision,option}),signal,
  });
 }
}
