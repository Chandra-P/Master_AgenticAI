import {ConnectedService} from './connected';
import type {ReviewedSuggestion} from './idea-discovery';
export interface PlanDraft {suggested_interests?:string[];interest_reason?:string;title:string;type:'outing'|'trip';location:string;start:string|null;end:string|null;participant_count:number|null;suggested_tasks:string[];suggested_itinerary:{title:string;time:string;category:string;location:string}[];suggested_budget:{amount:number|null;basis:'per_person'|'total'|'unknown';currency:string;notes:string};open_questions:string[]}
export interface DraftResponse {draft_id:string;draft:PlanDraft;mode:'live';notice:string}
export interface AcceptDraft {draft_id:string;title:string;kind:'outing'|'trip';location:string;start:string;end:string;budget_per_person:number|null;reviewed_suggestions?:ReviewedSuggestion[];group_id?:string;expected_group_revision?:number;share_with_group?:boolean}
export interface Coordination {plan_id:string;plan_revision:number;title:string;status:string;health:number;inactive_days:number;next_step:string;reason:string;target_tab:string;summary:string;decisions_made:string[];open_questions:string[];blockers:string[];activity_ideas:{title:string;reason:string;preference_labels:string[]}[];provider_status:'pending'|'live'|'unavailable';stale:boolean;generated_at:string|null;ai_next_step?:string|null;ai_reason?:string|null;last_activity_at:string|null}
export interface CoordinationOverview {plans:Coordination[];group_insights:{label:string;plan_count:number}[];notice:string}
export const statusLabel=(status:string)=>({WAITING_FOR_DATE:'Choose a date',WAITING_FOR_VOTES:'Waiting for votes',WAITING_FOR_LOCATION:'Choose a location',READY_TO_FINALIZE:'Ready to finalize',ACTIVE:'Planning in progress',COMPLETED:'Completed',STALLED:'Needs a little momentum'}[status]||'Planning in progress');
export class CoordinationService {
 constructor(private api:ConnectedService){}
 generate(prompt:string){const now=new Date();const local_date=[now.getFullYear(),String(now.getMonth()+1).padStart(2,'0'),String(now.getDate()).padStart(2,'0')].join('-');return this.api.request<DraftResponse>('/v1/plans/generate',{method:'POST',body:JSON.stringify({prompt,local_date})});}
 overview(){return this.api.request<CoordinationOverview>('/v1/coordination/overview');}
 plan(id:string){return this.api.request<Coordination>('/v1/plans/'+encodeURIComponent(id)+'/coordination');}
}
