function minutes(value:string):number|null {
 const match=value.trim().match(/^(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?$/i);if(!match)return null;
 let hour=Number(match[1]);const minute=Number(match[2]||0),period=match[3]?.toUpperCase();
 if(minute>59||hour>(period?12:23)||period&&hour<1)return null;
 if(period)hour=hour%12+(period==='PM'?12:0);
 return hour*60+minute;
}
/** Keep descriptive/unassigned slots in place; order all parseable times stably. */
export function orderActivities<T extends {time:string}>(activities:T[]):T[]{
 const known=activities.filter(a=>minutes(a.time)!==null).sort((a,b)=>minutes(a.time)!-minutes(b.time)!);
 let next=0;return activities.map(a=>minutes(a.time)===null?a:known[next++]);
}
