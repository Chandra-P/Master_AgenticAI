'use client';
import {useState} from 'react';
import {usePlanning} from './store';
import {ConnectedService,getAuth} from '@/services/connected';
import {Button} from '@/components/ui/button';

export function InvitationControls({planId}:{planId:string}){
 const {config}=usePlanning();const [link,setLink]=useState('');const [expires,setExpires]=useState('');const [message,setMessage]=useState('');const [busy,setBusy]=useState(false);
 async function change(disable=false){if(!config)return;setBusy(true);setMessage('');try{const api=new ConnectedService(getAuth(config));if(disable){await api.disableInvitation(planId);setLink('');setExpires('');setMessage('Invitation links disabled. Existing members keep access.');}else{const result=await api.invitation(planId);setLink(window.location.origin+'/join#'+result.token);setExpires(result.expires_at);setMessage('New link created. Any previous link no longer works.');}}catch(e){setMessage(e instanceof Error?e.message:'Could not update invitation.');}finally{setBusy(false);}}
 async function copy(){try{await navigator.clipboard.writeText(link);setMessage('Private link copied.');}catch{setMessage('Select and copy the link below.');}}
 return <section aria-label="Private invitation link"><h3>Invite with a private link</h3><p>Anyone with this link can sign in and join. It expires after seven days. Share it only with people you want in this plan.</p><Button type="button" disabled={busy} onClick={()=>void change()}>{link?'Replace invitation link':'Create invitation link'}</Button>{link&&<><label className="field">Private join link<input readOnly value={link} onFocus={e=>e.target.select()}/></label><p>Expires {new Date(expires).toLocaleString()}</p><Button type="button" onClick={()=>void copy()}>Copy invitation link</Button></>}<Button type="button" variant="outline" disabled={busy} onClick={()=>void change(true)}>Disable invitation link</Button><p>Removing a member does not disable the link. Disable or replace it to prevent them from rejoining.</p>{message&&<p role="status">{message}</p>}</section>;
}
