import {createClient,type SupabaseClient} from '@supabase/supabase-js';
import type {Plan,CreatePlanInput,Preference} from './types';
import {createPlanPatches} from './plan-patches';
import {readWorkspaceRole} from './workspace-role';
import {captureRecoveryLocation,markRecovery} from './password-recovery';

export interface PublicConfig {supabaseUrl:string;supabaseAnonKey:string;connectedReady:boolean;requireConnected?:boolean}
export interface CurrentUser {id:string;email:string;name:string;display_name?:string;app_admin?:boolean;workspace_mode?:'member'|'admin'}
export interface Source {id:string;title:string;text:string}
export interface DocumentSource extends Source {version:number;deleted:boolean;kind?:string}
export interface Proposal {id:string;label?:string;status:string;kind?:string;payload?:Record<string,unknown>;[key:string]:unknown}
export interface AssistantReply {text:string;preferences:Preference[];sources:Source[];mode:'live';proposal_ids:string[]}
let client:SupabaseClient|undefined;
export function getAuth(config:PublicConfig) {
  if(!config.supabaseUrl || !config.supabaseAnonKey) throw new Error('Shared workspace needs Supabase and the API configuration.');
  if(!client){captureRecoveryLocation();client=createClient(config.supabaseUrl,config.supabaseAnonKey);client.auth.onAuthStateChange((event,session)=>{if(event==='PASSWORD_RECOVERY')markRecovery(session?.user.id||null);});}
  return client;
}
export class ApiError extends Error {constructor(message:string,public status:number){super(message);}}
export interface RequestScope {userId?:string;isCurrent?:()=>boolean}
export class ConnectedService {
  constructor(private auth:SupabaseClient) {}
  async request<T>(path:string,options:RequestInit={},scope?:RequestScope):Promise<T> {
    const {data:{session},error}=await this.auth.auth.getSession();
    if(error || !session) throw new ApiError('Your session ended. Please sign in again.',401);
    const assertScope=()=>{if(scope&&((scope.userId&&session.user.id!==scope.userId)||(scope.isCurrent&&!scope.isCurrent())))throw new ApiError('Your account or workspace changed. Review the current plan before saving.',401);};
    assertScope();
    const timeout=AbortSignal.timeout(65_000);
    const signal=options.signal?AbortSignal.any([options.signal,timeout]):timeout;
    const read=(options.method||'GET').toUpperCase()==='GET';
    const unavailable='Shared workspace is temporarily unavailable. Please wait a moment and try again.';
    for(let attempt=0;attempt<2;attempt++){
      signal.throwIfAborted();
      assertScope();
      let result:Response;
      try{
        result=await fetch('/api/backend'+path,{...options,headers:{'Content-Type':'application/json',Authorization:'Bearer '+session.access_token,'X-Workspace-Mode':readWorkspaceRole(session.user.id),...options.headers},signal});
      }catch(error){
        if(signal.aborted)throw error;
        if(read&&attempt===0)continue;
        throw new ApiError(unavailable,503);
      }
      if(read&&attempt===0&&[502,503,504].includes(result.status)){
        await result.body?.cancel().catch(()=>{});
        continue;
      }
      let data:unknown;
      try{data=await result.json();}catch{
        if(signal.aborted)signal.throwIfAborted();
        if(read&&attempt===0&&result.ok)continue;
        throw new ApiError(unavailable,result.ok?503:result.status);
      }
      if(!result.ok){
        const detail=data&&typeof data==='object'&&'detail' in data?data.detail:null;
        throw new ApiError(typeof detail==='string'?detail:'This change could not be saved. Please check your input.',result.status);
      }
      return data as T;
    }
    throw new ApiError(unavailable,503);
  }
  me(){return this.request<CurrentUser>('/v1/me');}
  plans(){return this.request<Plan[]>('/v1/plans');}
  plan(id:string){return this.request<Plan>('/v1/plans/'+encodeURIComponent(id));}
  create(input:CreatePlanInput){return this.request<Plan>('/v1/plans',{method:'POST',body:JSON.stringify(input)});}
  deletePlan(id:string,revision:number,confirmation:string){return this.request<{status:string}>('/v1/plans/'+encodeURIComponent(id),{method:'DELETE',body:JSON.stringify({expected_revision:revision,confirmation})});}
  transferOwner(id:string,revision:number,userId:string){return this.request<Plan>('/v1/plans/'+encodeURIComponent(id)+'/owner',{method:'POST',body:JSON.stringify({expected_revision:revision,user_id:userId})});}
  save(plan:Plan,revision:number,previous:Plan){const patches=createPlanPatches(previous,plan);return patches.length?this.request<Plan>('/v1/plans/'+encodeURIComponent(plan.id),{method:'PATCH',body:JSON.stringify({patches,expected_revision:revision})}):Promise.resolve(previous);}
  assistant(id:string,message:string){return this.request<AssistantReply>('/v1/plans/'+encodeURIComponent(id)+'/assistant',{method:'POST',body:JSON.stringify({message})});}
  typingSuggestion(id:string,draft:string,revision:number,signal:AbortSignal){return this.request<{suggestion:string;source:'model'}>('/v1/plans/'+encodeURIComponent(id)+'/typing-suggestion',{method:'POST',body:JSON.stringify({draft,expected_revision:revision}),signal});}
  proposals(id:string){return this.request<Proposal[]>('/v1/plans/'+encodeURIComponent(id)+'/proposals');}
  confirm(id:string,proposal:string){return this.request<Plan>('/v1/plans/'+encodeURIComponent(id)+'/proposals/'+encodeURIComponent(proposal)+'/confirm',{method:'POST',body:'{}'});}
  share(id:string,email:string){return this.request<{status:string}>('/v1/plans/'+encodeURIComponent(id)+'/members',{method:'POST',body:JSON.stringify({email})});}
  invitation(id:string){return this.request<{token:string;expires_at:string}>('/v1/plans/'+encodeURIComponent(id)+'/invitation',{method:'POST',body:'{}'});}
  disableInvitation(id:string){return this.request<{status:string}>('/v1/plans/'+encodeURIComponent(id)+'/invitation',{method:'DELETE'});}
  acceptInvitation(token:string){return this.request<{plan_id:string}>('/v1/invitations/accept',{method:'POST',body:JSON.stringify({token})});}
  revoke(id:string,userId:string){return this.request<{status:string}>('/v1/plans/'+encodeURIComponent(id)+'/members/'+encodeURIComponent(userId),{method:'DELETE'});}
  documents(id:string){return this.request<DocumentSource[]>('/v1/plans/'+encodeURIComponent(id)+'/documents');}
  addDocument(id:string,title:string,text:string){return this.request<{id:string;status:string}>('/v1/plans/'+encodeURIComponent(id)+'/documents',{method:'POST',body:JSON.stringify({title,text,content_type:'text/plain'})});}
  removeDocument(id:string,sourceId:string){return this.request<{status:string}>('/v1/plans/'+encodeURIComponent(id)+'/documents/'+encodeURIComponent(sourceId),{method:'DELETE'});}
}
