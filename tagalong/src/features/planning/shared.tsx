import {avatarTextColor} from '@/lib/avatar-contrast';
import type {Member} from '@/services/types';

export function Avatars({members,limit=4}:{members:Member[];limit?:number}){return <div className="avatar-stack" aria-label={members.map(m=>m.name).join(', ')}>{members.slice(0,limit).map((m,i)=><span key={m.name+i} className="avatar" style={{background:m.color,color:avatarTextColor(m.color)}} title={m.name}>{m.name.slice(0,1)}{m.name.split(' ')[1]?.slice(0,1)}</span>)}{members.length>limit&&<span className="avatar extra">+{members.length-limit}</span>}</div>;}
