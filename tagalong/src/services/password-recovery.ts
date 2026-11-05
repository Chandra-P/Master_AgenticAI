import {createClient} from '@supabase/supabase-js';
import type {PublicConfig} from './connected';
import {clearWorkspaceRole} from './workspace-role';
const key='tagalong-password-recovery';
let captured=false;
export function recoveryRequestError(error:unknown){
 const code=typeof error==='object'&&error!==null&&'code' in error?error.code:undefined;
 if(code==='over_email_send_rate_limit')return 'The email limit has been reached. Use the most recent reset email if one arrived, or wait an hour before requesting another.';
 if(code==='over_request_rate_limit')return 'Too many requests. Wait at least a minute before trying again, or use the most recent reset email.';
 if(code==='email_address_not_authorized')return 'The email service cannot send to this address yet. The app administrator needs to configure outgoing email.';
 return 'Could not send the reset email. If one already arrived, use the most recent link. Otherwise, try again later.';
}
interface Recovery {userId:string|null;startedAt:number}
export function recoveryContext():Recovery|null{try{const value=JSON.parse(sessionStorage.getItem(key)||'null');if(value&&typeof value.startedAt==='number'&&Date.now()-value.startedAt<3600000&&(value.userId===null||typeof value.userId==='string'))return value;sessionStorage.removeItem(key);}catch{}return null;}
export function clearRecovery(){try{sessionStorage.removeItem(key);}catch{}}
export function markRecovery(userId:string|null){clearWorkspaceRole();try{sessionStorage.setItem(key,JSON.stringify({userId,startedAt:recoveryContext()?.startedAt||Date.now()}));}catch{}}
export function captureRecoveryLocation(){if(typeof window==='undefined')return false;if(!captured){captured=true;const params=new URLSearchParams(window.location.hash.slice(1));if(params.get('type')==='recovery'||params.get('error_code')==='otp_expired'){clearRecovery();markRecovery(null);}}const recovering=Boolean(recoveryContext());if(recovering)clearWorkspaceRole();return recovering;}
export function clearRecoveryLocation(){if(typeof window!=='undefined'&&window.location.hash)window.history.replaceState(null,'',window.location.pathname+window.location.search);}

export async function updateRecoveredPassword(config:PublicConfig,password:string){
 const expected=recoveryContext();
 if(!expected?.userId)throw new Error('This recovery link is invalid or expired. Request a new one.');
 const {getAuth}=await import('./connected');const auth=getAuth(config);
 const {data:{session}}=await auth.auth.getSession();
 if(!session||session.user.id!==expected.userId)throw new Error('Recovery account changed. Request a new reset link.');
 // Bind this operation to the verified recovery session, independent of a concurrent account switch.
 const isolated=createClient(config.supabaseUrl,config.supabaseAnonKey,{auth:{persistSession:false,autoRefreshToken:false,detectSessionInUrl:false,storageKey:'tagalong-recovery-isolated'}});
 const loaded=await isolated.auth.setSession({access_token:session.access_token,refresh_token:session.refresh_token});
 if(loaded.error||loaded.data.user?.id!==expected.userId)throw new Error('This recovery link is invalid or expired. Request a new one.');
 const current=recoveryContext();
 if(current?.userId!==expected.userId||current.startedAt!==expected.startedAt)throw new Error('Recovery was cancelled. Request a new reset link.');
 const result=await isolated.auth.updateUser({password});
 if(result.error)throw result.error;
 return expected.userId;
}
