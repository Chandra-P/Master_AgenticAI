import {ConnectedService,type RequestScope} from './connected';
import type {Plan} from './types';

export interface DemoStory {
 planId:string;template:'austin-four-friends';scripted:true;title:string;disclosure:string;referenceDate:string;
 liveCheck?:{status:string;at:string;sourceIds:string[];model:string;simulation:false;tools:{tool:string;status:string;match_count:number}[]};
 cast:{name:string;color:string}[];
 sources:{id:string;title:string;text:string}[];
 choices:{category:string;label:string;url?:string;estimate:number|null;image?:string;alternatives?:string[];reason?:string;votes?:Record<string,string>;sourceIds?:string[]}[];
 milestones:{id:string;title:string;text:string;sourceIds:string[];ai?:boolean;votes?:Record<string,string>}[];
 days:{date:string;title:string;items:{time:string;title:string;location:string;image:string}[]}[];
}

export class DemoPlanService {
 constructor(private api:ConnectedService){}
 create(idempotencyKey:string,scope:RequestScope){return this.api.request<Plan>('/v1/demo-plans',{method:'POST',body:JSON.stringify({template:'austin-four-friends',idempotency_key:idempotencyKey})},scope);}
 story(planId:string,scope:RequestScope){return this.api.request<DemoStory>('/v1/plans/'+encodeURIComponent(planId)+'/demo-story',{},scope);}
}
