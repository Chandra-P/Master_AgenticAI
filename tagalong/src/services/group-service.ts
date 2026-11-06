import {initialGroups} from './demo-data';
import type {Group,GroupDraft,GroupMember} from './types';

export const GROUP_STORAGE_KEY = 'tagalong-groups-v1';
export const groupOwner:GroupMember = {id:'alex',preferredName:'Alex',color:'#edc6b3'};
export const normalize = (value:string)=>value.trim().replace(/\s+/g,' ');
const comparison = (value:string)=>normalize(value).toLowerCase();

export function suggestGroupName(theme:string,groups:Group[]) {
 const base = normalize(theme).slice(0,55)+" · Alex’s circle";
 let name=base, suffix=2;
 while(groups.some(g=>comparison(g.name)===comparison(name)))name=base+' '+suffix++;
 return name;
}

export function validateGroup(draft:GroupDraft,groups:Group[],id?:string):string|null {
 const name=normalize(draft.name),theme=normalize(draft.theme);
 if(!name||name.length>80)return 'Use a group name between 1 and 80 characters.';
 if(groups.some(g=>g.id!==id&&comparison(g.name)===comparison(name)))return 'That group name is already in use. Try another name.';
 if(!theme||theme.length>60)return 'Use a theme between 1 and 60 characters.';
 if(draft.members.length<1||draft.members.length>13)return 'Add up to 12 adults alongside Alex.';
 const owner=draft.members.find(m=>m.id==='alex');
 if(!owner||owner.preferredName!=='Alex')return 'Alex must remain the group owner.';
 const aliases=new Set<string>(),emails=new Set<string>(),ids=new Set<string>();
 for(const member of draft.members){
  const alias=normalize(member.preferredName);
  if(!alias||alias.length>40)return 'Each adult needs a preferred name or alias (up to 40 characters).';
  if(ids.has(member.id)||!member.id)return 'Each adult needs a separate member row.';
  ids.add(member.id);
  if(aliases.has(comparison(alias)))return 'Give each adult a different preferred name or alias.';
  aliases.add(comparison(alias));
  if((member.firstName?.length??0)>40||(member.lastName?.length??0)>40)return 'First and last names must be 40 characters or fewer.';
  const email=member.email?.trim();
  if(email){
   if(email.length>254||!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))return 'Enter a valid email address or leave it blank.';
   if(emails.has(email.toLowerCase()))return 'Each email address can appear only once in a group.';
   emails.add(email.toLowerCase());
  }
 }
 return null;
}

export function makeGroup(draft:GroupDraft,id=crypto.randomUUID()):Group {
 return {id,name:normalize(draft.name),theme:normalize(draft.theme),ownerId:'alex',archived:false,members:draft.members.map(m=>({id:m.id,preferredName:normalize(m.preferredName),color:m.color,firstName:m.firstName?.trim()||undefined,lastName:m.lastName?.trim()||undefined,email:m.email?.trim()||undefined}))};
}

function isGroup(value:unknown):value is Group {
 if(!value||typeof value!=='object')return false;
 const g=value as Group;
 return typeof g.id==='string'&&!!g.id&&typeof g.name==='string'&&typeof g.theme==='string'&&g.ownerId==='alex'&&typeof g.archived==='boolean'&&Array.isArray(g.members)&&g.members.every(m=>m&&typeof m.id==='string'&&typeof m.preferredName==='string'&&typeof m.color==='string'&&[m.firstName,m.lastName,m.email].every(v=>v===undefined||typeof v==='string'))&&validateGroup(g,[],g.id)===null;
}

export function loadGroups():{groups:Group[];writable:boolean;warning:string} {
 try{
  const raw=localStorage.getItem(GROUP_STORAGE_KEY);
  if(raw===null)return {groups:initialGroups(),writable:true,warning:''};
  const value:unknown=JSON.parse(raw);
  if(!Array.isArray(value)||!value.every(isGroup)||new Set(value.map(g=>g.id)).size!==value.length||new Set(value.map(g=>comparison(g.name))).size!==value.length)throw new Error('Invalid groups');
  return {groups:value,writable:true,warning:''};
 }catch{
  return {groups:[],writable:false,warning:'Saved groups could not be loaded. Group changes are available only until you reload; existing stored data will not be overwritten.'};
 }
}

export function saveGroups(groups:Group[],writable:boolean):string {
 if(writable){try{localStorage.setItem(GROUP_STORAGE_KEY,JSON.stringify(groups));return '';}catch{/* Keep the group usable in memory. */}}
 return 'Group changes are only in memory and will be lost on reload. Browser storage is unavailable.';
}
