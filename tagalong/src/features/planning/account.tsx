'use client';
import {useState} from 'react';
import {usePlanning} from './store';
import {getAuth} from '@/services/connected';
import {Button} from '@/components/ui/button';

export function Account(){
 const {mode,setMode,config,user,signOut,reload,error}=usePlanning();
 const [email,setEmail]=useState('');const [password,setPassword]=useState('');const [register,setRegister]=useState(false);const [pending,setPending]=useState(false);const [message,setMessage]=useState('');
 async function submit(e:React.FormEvent){e.preventDefault();setPending(true);setMessage('');try{
   if(!config?.connectedReady)throw new Error('Shared workspace needs Supabase and the API configuration.');
   const auth=getAuth(config);
   const result=register?await auth.auth.signUp({email:email.trim(),password}):await auth.auth.signInWithPassword({email:email.trim(),password});
   if(result.error)throw result.error;
   if(register&&!result.data.session)setMessage('Check your email to confirm your account, then sign in.');else await reload();
 }catch(e){setMessage(e instanceof Error?e.message:'Could not sign in. Please try again.');}finally{setPending(false);}}
 return <main className="page-content account-page"><div className="page-heading"><div><div className="eyebrow">YOUR PEOPLE. YOUR PLANS.</div><h1>{user?'Your account':'Make room for good company.'}</h1><p>Sign in to plan together across devices.</p></div></div><section className="account-card">
 {mode==='demo'?<><h2>You’re exploring the demo</h2><p>Demo plans and simulated assistance stay in this browser.</p><Button onClick={()=>{setMessage('');setMode('connected');}}>Use shared workspace</Button></>:user?<><h2>Signed in</h2><p>{user.email}</p><p>Shared changes save to your group’s workspace. Members can read the conversation and plan details.</p><Button variant="outline" onClick={()=>void signOut()}>Sign out</Button></>:<><h2>{register?'Create your account':'Welcome back'}</h2><p>Only members you add can access your plans.</p>{config?.connectedReady?<form onSubmit={submit}><label className="field">Email address<input type="email" autoComplete="email" required maxLength={254} value={email} onChange={e=>setEmail(e.target.value)}/></label><label className="field">Password<input type="password" autoComplete={register?'new-password':'current-password'} required minLength={register?12:1} maxLength={128} value={password} onChange={e=>setPassword(e.target.value)}/></label><Button type="submit" disabled={pending} className="full">{pending?'Please wait…':register?'Create account':'Sign in'}</Button><button className="text-button account-switch" type="button" onClick={()=>{setRegister(!register);setMessage('');}}>{register?'Already have an account? Sign in':'New here? Create an account'}</button></form>:<p role="alert">Shared workspace needs Supabase and the API configuration.</p>}</>}
 {message&&<p role="status">{message}</p>}{error&&config?.connectedReady&&<p role="alert">{error}</p>}
 {mode==='connected'&&<button className="text-button account-switch" onClick={()=>{setMessage('');setMode('demo');}}>Explore the demo</button>}
 </section><p className="account-privacy">Your account uses Supabase authentication. Never share passwords or API keys in a plan. AI suggestions need your review; nothing is booked automatically.</p></main>;
}
