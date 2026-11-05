'use client';
import {useEffect,useState} from 'react';
import {useRouter} from 'next/navigation';
import Link from 'next/link';
import {usePlanning} from './store';
import {ConnectedService,getAuth} from '@/services/connected';
import {clearInvitation,pendingInvitation,rememberInvitation,validInvitation} from '@/services/invitation-session';
import {Button} from '@/components/ui/button';

export function JoinPlan(){
 const {config,user,mode,setMode,reload}=usePlanning();const router=useRouter();
 const [token,setToken]=useState('');const [error,setError]=useState('');const [busy,setBusy]=useState(false);const [displayName,setDisplayName]=useState<string|null>(null);
 const preferredName=(displayName??user?.display_name??'').trim();
 useEffect(()=>{let active=true;queueMicrotask(()=>{if(!active)return;const fragment=window.location.hash.slice(1);const value=fragment||pendingInvitation();if(validInvitation(value)){rememberInvitation(value);setToken(value);}else{clearInvitation();setError('This invitation is unavailable. Ask the owner for a new link.');}});return()=>{active=false;};},[]);
 async function join(){if(!config||!user||!token||!preferredName)return;setBusy(true);setError('');try{const auth=getAuth(config);if(preferredName!==user.display_name){const saved=await auth.auth.updateUser({data:{display_name:preferredName}});if(saved.error)throw saved.error;}const result=await new ConnectedService(auth).acceptInvitation(token);clearInvitation();window.history.replaceState(null,'','/join');await reload();router.push('/plans/'+encodeURIComponent(result.plan_id));}catch(e){setError(e instanceof Error?e.message:'Could not join. Please retry.');}finally{setBusy(false);}}
 function cancel(){clearInvitation();window.history.replaceState(null,'','/join');router.push('/');}
 return <main className="page-content account-page"><section className="account-card"><h1>Join your people.</h1><p>A private invitation gives you access to a shared plan, its conversation, and documents.</p>{error&&<p role="alert">{error}</p>}{token&&(mode!=='connected'?<Button onClick={()=>setMode('connected')}>Use shared workspace</Button>:!user?<><p>Register or sign in, then return here to choose whether to join.</p><Link className="btn btn-primary" href="/account">Sign in or create account</Link></>:<><p>Signed in as {user.email}. Choose how your name appears to the group.</p><label className="field">Preferred display name<input required maxLength={50} autoComplete="nickname" value={displayName??user.display_name??''} onChange={e=>setDisplayName(e.target.value)}/></label><Button disabled={busy||!preferredName} onClick={()=>void join()}>{busy?'Joining…':'Join plan'}</Button></>)}<Button variant="outline" disabled={busy} onClick={cancel}>Cancel invitation</Button></section></main>;
}
