import {ConnectedService} from './connected';
import type {Plan} from './types';
export interface AdminEvent {id:string;at:string;actor_id:string;action:string;target:string;reason:string}
export interface AdminOverview {
 counts:{plans:number;accounts:number;qa_plans:number};
 plans:{id:string;title:string;owner_id:string;members:number;revision:number;qa:boolean;deleted:boolean}[];
 accounts:{id:string;email:string;display_name:string;app_admin:boolean;suspended:boolean}[];
 jobs:Record<string,number>;audit:AdminEvent[];offset:number;limit:number;
}
export interface AdminInspection {plan:Omit<Plan,'role'>&{role:'admin_review'};documents:{id:string;title:string;text:string}[];audit_id:string;deleted:boolean}
export class AdminService {
 constructor(private api:ConnectedService){}
 overview(offset=0){return this.api.request<AdminOverview>('/v1/admin/overview?offset='+offset+'&limit=50');}
 inspect(id:string,reason:string){return this.api.request<AdminInspection>('/v1/admin/plans/'+encodeURIComponent(id)+'/inspect',{method:'POST',body:JSON.stringify({reason})});}
 suspend(id:string,suspended:boolean,reason:string){return this.api.request<{status:string}>('/v1/admin/accounts/'+encodeURIComponent(id)+'/suspension',{method:'POST',body:JSON.stringify({suspended,reason})});}
 qa(){return this.api.request<{plan_ids:string[]}>('/v1/admin/qa-plans',{method:'POST',body:'{}'});}
}
