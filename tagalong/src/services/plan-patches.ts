import type {Plan} from './types';
export interface PlanPatch {op:'add'|'replace'|'remove';path:(string|number)[];value?:unknown}
const mutable=['title','location','date','start','end','budget','image','messages','polls','itinerary','tasks'] as const;

/** Send only changed fields; private history stays on the server during unrelated edits. */
export function createPlanPatches(before:Plan,after:Plan):PlanPatch[]{
 const patches:PlanPatch[]=[];
 const old=JSON.parse(JSON.stringify(before)) as Plan;
 const next=JSON.parse(JSON.stringify(after)) as Plan;
 function walk(a:unknown,b:unknown,path:(string|number)[]){
  if(a===b)return;
  if(Array.isArray(a)&&Array.isArray(b)){
   for(let i=0;i<Math.min(a.length,b.length);i++)walk(a[i],b[i],[...path,i]);
   for(let i=a.length-1;i>=b.length;i--)patches.push({op:'remove',path:[...path,i]});
   for(let i=a.length;i<b.length;i++)patches.push({op:'add',path:[...path,i],value:b[i]});
   return;
  }
  if(a&&b&&typeof a==='object'&&typeof b==='object'&&!Array.isArray(a)&&!Array.isArray(b)){
   const left=a as Record<string,unknown>,right=b as Record<string,unknown>;
   for(const key of Object.keys(left))if(!Object.hasOwn(right,key))patches.push({op:'remove',path:[...path,key]});
   for(const key of Object.keys(right))if(!Object.hasOwn(left,key))patches.push({op:'add',path:[...path,key],value:right[key]});else walk(left[key],right[key],[...path,key]);
   return;
  }
  patches.push({op:'replace',path,value:b});
 }
 for(const key of mutable)walk(old[key],next[key],[key]);
 if(patches.length>200)throw new Error('This change is too large. Please make smaller edits.');
 return patches;
}
