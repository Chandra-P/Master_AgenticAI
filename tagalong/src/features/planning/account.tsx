'use client';
import Link from 'next/link';
import {pendingInvitation} from '@/services/invitation-session';
import {useState} from 'react';
import {usePlanning} from './store';
import {getAuth} from '@/services/connected';
import {clearWorkspaceRole} from '@/services/workspace-role';
import {PasswordRecovery,ResetRequest} from './password-recovery';
import {Button} from '@/components/ui/button';

export function Account(){const {user,mode,passwordRecovery}=usePlanning();if(passwordRecovery)return <PasswordRecovery/>;return <AccountForm key={user?.id||mode}/>;}
function AccountForm(){
 const {mode,setMode,config,user,signOut,reload,error,workspaceRole,chooseWorkspaceRole}=usePlanning();
 const [forgot,setForgot]=useState(false);
 const [loginRole,setLoginRole]=useState<'member'|'admin'>('member');
 const [displayName,setDisplayName]=useState(user?.display_name||'');const [email,setEmail]=useState('');const [password,setPassword]=useState('');const [register,setRegister]=useState(false);const [pending,setPending]=useState(false);const [message,setMessage]=useState('');
 async function submit(e:React.FormEvent){e.preventDefault();setPending(true);setMessage('');try{
   if(register&&!displayName.trim())throw new Error('Enter your preferred display name.');
   if(!config?.connectedReady)throw new Error('Shared workspace needs Supabase and the API configuration.');
   const auth=getAuth(config);
   clearWorkspaceRole();
   const result=register?await auth.auth.signUp({email:email.trim(),password,options:{data:{display_name:displayName.trim()}}}):await auth.auth.signInWithPassword({email:email.trim(),password});
   if(result.error)throw result.error;
   if(register&&!result.data.session)setMessage('Check your email to confirm your account, then sign in.');else if(!register&&loginRole==='admin')await chooseWorkspaceRole('admin');else await reload();
 }catch(e){setMessage(e instanceof Error?e.message:'Could not sign in. Please try again.');}finally{setPending(false);}}
 return <main className="page-content account-page"><div className="page-heading"><div><div className="eyebrow">YOUR PEOPLE. YOUR PLANS.</div><h1>{user?'Your account':'Make room for good company.'}</h1><p>Sign in to plan together across devices.</p></div></div><section className="account-card">
 {forgot?<ResetRequest initialEmail={email} onBack={()=>setForgot(false)}/>:mode==='demo'?<><h2>You’re exploring the demo</h2><p>Demo plans and simulated assistance stay in this browser.</p><Button onClick={()=>{setMessage('');setMode('connected');}}>Use shared workspace</Button></>:user?<><h2>Signed in</h2><p>{user.email}</p><p>Current role: {workspaceRole==='admin'?'Admin':'Member'}</p>{user.app_admin&&<Button variant="outline" onClick={()=>void chooseWorkspaceRole(workspaceRole==='admin'?'member':'admin').catch(e=>setMessage(e instanceof Error?e.message:'Could not switch role.'))}>Switch to {workspaceRole==='admin'?'Member':'Admin'}</Button>}<form onSubmit={async e=>{e.preventDefault();setPending(true);setMessage('');try{if(!config)return;const result=await getAuth(config).auth.updateUser({data:{display_name:displayName.trim()}});if(result.error)throw result.error;await reload();setMessage('Display name saved.');}catch(e){setMessage(e instanceof Error?e.message:'Could not save display name.');}finally{setPending(false);}}}><label className="field">Preferred display name<input required maxLength={50} value={displayName} placeholder={user.display_name||'What should people call you?'} onChange={e=>setDisplayName(e.target.value)}/></label><Button type="submit" disabled={pending||!displayName.trim()}>Save display name</Button></form>{pendingInvitation()&&<Link className="btn btn-primary" href="/join">Continue to invitation</Link>}<p>Shared changes save to your group’s workspace. Members can read the conversation and plan details.</p><Button variant="outline" onClick={()=>void signOut()}>Sign out</Button></>:<><h2>{register?'Create your account':'Welcome back'}</h2><p>Only members you add can access your plans.</p>{config?.connectedReady?<form onSubmit={submit}>{!register&&<fieldset><legend>Sign in as</legend><label><input type="radio" name="workspace-role" checked={loginRole==='member'} onChange={()=>setLoginRole('member')}/> Member</label><label><input type="radio" name="workspace-role" checked={loginRole==='admin'} onChange={()=>setLoginRole('admin')}/> Admin</label><p>Admin mode requires an authorized account.</p></fieldset>}{register&&<label className="field">Preferred display name<input required maxLength={50} autoComplete="nickname" value={displayName} onChange={e=>setDisplayName(e.target.value)}/></label>}<label className="field">Email address<input type="email" autoComplete="email" required maxLength={254} value={email} onChange={e=>setEmail(e.target.value)}/></label><label className="field">Password<input type="password" autoComplete={register?'new-password':'current-password'} required minLength={register?12:1} maxLength={128} value={password} onChange={e=>setPassword(e.target.value)}/></label>{!register&&<button className="text-button account-switch" type="button" onClick={()=>{setForgot(true);setMessage('');}}>Forgot password?</button>}<Button type="submit" disabled={pending} className="full">{pending?'Please wait…':register?'Create account':'Sign in'}</Button><button className="text-button account-switch" type="button" onClick={()=>{setRegister(!register);setMessage('');}}>{register?'Already have an account? Sign in':'New here? Create an account'}</button></form>:<p role="alert">{error||'Shared workspace needs Supabase and the API configuration.'}</p>}</>}
 {message&&<p role="status">{message}</p>}{error&&config?.connectedReady&&<p role="alert">{error}</p>}
 {mode==='connected'&&config&&<button className="text-button account-switch" onClick={()=>{setMessage('');setMode('demo');}}>Explore the demo</button>}
 {!config&&<Button variant="outline" onClick={()=>window.location.reload()}>Retry connection</Button>}</section><p className="account-privacy">Your account uses Supabase authentication. Never share passwords or API keys in a plan. AI suggestions need your review; nothing is booked automatically.</p></main>;
}
