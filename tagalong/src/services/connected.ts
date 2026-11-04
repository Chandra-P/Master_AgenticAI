import {createClient,type SupabaseClient} from '@supabase/supabase-js';
import type {Plan,CreatePlanInput,Preference} from './types';

export interface PublicConfig {supabaseUrl:string;supabaseAnonKey:string;connectedReady:boolean}
export interface CurrentUser {id:string;email:string;name:string}
export interface Source {id:string;title:string;text:string}
export interface Proposal {id:string;label?:string;status:string;kind?:string;payload?:Record<string,unknown>;[key:string]:unknown}
export interface AssistantReply {text:string;preferences:Preference[];sources:Source[];mode:'live';proposal_ids:string[]}
let client:SupabaseClient|undefined;
export function getAuth(config:PublicConfig) {
  if(!config.supabaseUrl || !config.supabaseAnonKey) throw new Error('Shared workspace needs Supabase and the API configuration.');
  return client ||= createClient(config.supabaseUrl,config.supabaseAnonKey);
}
export class ApiError extends Error {constructor(message:string,public status:number){super(message);}}
export class ConnectedService {
  constructor(private auth:SupabaseClient) {}
  async request<T>(path:string,options:RequestInit={}):Promise<T> {
    const {data:{session},error}=await this.auth.auth.getSession();
    if(error || !session) throw new ApiError('Your session ended. Please sign in again.',401);
    const result=await fetch('/api/backend'+path,{...options,headers:{'Content-Type':'application/json',Authorization:'Bearer '+session.access_token,...options.headers},signal:AbortSignal.timeout(65_000)});
    const data=await result.json().catch(()=>({detail:'Unexpected response from the shared workspace.'}));
    if(!result.ok) throw new ApiError(typeof data.detail==='string'?data.detail:'This change could not be saved. Please check your input.',result.status);
    return data as T;
  }
  me(){return this.request<CurrentUser>('/v1/me');}
  plans(){return this.request<Plan[]>('/v1/plans');}
  plan(id:string){return this.request<Plan>('/v1/plans/'+encodeURIComponent(id));}
  create(input:CreatePlanInput){return this.request<Plan>('/v1/plans',{method:'POST',body:JSON.stringify(input)});}
  save(plan:Plan,revision:number){return this.request<Plan>('/v1/plans/'+encodeURIComponent(plan.id),{method:'PUT',body:JSON.stringify({plan,expected_revision:revision})});}
  assistant(id:string,message:string){return this.request<AssistantReply>('/v1/plans/'+encodeURIComponent(id)+'/assistant',{method:'POST',body:JSON.stringify({message})});}
  proposals(id:string){return this.request<Proposal[]>('/v1/plans/'+encodeURIComponent(id)+'/proposals');}
  confirm(id:string,proposal:string){return this.request<Plan>('/v1/plans/'+encodeURIComponent(id)+'/proposals/'+encodeURIComponent(proposal)+'/confirm',{method:'POST',body:'{}'});}
  share(id:string,email:string){return this.request<{status:string}>('/v1/plans/'+encodeURIComponent(id)+'/members',{method:'POST',body:JSON.stringify({email})});}
}
