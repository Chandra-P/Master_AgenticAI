import {createClient,type SupabaseClient} from '@supabase/supabase-js';
import type {Plan,CreatePlanInput,Preference,Group,GroupDraft} from './types';
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
const READ_RETRY_DELAYS_MS=[1000,3000,7000,12000,20000] as const;
function waitForRetry(delay:number,signal:AbortSignal){
 return new Promise<void>((resolve,reject)=>{
  if(signal.aborted){reject(signal.reason??new DOMException('Aborted','AbortError'));return;}
  const finish=()=>{signal.removeEventListener('abort',abort);resolve();};
  const timer=setTimeout(finish,delay);
  const abort=()=>{clearTimeout(timer);signal.removeEventListener('abort',abort);reject(signal.reason??new DOMException('Aborted','AbortError'));};
  signal.addEventListener('abort',abort,{once:true});
 });
}
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
    const maxAttempts=read?READ_RETRY_DELAYS_MS.length+1:1;
    for(let attempt=0;attempt<maxAttempts;attempt++){
      signal.throwIfAborted();
      assertScope();
      let result:Response;
      try{
        result=await fetch('/api/backend'+path,{...options,headers:{'Content-Type':'application/json',Authorization:'Bearer '+session.access_token,'X-Workspace-Mode':readWorkspaceRole(session.user.id),...options.headers},signal});
      }catch(error){
        if(signal.aborted)throw error;
        if(read&&attempt<READ_RETRY_DELAYS_MS.length){await waitForRetry(READ_RETRY_DELAYS_MS[attempt],signal);continue;}
        throw new ApiError(unavailable,503);
      }
      const contentType=result.headers.get('content-type')?.toLowerCase()||'';
      const isGatewayFailure=[502,503,504].includes(result.status);
      // Render's cold-start proxy returns HTML for transient gateway failures.
      // JSON 5xx responses came from the API itself, so surface them immediately.
      if(read&&attempt<READ_RETRY_DELAYS_MS.length&&isGatewayFailure&&!contentType.includes('json')){
        await result.body?.cancel().catch(()=>{});
        await waitForRetry(READ_RETRY_DELAYS_MS[attempt],signal);
        continue;
      }
      let data:unknown;
      try{data=await result.json();}catch{
        if(signal.aborted)signal.throwIfAborted();
        if(read&&attempt===0&&result.ok){await waitForRetry(READ_RETRY_DELAYS_MS[attempt],signal);continue;}
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
  groups(){return this.request<Group[]>('/v1/groups');}
  group(id:string,scope?:RequestScope){return this.request<Group>('/v1/groups/'+encodeURIComponent(id),{},scope);}
  groupSharing(group:Group,shared:boolean){return this.request<Group>('/v1/groups/'+encodeURIComponent(group.id)+'/sharing',{method:'POST',body:JSON.stringify({shared,expected_revision:group.revision})});}
  saveGroup(draft:GroupDraft,group?:Group,revision?:number){return this.request<Group>(group?'/v1/groups/'+encodeURIComponent(group.id):'/v1/groups',{method:group?'PATCH':'POST',body:JSON.stringify(group?{...draft,archived:group.archived,expected_revision:revision??group.revision}:draft)});}
  archiveGroup(group:Group,archived:boolean,revision?:number){return this.request<Group>('/v1/groups/'+encodeURIComponent(group.id),{method:'PATCH',body:JSON.stringify({name:group.name,theme:group.theme,members:group.members,archived,expected_revision:revision??group.revision})});}
  removeGroup(group:Group,revision?:number){return this.request<{status:string}>('/v1/groups/'+encodeURIComponent(group.id),{method:'DELETE',body:JSON.stringify({expected_revision:revision??group.revision})});}
  create(input:CreatePlanInput){const {groupId,expectedGroupRevision,shareWithGroup,...fields}=input;return this.request<Plan>('/v1/plans',{method:'POST',body:JSON.stringify({...fields,...(groupId?{group_id:groupId,expected_group_revision:expectedGroupRevision,share_with_group:shareWithGroup??false}:{})})});}
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

